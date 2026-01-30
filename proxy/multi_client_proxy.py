#!/usr/bin/env python3
"""
Meshtastic Multi-Client TCP Proxy

Supports multiple simultaneous client connections through a single radio connection.
All clients receive all radio messages (broadcast mode).
Intercepts /gem commands and forwards to Gemini AI.
"""

import asyncio
import argparse
import logging
import os
import random
import struct
import sys
import time
from typing import Optional, Dict, Set
from dataclasses import dataclass, field

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Silence noisy third-party loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)

# Meshtastic TCP protocol constants
MESHTASTIC_MAGIC = b'\x94\xc3'
HEADER_SIZE = 4  # 2 bytes magic + 2 bytes length

# Default configuration
DEFAULT_LISTEN_HOST = '0.0.0.0'
DEFAULT_LISTEN_PORT = 4404
DEFAULT_RADIO_HOST = '192.168.2.144'
DEFAULT_RADIO_PORT = 4403
DEFAULT_CHANNEL_INDEX = 2
DEFAULT_RESPONSE_DELAY = 2.0


@dataclass
class ClientConnection:
    """Represents a connected client."""
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    address: str
    id: int


class MeshtasticProtocolParser:
    """Parses Meshtastic TCP protocol frames."""

    def __init__(self):
        self.buffer = bytearray()

    def add_data(self, data: bytes) -> list:
        """
        Add data to buffer and extract complete frames.
        Returns list of (raw_frame, payload) tuples.
        """
        self.buffer.extend(data)
        frames = []

        while len(self.buffer) >= HEADER_SIZE:
            # Look for magic bytes (0x94 0xc3)
            if self.buffer[0:2] != MESHTASTIC_MAGIC:
                # Search for complete magic sequence
                magic_pos = -1
                for i in range(len(self.buffer) - 1):
                    if self.buffer[i:i+2] == MESHTASTIC_MAGIC:
                        magic_pos = i
                        break

                if magic_pos == -1:
                    # No magic found, keep last byte in case it's start of magic
                    if self.buffer and self.buffer[-1] == MESHTASTIC_MAGIC[0]:
                        self.buffer = self.buffer[-1:]
                    else:
                        self.buffer.clear()
                    break
                else:
                    # Skip to magic position
                    self.buffer = self.buffer[magic_pos:]
                continue

            # Parse length (big-endian uint16)
            length = struct.unpack('>H', self.buffer[2:4])[0]
            total_size = HEADER_SIZE + length

            if len(self.buffer) < total_size:
                break  # Need more data

            # Extract complete frame
            raw_frame = bytes(self.buffer[:total_size])
            payload = bytes(self.buffer[HEADER_SIZE:total_size])
            frames.append((raw_frame, payload))
            self.buffer = self.buffer[total_size:]

        return frames


class GeminiIntegration:
    """Handles Gemini AI interactions for /gem commands."""

    def __init__(self):
        self.ai_handler = None
        self._setup()

    def _setup(self):
        """Initialize the AI handler if API key is available."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set - /gem commands disabled")
            return

        try:
            from ai_handler import AIHandler
            self.ai_handler = AIHandler(api_key)
            logger.info("Gemini AI handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    def process_message(self, sender_id: str, message: str) -> Optional[str]:
        """
        Process a message and return AI response if it's a /gem command.
        """
        if not message.startswith('/gem'):
            return None

        if not self.ai_handler:
            return "[Gemini AI not available - GEMINI_API_KEY not set]"

        prompt = message[4:].strip()
        if not prompt:
            return "[Please provide a question after /gem]"

        try:
            logger.info(f"Processing /gem from {sender_id}: {prompt[:50]}...")
            response = self.ai_handler.chat_respond(sender_id, prompt)
            logger.info(f"Gemini response: {len(response)} chars")
            return response
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return f"[AI Error: {str(e)[:100]}]"


class MultiClientProxy:
    """
    Multi-Client TCP Proxy for Meshtastic devices.

    - Single connection to radio (shared)
    - Multiple client connections supported
    - All clients receive all radio messages
    - Intercepts /gem commands for AI responses
    """

    def __init__(self,
                 listen_host: str = DEFAULT_LISTEN_HOST,
                 listen_port: int = DEFAULT_LISTEN_PORT,
                 radio_host: str = DEFAULT_RADIO_HOST,
                 radio_port: int = DEFAULT_RADIO_PORT,
                 channel_index: int = DEFAULT_CHANNEL_INDEX,
                 response_delay: float = DEFAULT_RESPONSE_DELAY):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.radio_host = radio_host
        self.radio_port = radio_port
        self.channel_index = channel_index
        self.response_delay = response_delay

        # Client management
        self.clients: Dict[int, ClientConnection] = {}
        self.client_id_counter = 0
        self.clients_lock = asyncio.Lock()

        # Shared radio connection
        self.radio_reader: Optional[asyncio.StreamReader] = None
        self.radio_writer: Optional[asyncio.StreamWriter] = None
        self.radio_lock = asyncio.Lock()
        self.radio_connected = asyncio.Event()

        # AI integration
        self.gemini = GeminiIntegration()

        # Control
        self.running = False

    async def connect_to_radio(self) -> bool:
        """Establish connection to the radio."""
        try:
            logger.info(f"Connecting to radio at {self.radio_host}:{self.radio_port}...")
            self.radio_reader, self.radio_writer = await asyncio.wait_for(
                asyncio.open_connection(self.radio_host, self.radio_port),
                timeout=10.0
            )
            logger.info(f"Connected to radio at {self.radio_host}:{self.radio_port}")

            # Send initialization request to start receiving messages
            await self._send_want_config()

            self.radio_connected.set()
            return True
        except asyncio.TimeoutError:
            logger.error(f"Timeout connecting to radio")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to radio: {e}")
            return False

    async def _send_want_config(self) -> None:
        """Send want_config request to start receiving radio messages."""
        try:
            from meshtastic import mesh_pb2

            # Request config to start receiving messages
            to_radio = mesh_pb2.ToRadio()
            to_radio.want_config_id = random.randint(1, 0xFFFFFFFF)

            payload = to_radio.SerializeToString()
            header = MESHTASTIC_MAGIC + struct.pack('>H', len(payload))
            frame = header + payload

            self.radio_writer.write(frame)
            await self.radio_writer.drain()
            logger.info(f"Sent want_config request to radio (config_id={to_radio.want_config_id})")

        except ImportError:
            logger.warning("Meshtastic protobuf not available - skipping want_config")
        except Exception as e:
            logger.error(f"Failed to send want_config: {e}")

    async def reconnect_to_radio(self) -> None:
        """Attempt to reconnect to radio with backoff."""
        self.radio_connected.clear()
        backoff = 1
        while self.running:
            logger.info(f"Attempting radio reconnection in {backoff}s...")
            await asyncio.sleep(backoff)
            if await self.connect_to_radio():
                return
            backoff = min(backoff * 2, 30)

    async def broadcast_to_clients(self, data: bytes, exclude_id: Optional[int] = None) -> None:
        """Send data to all connected clients."""
        async with self.clients_lock:
            disconnected = []
            for client_id, client in self.clients.items():
                if exclude_id and client_id == exclude_id:
                    continue
                try:
                    client.writer.write(data)
                    await client.writer.drain()
                except Exception as e:
                    logger.warning(f"Failed to send to client {client.address}: {e}")
                    disconnected.append(client_id)

            # Clean up disconnected clients
            for client_id in disconnected:
                await self._remove_client(client_id)

    async def send_to_radio(self, data: bytes) -> bool:
        """Send data to the radio."""
        async with self.radio_lock:
            if not self.radio_writer:
                logger.warning("Radio not connected, cannot send")
                return False
            try:
                self.radio_writer.write(data)
                await self.radio_writer.drain()
                return True
            except Exception as e:
                logger.error(f"Failed to send to radio: {e}")
                return False

    def try_parse_text_message(self, payload: bytes) -> Optional[tuple]:
        """Try to parse a text message from payload using protobuf."""
        try:
            from meshtastic import mesh_pb2, portnums_pb2

            # Try to parse as ToRadio (client -> radio)
            to_radio = mesh_pb2.ToRadio()
            try:
                to_radio.ParseFromString(payload)
                if to_radio.HasField('packet'):
                    packet = to_radio.packet
                    if packet.HasField('decoded'):
                        if packet.decoded.portnum == portnums_pb2.TEXT_MESSAGE_APP:
                            text = packet.decoded.payload.decode('utf-8', errors='ignore')
                            # Use 'from' field as sender ID (hex node ID)
                            # Note: 'from' is a Python keyword, so use getattr
                            from_id = getattr(packet, 'from', 0)
                            sender_id = f"!{from_id:08x}" if from_id else "client"
                            channel = packet.channel
                            # Log full packet details for debugging
                            logger.info(f"Parsed ToRadio packet:")
                            logger.info(f"  - from: 0x{from_id:08x}")
                            logger.info(f"  - to: 0x{packet.to:08x}")
                            logger.info(f"  - channel: {channel}")
                            logger.info(f"  - id: {packet.id}")
                            logger.info(f"  - hop_limit: {packet.hop_limit}")
                            logger.info(f"  - want_ack: {packet.want_ack}")
                            return (sender_id, channel, text)
            except Exception as e:
                logger.debug(f"ToRadio parse failed: {e}")

            # Try to parse as FromRadio (radio -> client)
            from_radio = mesh_pb2.FromRadio()
            try:
                from_radio.ParseFromString(payload)
                if from_radio.HasField('packet'):
                    packet = from_radio.packet
                    if packet.HasField('decoded'):
                        if packet.decoded.portnum == portnums_pb2.TEXT_MESSAGE_APP:
                            text = packet.decoded.payload.decode('utf-8', errors='ignore')
                            # Use 'from' field as sender ID (hex node ID)
                            # Note: protobuf field 'from' is accessed via getattr due to Python keyword
                            from_id = getattr(packet, 'from', 0)
                            sender_id = f"!{from_id:08x}" if from_id else "unknown"
                            channel = packet.channel
                            logger.debug(f"Parsed FromRadio text message from {sender_id}: {text}")
                            return (sender_id, channel, text)
            except Exception as e:
                logger.debug(f"FromRadio parse failed: {e}")

            return None
        except ImportError:
            logger.warning("Meshtastic protobuf not available for parsing")
            return None
        except Exception as e:
            logger.debug(f"Failed to parse message: {e}")
            return None

    def _generate_packet_id(self) -> int:
        """Generate a unique packet ID."""
        return random.randint(1, 0xFFFFFFFF)

    async def send_ai_response(self, text: str, channel: int = None) -> None:
        """Send AI response through the radio and to connected clients."""
        try:
            from meshtastic import mesh_pb2, portnums_pb2

            # Delay to let radio finish transmitting any pending message
            # LoRa transmission can take 1-3+ seconds depending on settings
            if self.response_delay > 0:
                logger.debug(f"Waiting {self.response_delay}s before sending response...")
                await asyncio.sleep(self.response_delay)

            trimmed = text[:200]
            use_channel = channel if channel is not None else self.channel_index
            logger.info(f"Sending AI response on channel {use_channel}: {trimmed[:50]}...")

            # Generate unique packet ID
            packet_id = self._generate_packet_id()

            # Create protobuf message for radio (ToRadio)
            mesh_packet = mesh_pb2.MeshPacket()
            mesh_packet.id = packet_id
            mesh_packet.to = 0xFFFFFFFF  # Broadcast
            mesh_packet.channel = use_channel
            mesh_packet.want_ack = True
            mesh_packet.hop_limit = 7
            mesh_packet.decoded.portnum = portnums_pb2.TEXT_MESSAGE_APP
            mesh_packet.decoded.payload = trimmed.encode('utf-8')

            to_radio = mesh_pb2.ToRadio()
            to_radio.packet.CopyFrom(mesh_packet)

            payload = to_radio.SerializeToString()
            header = MESHTASTIC_MAGIC + struct.pack('>H', len(payload))
            frame = header + payload

            # Log detailed packet info for debugging
            logger.info(f"AI response packet details:")
            logger.info(f"  - id: {packet_id}")
            logger.info(f"  - to: 0x{mesh_packet.to:08x}")
            logger.info(f"  - channel: {use_channel}")
            logger.info(f"  - hop_limit: {mesh_packet.hop_limit}")
            logger.info(f"  - want_ack: {mesh_packet.want_ack}")
            logger.info(f"  - portnum: {mesh_packet.decoded.portnum}")
            logger.info(f"  - payload len: {len(mesh_packet.decoded.payload)}")
            logger.debug(f"  - raw frame hex: {frame.hex()}")

            # Send to radio
            if await self.send_to_radio(frame):
                logger.info(f"AI response sent to radio ({len(frame)} bytes)")
            else:
                logger.error("Failed to send AI response to radio")

            # Also create a FromRadio message to send directly to clients
            # This ensures clients see the response even if radio doesn't echo it
            from_radio = mesh_pb2.FromRadio()
            from_radio.packet.CopyFrom(mesh_packet)

            client_payload = from_radio.SerializeToString()
            client_header = MESHTASTIC_MAGIC + struct.pack('>H', len(client_payload))
            client_frame = client_header + client_payload

            await self.broadcast_to_clients(client_frame)
            logger.info(f"AI response broadcast to clients ({len(client_frame)} bytes)")

        except ImportError as e:
            logger.error(f"Meshtastic protobuf not available: {e}")
        except Exception as e:
            logger.error(f"Failed to send AI response: {e}")

    async def handle_client_data(self, client: ClientConnection, data: bytes) -> None:
        """Process data from a client and forward to radio."""
        parser = MeshtasticProtocolParser()
        frames = parser.add_data(data)

        for raw_frame, payload in frames:
            parsed = self.try_parse_text_message(payload)
            if parsed:
                sender_id, channel, text = parsed
                logger.info(f"[Client {client.id}] Detected message on ch{channel}: {text[:50]}...")

                if text.startswith('/gem'):
                    response = self.gemini.process_message(sender_id, text)
                    if response:
                        # Pass the channel so response goes to same channel
                        asyncio.create_task(self.send_ai_response(response, channel=channel))

        # Forward to radio
        await self.send_to_radio(data)

    async def handle_client(self,
                           reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter) -> None:
        """Handle a new client connection."""
        addr = writer.get_extra_info('peername')

        async with self.clients_lock:
            self.client_id_counter += 1
            client_id = self.client_id_counter
            client = ClientConnection(
                reader=reader,
                writer=writer,
                address=f"{addr[0]}:{addr[1]}",
                id=client_id
            )
            self.clients[client_id] = client

        client_count = len(self.clients)
        logger.info(f"Client {client.id} connected from {client.address} (total: {client_count})")

        try:
            # Wait for radio connection
            await self.radio_connected.wait()

            while self.running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=60.0)
                    if not data:
                        break

                    logger.debug(f"[Client {client.id}] Received {len(data)} bytes")
                    await self.handle_client_data(client, data)

                except asyncio.TimeoutError:
                    # Keep-alive check, continue
                    continue

        except Exception as e:
            logger.error(f"Client {client.id} error: {e}")
        finally:
            await self._remove_client(client_id)
            logger.info(f"Client {client.id} disconnected from {client.address}")

    async def _remove_client(self, client_id: int) -> None:
        """Remove a client connection."""
        async with self.clients_lock:
            if client_id in self.clients:
                client = self.clients.pop(client_id)
                try:
                    client.writer.close()
                    await client.writer.wait_closed()
                except:
                    pass
                logger.info(f"Client {client_id} removed (remaining: {len(self.clients)})")

    async def handle_radio_data(self, data: bytes) -> None:
        """Process data from radio, check for /gem commands, and broadcast to clients."""
        parser = MeshtasticProtocolParser()
        frames = parser.add_data(data)

        for raw_frame, payload in frames:
            # Try to decode all FromRadio messages for debugging
            self._debug_from_radio(payload)

            parsed = self.try_parse_text_message(payload)
            if parsed:
                sender_id, channel, text = parsed
                logger.info(f"[Radio] Detected message on ch{channel}: {text[:50]}...")

                # Check for /gem command from radio
                if text.startswith('/gem'):
                    logger.info(f"[Radio] Processing /gem command from {sender_id} on ch{channel}")
                    response = self.gemini.process_message(sender_id, text)
                    if response:
                        # Pass the channel so response goes to same channel
                        asyncio.create_task(self.send_ai_response(response, channel=channel))

        # Broadcast raw data to all connected clients
        await self.broadcast_to_clients(data)

    def _debug_from_radio(self, payload: bytes) -> None:
        """Debug helper to decode and log FromRadio messages."""
        try:
            from meshtastic import mesh_pb2

            from_radio = mesh_pb2.FromRadio()
            from_radio.ParseFromString(payload)

            # Log what type of FromRadio message this is
            if from_radio.HasField('packet'):
                pkt = from_radio.packet
                from_id = getattr(pkt, 'from', 0)
                logger.info(f"[Radio] FromRadio packet: from=0x{from_id:08x} to=0x{pkt.to:08x} ch={pkt.channel} id={pkt.id}")
            elif from_radio.HasField('my_info'):
                logger.info(f"[Radio] FromRadio my_info: node_num={from_radio.my_info.my_node_num}")
            elif from_radio.HasField('node_info'):
                logger.info(f"[Radio] FromRadio node_info: num={from_radio.node_info.num}")
            elif from_radio.HasField('config_complete_id'):
                logger.info(f"[Radio] FromRadio config_complete: id={from_radio.config_complete_id}")
            elif from_radio.HasField('rebooted'):
                logger.info(f"[Radio] FromRadio rebooted: {from_radio.rebooted}")
            elif from_radio.HasField('queueStatus'):
                qs = from_radio.queueStatus
                logger.info(f"[Radio] FromRadio queueStatus: res={qs.res} free={qs.free} maxlen={qs.maxlen} mesh_packet_id={qs.mesh_packet_id}")
            else:
                logger.debug(f"[Radio] FromRadio other: {from_radio}")
        except Exception as e:
            logger.debug(f"[Radio] Failed to decode FromRadio: {e}")

    async def radio_reader_task(self) -> None:
        """Read from radio, intercept /gem commands, and broadcast to all clients."""
        logger.info("Radio reader task started")
        while self.running:
            try:
                await self.radio_connected.wait()

                if not self.radio_reader:
                    await asyncio.sleep(0.1)
                    continue

                data = await self.radio_reader.read(4096)
                if not data:
                    logger.warning("Radio connection closed")
                    self.radio_connected.clear()
                    asyncio.create_task(self.reconnect_to_radio())
                    continue

                logger.info(f"[Radio RX] Received {len(data)} bytes from radio")
                await self.handle_radio_data(data)

            except Exception as e:
                logger.error(f"Radio reader error: {e}")
                self.radio_connected.clear()
                asyncio.create_task(self.reconnect_to_radio())

    async def start(self) -> None:
        """Start the proxy server."""
        self.running = True

        # Connect to radio first
        if not await self.connect_to_radio():
            logger.error("Failed to connect to radio, exiting")
            return

        # Start radio reader task
        radio_task = asyncio.create_task(self.radio_reader_task())

        # Start client server
        server = await asyncio.start_server(
            self.handle_client,
            self.listen_host,
            self.listen_port
        )

        addr = server.sockets[0].getsockname()
        logger.info("=" * 60)
        logger.info("Meshtastic Multi-Client TCP Proxy Started")
        logger.info("=" * 60)
        logger.info(f"Listening on: {addr[0]}:{addr[1]}")
        logger.info(f"Radio: {self.radio_host}:{self.radio_port} (single connection)")
        logger.info(f"Channel index: {self.channel_index}")
        logger.info(f"Response delay: {self.response_delay}s")
        logger.info(f"Gemini AI: {'enabled' if self.gemini.ai_handler else 'disabled'}")
        logger.info("=" * 60)
        logger.info("Multiple clients can connect simultaneously")
        logger.info("All clients receive all radio messages")
        logger.info("Send /gem <question> to get AI responses")
        logger.info("=" * 60)

        try:
            async with server:
                await server.serve_forever()
        finally:
            self.running = False
            radio_task.cancel()

    async def stop(self) -> None:
        """Stop the proxy server."""
        logger.info("Stopping proxy...")
        self.running = False

        # Close all clients
        async with self.clients_lock:
            for client in self.clients.values():
                try:
                    client.writer.close()
                except:
                    pass

        # Close radio connection
        if self.radio_writer:
            try:
                self.radio_writer.close()
                await self.radio_writer.wait_closed()
            except:
                pass


async def main():
    parser = argparse.ArgumentParser(
        description='Meshtastic Multi-Client TCP Proxy with Gemini AI'
    )
    parser.add_argument('--listen-host', default=DEFAULT_LISTEN_HOST,
                       help=f'Host to listen on (default: {DEFAULT_LISTEN_HOST})')
    parser.add_argument('--listen-port', type=int, default=DEFAULT_LISTEN_PORT,
                       help=f'Port to listen on (default: {DEFAULT_LISTEN_PORT})')
    parser.add_argument('--radio-host', default=DEFAULT_RADIO_HOST,
                       help=f'Meshtastic radio IP (default: {DEFAULT_RADIO_HOST})')
    parser.add_argument('--radio-port', type=int, default=DEFAULT_RADIO_PORT,
                       help=f'Meshtastic radio port (default: {DEFAULT_RADIO_PORT})')
    parser.add_argument('--channel', type=int, default=DEFAULT_CHANNEL_INDEX,
                       help=f'Channel index for AI responses (default: {DEFAULT_CHANNEL_INDEX})')
    parser.add_argument('--response-delay', type=float, default=DEFAULT_RESPONSE_DELAY,
                       help=f'Delay in seconds before sending AI response (default: {DEFAULT_RESPONSE_DELAY})')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    proxy = MultiClientProxy(
        listen_host=args.listen_host,
        listen_port=args.listen_port,
        radio_host=args.radio_host,
        radio_port=args.radio_port,
        channel_index=args.channel,
        response_delay=args.response_delay
    )

    try:
        await proxy.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        await proxy.stop()


if __name__ == '__main__':
    asyncio.run(main())

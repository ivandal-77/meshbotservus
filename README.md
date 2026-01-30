# Meshtastic Multi-Client TCP Proxy with AI

A TCP proxy for Meshtastic devices that enables multiple simultaneous client connections through a single radio, with integrated Gemini AI support for `/gem` commands.

## Architecture

```
                                    LoRa Radio Network
                                           |
                                           v
+------------------+              +------------------+
|  Meshtastic      |    TCP      |                  |
|  Radio Device    |<----------->|   TCP Proxy      |
|  (192.168.2.144) |   :4403     |   (this app)     |
+------------------+              |                  |
                                  |  - Message       |
                                  |    forwarding    |
                                  |  - /gem command  |
                                  |    interception  |
                                  |  - AI response   |
                                  |    injection     |
                                  +--------+---------+
                                           |
                              TCP :4404    |
                    +----------------------+----------------------+
                    |                      |                      |
                    v                      v                      v
            +-------------+        +-------------+        +-------------+
            | Client App  |        | Client App  |        | Client App  |
            | (Phone/PC)  |        | (Phone/PC)  |        | (Phone/PC)  |
            +-------------+        +-------------+        +-------------+
```

## Features

- **Multi-Client Support**: Multiple Meshtastic apps can connect simultaneously through a single radio
- **Message Broadcasting**: All connected clients receive all radio messages
- **AI Integration**: `/gem <question>` commands are intercepted and answered by Google Gemini AI
- **Dual-Source AI**: Responds to `/gem` commands from both:
  - Connected client apps (via proxy)
  - Remote radio devices (over LoRa mesh)
- **Automatic Reconnection**: Handles radio disconnections with exponential backoff
- **Configurable Delays**: Tunable response delay for different LoRa configurations

## Message Flow

### Client to Radio
```
Client App → Proxy → Radio → LoRa Mesh
                ↓
         (if /gem command)
                ↓
         Gemini AI → Response → Radio → LoRa Mesh
                              → All Clients
```

### Radio to Clients
```
LoRa Mesh → Radio → Proxy → All Connected Clients
                ↓
         (if /gem command)
                ↓
         Gemini AI → Response → Radio → LoRa Mesh
                              → All Clients
```

## Requirements

- Python 3.8+
- Meshtastic device with TCP API enabled
- Google Gemini API key (for AI features)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/meshbotservus.git
cd meshbotservus
```

2. Install dependencies with pipenv:
```bash
pip install pipenv
pipenv install
```

3. Set your Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LISTEN_HOST` | `0.0.0.0` | Host to listen on |
| `LISTEN_PORT` | `4404` | Port for client connections |
| `RADIO_HOST` | `192.168.2.144` | Meshtastic radio IP address |
| `RADIO_PORT` | `4403` | Meshtastic radio TCP port |
| `CHANNEL` | `2` | Channel index for AI responses |
| `RESPONSE_DELAY` | `2.0` | Delay (seconds) before sending AI response |
| `DEBUG` | `0` | Set to `1` for debug logging |
| `GEMINI_API_KEY` | - | Google Gemini API key (required for AI) |

### Command Line Arguments

```
--listen-host      Host to listen on (default: 0.0.0.0)
--listen-port      Port to listen on (default: 4404)
--radio-host       Meshtastic radio IP (default: 192.168.2.144)
--radio-port       Meshtastic radio port (default: 4403)
--channel          Channel index for AI responses (default: 2)
--response-delay   Delay in seconds before sending AI response (default: 2.0)
--debug            Enable debug logging
```

## Usage

### Using the shell script
```bash
# Basic usage
./proxy/run_proxy.sh

# With custom settings
RADIO_HOST=192.168.1.100 RESPONSE_DELAY=5 ./proxy/run_proxy.sh

# With debug logging
DEBUG=1 ./proxy/run_proxy.sh
```

### Using Python directly
```bash
pipenv run python proxy/multi_client_proxy.py --radio-host 192.168.1.100 --debug
```

### Connecting Clients

Configure your Meshtastic app to connect via TCP:
- **Host**: Your proxy server IP
- **Port**: 4404 (default)

## AI Commands

Send messages starting with `/gem` followed by your question:

```
/gem What is the weather forecast?
/gem Translate "hello" to Spanish
/gem How do I configure a Meshtastic node?
```

The AI response will be broadcast to:
- All connected client apps
- The LoRa mesh network (visible to all radio devices)

## Response Delay Tuning

The `RESPONSE_DELAY` setting controls how long the proxy waits before sending an AI response. This is necessary because LoRa transmission takes time, and the radio cannot process a new outgoing message while still transmitting.

Recommended values based on LoRa settings:
- **Fast settings** (SF7, high bandwidth): 3-4 seconds
- **Medium settings** (SF10): 5-6 seconds
- **Long range settings** (SF12, low bandwidth): 8-10 seconds

If AI responses aren't being transmitted over LoRa, try increasing this value.

## Project Structure

```
meshbotservus/
├── proxy/
│   ├── __init__.py
│   ├── multi_client_proxy.py    # Main proxy implementation
│   └── run_proxy.sh             # Launch script
├── ai_handler.py                # Gemini AI integration
├── Pipfile                      # Python dependencies
└── README.md
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

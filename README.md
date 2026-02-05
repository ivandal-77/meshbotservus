# Meshtastic Multi-Client TCP Proxy with AI & Telegram

A comprehensive TCP proxy for Meshtastic devices featuring:
- **Multi-client support**: Multiple simultaneous connections through a single radio
- **Gemini AI integration**: Intelligent `/gem` command responses
- **Telegram bridge**: Bidirectional message forwarding to/from Telegram
- **GUI & CLI modes**: Modern Qt6 interface or command-line operation
- **Standalone app**: Self-contained binary with no dependencies

## Architecture

```
                         Telegram Channel/Group
                                   ↕
                         [Telegram Bot Bridge]
                                   ↕
                              LoRa Radio Network
                                   ↕
            +------------------+              +------------------+
            |  Meshtastic      |    TCP      |                  |
            |  Radio Device    |<----------->|   TCP Proxy      |
            |  (192.168.2.144) |   :4403     |   (this app)     |
            +------------------+              |                  |
                                              |  - Multi-client  |
                                              |  - /gem AI       |
                                              |  - Telegram fwd  |
                                              |  - Qt6 GUI       |
                                              +--------+---------+
                                                       |
                                          TCP :4404    |
                            +--------------------------|------------------+
                            |                          |                  |
                            v                          v                  v
                    +-------------+            +-------------+    +-------------+
                    | Client App  |            | Client App  |    | Client App  |
                    | (Phone/PC)  |            | (Phone/PC)  |    | (Phone/PC)  |
                    +-------------+            +-------------+    +-------------+
```

## Features

### Core Proxy Features
- **Multi-Client Support**: Multiple Meshtastic apps can connect simultaneously through a single radio
- **Message Broadcasting**: All connected clients receive all radio messages in real-time
- **Automatic Reconnection**: Handles radio disconnections with exponential backoff
- **Channel Preservation**: Messages maintain their original channel assignments

### AI Integration
- **Gemini AI**: `/gem <question>` commands are intercepted and answered by Google Gemini 2.5 Flash
- **Multi-Source Processing**: Responds to `/gem` commands from:
  - Connected client apps (via TCP)
  - Remote radio devices (over LoRa mesh)
  - Telegram channel/group
- **Configurable Response Delay**: Tunable delay for different LoRa configurations

### Telegram Bridge
- **Bidirectional Messaging**: Seamless forwarding between Telegram ↔ Radio ↔ Clients
- **Radio → Telegram**: All text messages from Meshtastic network forwarded to Telegram
- **Telegram → Radio**: Messages from Telegram channel broadcast to mesh network
- **AI Integration**: `/gem` commands from Telegram are processed and responded to
- **Optional**: Completely optional feature, disabled by default

### GUI Application
- **Modern Qt6 Interface**: Easy-to-use graphical configuration
- **Real-Time Log Viewer**: Live monitoring of all proxy activity with filtering
- **Client Management**: View all connected clients and their status
- **Statistics Dashboard**: Track uptime, message count, and radio status
- **Settings Persistence**: Automatically saves and loads configuration
- **Standalone Binary**: Self-contained ~91MB app with Python runtime included

### CLI Mode
- **Headless Operation**: Run without GUI for servers/automation
- **Command-Line Arguments**: Full configuration via flags
- **Environment Variables**: Alternative configuration method

## Message Flow

### Client to Radio (with Telegram & AI)
```
Client App → Proxy → Radio → LoRa Mesh
                ↓          ↓
                ↓       Telegram
                ↓
         (if /gem command)
                ↓
         Gemini AI → Response → Radio → LoRa Mesh
                              → All Clients
                              → Telegram
```

### Radio to Clients (with Telegram & AI)
```
LoRa Mesh → Radio → Proxy → All Connected Clients
                      ↓    → Telegram
                      ↓
               (if /gem command)
                      ↓
               Gemini AI → Response → Radio → LoRa Mesh
                                    → All Clients
                                    → Telegram
```

### Telegram to Radio (with AI)
```
Telegram → Proxy → Radio → LoRa Mesh
              ↓          ↓
              ↓    All Connected Clients
              ↓
       (if /gem command)
              ↓
       Gemini AI → Response → Radio → LoRa Mesh
                            → All Clients
                            → Telegram
```

## Requirements

### For Standalone Binary (Recommended)
- **macOS/Linux/Windows**: Just the binary - no Python installation needed
- Meshtastic device with TCP API enabled
- Google Gemini API key (optional, for `/gem` AI features)
- Telegram Bot Token & Chat ID (optional, for Telegram integration)

### For Running from Source
- Python 3.8+
- PyQt6 (for GUI mode)
- Meshtastic Python library
- python-telegram-bot (optional, for Telegram)
- google-genai SDK (optional, for AI)
- See `proxy/requirements.txt` for full list

## Quick Start

### Option 1: Standalone GUI App (Easiest)

1. Download or build the `MeshtasticProxy.app` binary
2. Double-click to launch
3. Configure settings in the GUI:
   - Radio IP and port
   - Optional: Gemini API key for AI
   - Optional: Telegram Bot Token and Chat ID
4. Click "Start Proxy"

**See [proxy/README_GUI.md](proxy/README_GUI.md) for full GUI documentation**

### Option 2: From Source (GUI)

```bash
cd proxy
./run_gui.sh  # Automatically creates venv and installs dependencies
```

### Option 3: From Source (CLI/Headless)

1. Clone the repository:
```bash
git clone <repo-url>
cd meshbotservus
```

2. Install dependencies:
```bash
cd proxy
pip install -r requirements.txt
```

3. Set environment variables (optional):
```bash
export GEMINI_API_KEY="your-api-key-here"
export DISABLE_SSL_VERIFY="true"  # Only if behind corporate proxy
```

4. Run the proxy:
```bash
python multi_client_proxy.py --radio-host 192.168.2.144
```

## Configuration

### GUI Configuration (Easiest)

All settings are available in the GUI:
- **Listen Settings**: Host and port for client connections
- **Radio Settings**: Meshtastic device IP and port
- **Bot Messages Channel**: Channel for AI and Telegram messages (0-7)
- **Response Delay**: Seconds to wait before sending AI response
- **Gemini API Key**: Optional, for `/gem` AI commands
- **Telegram Bot Token**: Optional, from @BotFather
- **Telegram Chat ID**: Optional, channel/group ID
- **SSL Verification**: Disable for corporate proxies (insecure)

Settings are automatically saved and restored.

### CLI Configuration

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LISTEN_HOST` | `0.0.0.0` | Host to listen on |
| `LISTEN_PORT` | `4404` | Port for client connections |
| `RADIO_HOST` | `192.168.2.144` | Meshtastic radio IP address |
| `RADIO_PORT` | `4403` | Meshtastic radio TCP port |
| `CHANNEL` | `2` | Channel index for bot messages (AI & Telegram) |
| `RESPONSE_DELAY` | `2.0` | Delay (seconds) before sending AI response |
| `GEMINI_API_KEY` | - | Google Gemini API key (optional, for AI) |
| `DISABLE_SSL_VERIFY` | `false` | Set to `true` for corporate proxies (insecure) |

#### Command Line Arguments

```
--listen-host      Host to listen on (default: 0.0.0.0)
--listen-port      Port to listen on (default: 4404)
--radio-host       Meshtastic radio IP (default: 192.168.2.144)
--radio-port       Meshtastic radio port (default: 4403)
--channel          Channel index for bot messages (default: 2)
--response-delay   Delay in seconds before sending AI response (default: 2.0)
--debug            Enable debug logging
```

### Telegram Setup

For Telegram integration:
1. Create a bot with @BotFather to get Bot Token
2. Get your channel/group Chat ID
3. Enter both in GUI or pass to CLI

**See [proxy/TELEGRAM_SETUP.md](proxy/TELEGRAM_SETUP.md) for detailed setup instructions**

## Usage

### GUI Mode (Recommended)

```bash
# From binary
open dist/MeshtasticProxy.app

# From source
cd proxy
./run_gui.sh
```

1. Enter your radio IP address
2. Optional: Add Gemini API key for AI features
3. Optional: Add Telegram credentials for bridge
4. Click "Start Proxy"
5. Monitor logs and connected clients in real-time

### CLI Mode (Headless/Server)

```bash
# Basic usage
python proxy/multi_client_proxy.py

# With custom settings
python proxy/multi_client_proxy.py \
  --radio-host 192.168.1.100 \
  --channel 0 \
  --response-delay 5 \
  --debug

# Using environment variables
export GEMINI_API_KEY="your-key"
export RADIO_HOST="192.168.1.100"
python proxy/multi_client_proxy.py
```

### Connecting Clients

Configure your Meshtastic app to connect via TCP:
- **Host**: Your proxy server IP
- **Port**: 4404 (default)

Multiple clients can connect simultaneously and all will receive all messages.

## AI Commands

Send messages starting with `/gem` followed by your question from:
- Any Meshtastic client app connected to the proxy
- Any Meshtastic radio on the mesh network
- The Telegram channel/group (if configured)

```
/gem What is the weather forecast?
/gem Translate "hello" to Spanish
/gem How do I configure a Meshtastic node?
```

The AI response (powered by Google Gemini 2.5 Flash) will be broadcast to:
- All connected client apps
- The LoRa mesh network (visible to all radio devices)
- The Telegram channel (if configured)

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
│   ├── multi_client_proxy.py      # Core proxy implementation
│   ├── proxy_gui.py               # Qt6 GUI application
│   ├── telegram_bridge.py         # Telegram integration
│   ├── proxy_gui_onedir.spec      # PyInstaller build config
│   ├── requirements.txt           # Python dependencies
│   ├── run_gui.sh                 # Launch GUI from source
│   ├── build.sh                   # Build standalone binary
│   ├── README_GUI.md              # GUI documentation
│   ├── TELEGRAM_SETUP.md          # Telegram setup guide
│   ├── DISTRIBUTION.md            # Binary distribution guide
│   ├── QUICK_START.md             # Quick reference
│   └── dist/
│       └── MeshtasticProxy.app    # Standalone binary (after build)
├── ai_handler.py                  # Gemini AI integration
└── README.md                      # This file
```

## Building from Source

### Build Standalone Binary

```bash
cd proxy
./build.sh
```

The standalone app will be created in `dist/MeshtasticProxy.app` (macOS) or `dist/MeshtasticProxy/` (Linux/Windows).

**Build time**: ~30-60 seconds
**Binary size**: ~91 MB (includes Python runtime + all dependencies)

See [proxy/DISTRIBUTION.md](proxy/DISTRIBUTION.md) for distribution instructions.

## Features Comparison

| Feature | CLI Mode | GUI Mode |
|---------|----------|----------|
| Multi-client proxy | ✓ | ✓ |
| Gemini AI integration | ✓ | ✓ |
| Telegram bridge | ✓ | ✓ |
| Command-line arguments | ✓ | - |
| Visual configuration | - | ✓ |
| Real-time log viewer | - | ✓ |
| Client monitoring | - | ✓ |
| Statistics display | - | ✓ |
| Settings persistence | - | ✓ |
| Headless operation | ✓ | - |
| Standalone binary | - | ✓ |

## Troubleshooting

### Radio Connection Issues
- Verify radio IP address is correct
- Ensure radio has TCP API enabled in settings
- Check firewall isn't blocking port 4403
- The proxy will retry connection 3 times automatically

### SSL Certificate Errors (Corporate Proxy)
- Enable "Disable SSL verification" in GUI
- Or set `DISABLE_SSL_VERIFY=true` environment variable
- **Warning**: This is insecure, only use behind corporate firewalls

### Telegram Not Working
- Verify Bot Token from @BotFather is correct
- Ensure Chat ID includes minus sign for groups/channels (e.g., `-1001234567890`)
- Make sure bot is added as administrator in channel/group
- Check [proxy/TELEGRAM_SETUP.md](proxy/TELEGRAM_SETUP.md) for detailed instructions

### /gem Commands Not Responding
- Verify `GEMINI_API_KEY` is set (in GUI or environment)
- Check logs for AI errors (quota exceeded, API errors)
- Ensure internet connectivity for Gemini API

### GUI Won't Start on macOS
- Right-click app and select "Open" (first time only)
- Or: System Settings → Privacy & Security → "Open Anyway"
- Or remove quarantine: `xattr -cr MeshtasticProxy.app`

## Documentation

- **GUI Guide**: [proxy/README_GUI.md](proxy/README_GUI.md)
- **Telegram Setup**: [proxy/TELEGRAM_SETUP.md](proxy/TELEGRAM_SETUP.md)
- **Distribution**: [proxy/DISTRIBUTION.md](proxy/DISTRIBUTION.md)
- **Quick Reference**: [proxy/QUICK_START.md](proxy/QUICK_START.md)

## License

**GPL v3 License**

This project is licensed under the GNU General Public License v3.0 due to the use of PyQt6.

```
Copyright (C) 2025 Meshtastic Proxy Contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
```

**Third-Party Licenses**: See [LICENSES.md](LICENSES.md) for detailed information about all third-party components.

**Commercial Use**: For commercial use without GPL obligations, you can:
- Purchase a commercial PyQt6 license
- Use the CLI version without the GUI
- Replace PyQt6 with an alternative framework

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

By contributing to this project, you agree that your contributions will be licensed under the GPLv3 license.

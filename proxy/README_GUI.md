# Meshtastic Multi-Client TCP Proxy - GUI Application

A Qt-based graphical user interface for the Meshtastic Multi-Client TCP Proxy.

## Features

- **Easy Configuration**: GUI for all proxy settings (listen/radio hosts, ports, channel, delays)
- **Real-time Monitoring**: Live log viewer with filtering and auto-scroll
- **Client Management**: View all connected clients and their status
- **Statistics**: Track uptime, message count, and radio status
- **Dark Theme**: Modern dark UI for comfortable viewing
- **Settings Persistence**: Automatically saves and loads configuration
- **Fully Standalone**: Binary includes Python runtime, Qt, all dependencies, and AI handler - no installation needed

## Requirements

- Python 3.8 or higher
- PyQt6
- Meshtastic Python library
- All dependencies from the original proxy script

## Installation

### Option 1: Run from Source

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the GUI:
```bash
python3 proxy_gui.py
```

### Option 2: Build Standalone Binary

#### macOS/Linux:
```bash
./build.sh
```

The app will be created in:
- macOS: `dist/MeshtasticProxy.app` (app bundle) or `dist/MeshtasticProxy/` (directory with executable)
- Linux: `dist/MeshtasticProxy/` (directory with executable)

#### Windows:
```cmd
build.bat
```

The application will be created at: `dist\MeshtasticProxy\MeshtasticProxy.exe`

## What's Included in the Standalone Binary

The standalone application (approximately 91MB) is **completely self-contained** and includes:

✅ **Everything needed to run:**
- Python 3.14 runtime
- PyQt6 GUI framework (Qt 6)
- All dependencies (meshtastic, google-generativeai, asyncio, etc.)
- Your proxy code (`multi_client_proxy.py`)
- GUI code (`proxy_gui.py`)
- AI handler (`ai_handler.py`)
- All required system libraries

❌ **Only runtime requirements:**
- Network access to your Meshtastic radio
- `GEMINI_API_KEY` environment variable (only needed for `/gem` AI commands)

The app can be copied to any Mac and run without installing Python or any dependencies.

## Usage

### Starting the Proxy

1. **Configure Settings**:
   - **Listen Host**: IP address to listen on (default: 0.0.0.0 for all interfaces)
   - **Listen Port**: Port for client connections (default: 4404)
   - **Radio Host**: IP address of your Meshtastic radio
   - **Radio Port**: TCP port of your Meshtastic radio (default: 4403)
   - **Channel**: Meshtastic channel index for AI responses (default: 2)
   - **Response Delay**: Delay in seconds before sending AI responses (default: 2.0)
   - **Gemini API Key**: (Optional) Your Gemini API key for /gem commands

2. **Click "Start Proxy"**: The proxy will start and connect to your radio

3. **Monitor Activity**: Watch the log viewer for real-time activity

### Using the Interface

- **Log Level**: Change between DEBUG, INFO, WARNING, and ERROR
- **Auto-scroll**: Keep the log viewer scrolled to the bottom
- **Clear Logs**: Clear the log viewer
- **Statistics**: Monitor connected clients, messages, uptime, and radio status
- **Connected Clients**: See all currently connected client applications

### Stopping the Proxy

Click the "Stop Proxy" button to gracefully shut down the proxy server.

## Features Comparison

| Feature | CLI Version | GUI Version |
|---------|-------------|-------------|
| Multi-client support | ✓ | ✓ |
| Gemini AI integration | ✓ | ✓ |
| Command-line arguments | ✓ | - |
| Visual configuration | - | ✓ |
| Real-time log viewer | - | ✓ |
| Client monitoring | - | ✓ |
| Statistics display | - | ✓ |
| Settings persistence | - | ✓ |

## Modifying and Rebuilding

After making changes to any of the source files (`multi_client_proxy.py`, `proxy_gui.py`, or `ai_handler.py`), rebuild the standalone app:

### Quick Rebuild

```bash
cd /Users/ivan.dallaserra/Git/Claude/meshbotservus/proxy
./build.sh
```

This will:
1. Clean previous builds
2. Recompile all modified source files
3. Create a new `MeshtasticProxy.app` with your changes

### Development Workflow

```bash
# 1. Edit source files (multi_client_proxy.py, proxy_gui.py, etc.)

# 2. Test changes with the GUI from source (optional)
./run_gui.sh

# 3. Rebuild the standalone app
./build.sh

# 4. Test the standalone app
open dist/MeshtasticProxy.app
```

**Build time:** Approximately 30-60 seconds

**Note:** Always use `./build.sh` instead of running PyInstaller directly, as it ensures the virtual environment and dependencies are properly configured.

## Building Tips

### Reducing Binary Size

To create a smaller binary, you can:
1. Remove unused packages from requirements.txt
2. Use `--onefile` option (already enabled in .spec)
3. Use UPX compression (already enabled in .spec)

### Adding an Icon

To add a custom icon to your binary:

1. Create or obtain an icon file:
   - macOS: `.icns` file
   - Windows: `.ico` file
   - Linux: `.png` file

2. Edit `proxy_gui.spec` and update the `icon` parameter:
```python
exe = EXE(
    ...
    icon='path/to/your/icon.icns',  # or .ico for Windows
    ...
)
```

3. Rebuild using the build script

## Troubleshooting

### "ModuleNotFoundError" when running binary

Make sure all hidden imports are listed in `proxy_gui.spec`. Add any missing modules to the `hiddenimports` list.

### GUI doesn't start

Check that PyQt6 is properly installed:
```bash
python3 -c "from PyQt6 import QtWidgets"
```

### Radio connection fails

- Verify your radio's IP address and TCP port
- Ensure your radio has TCP networking enabled
- Check firewall settings

### Gemini AI not working

- Verify your GEMINI_API_KEY is correct
- Ensure the `ai_handler.py` file is present
- Check the logs for specific error messages

## Command-Line Version

The original command-line version is still available in `multi_client_proxy.py`. Use it for:
- Server deployments
- Running as a system service
- Automation and scripting
- Lower resource usage

## License

Same as the original proxy script.

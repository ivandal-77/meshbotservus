# Quick Start Guide - Meshtastic Proxy GUI

## Running the GUI

### From Source
```bash
cd /Users/ivan.dallaserra/Git/Claude/meshbotservus/proxy
./run_gui.sh
```

### Standalone App
```bash
open /Users/ivan.dallaserra/Git/Claude/meshbotservus/proxy/dist/MeshtasticProxy.app
```

## After Modifying Code

**Modified `multi_client_proxy.py`, `proxy_gui.py`, or `ai_handler.py`?**

Rebuild the standalone app:
```bash
cd /Users/ivan.dallaserra/Git/Claude/meshbotservus/proxy
./build.sh
```

That's it! The new `MeshtasticProxy.app` will be in the `dist/` folder.

## Project Structure

```
proxy/
├── proxy_gui.py              # Qt GUI application
├── multi_client_proxy.py     # Core proxy logic
├── requirements.txt          # Python dependencies
├── run_gui.sh               # Run from source
├── build.sh                 # Build standalone app
├── proxy_gui_onedir.spec    # PyInstaller configuration
└── dist/
    └── MeshtasticProxy.app  # Standalone app (after building)
```

## Common Commands

| Task | Command |
|------|---------|
| Run from source | `./run_gui.sh` |
| Rebuild app | `./build.sh` |
| Open standalone app | `open dist/MeshtasticProxy.app` |
| Install dependencies | `pip install -r requirements.txt` |

## Need Help?

- Full documentation: [README_GUI.md](README_GUI.md)
- Distribution guide: [DISTRIBUTION.md](DISTRIBUTION.md)
- Original proxy docs: `../README.md` (if exists)

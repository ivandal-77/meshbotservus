# Third-Party Licenses

This project uses the following third-party libraries and frameworks:

## Core Dependencies

### PyQt6
- **License**: GPL v3 / Commercial
- **Project**: https://www.riverbankcomputing.com/software/pyqt/
- **Usage**: GUI framework for the Meshtastic Proxy application
- **License Text**: https://www.gnu.org/licenses/gpl-3.0.html
- **Note**: This project is distributed under GPLv3 to comply with PyQt6's licensing. For commercial use without GPL obligations, a commercial PyQt6 license is required.

### Meshtastic Python Library
- **License**: Apache 2.0
- **Project**: https://github.com/meshtastic/python
- **Usage**: Communication protocol for Meshtastic devices
- **License Text**: https://github.com/meshtastic/python/blob/master/LICENSE

### python-telegram-bot
- **License**: LGPL v3
- **Project**: https://github.com/python-telegram-bot/python-telegram-bot
- **Usage**: Telegram Bot API integration
- **License Text**: https://www.gnu.org/licenses/lgpl-3.0.html

### Google Generative AI SDK (google-genai)
- **License**: Apache 2.0
- **Project**: https://github.com/googleapis/python-genai
- **Usage**: Google Gemini AI integration
- **License Text**: https://www.apache.org/licenses/LICENSE-2.0

### PyInstaller
- **License**: GPL v2+ with special exception
- **Project**: https://github.com/pyinstaller/pyinstaller
- **Usage**: Build tool for standalone binaries
- **License Text**: https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt
- **Note**: PyInstaller's license allows distribution of bundled applications

## Additional Dependencies

All other dependencies are transitively included through the above packages. Refer to their respective licenses:

- **asyncio-mqtt**: BSD-3-Clause
- **httpx**: BSD-3-Clause
- **protobuf**: BSD-3-Clause

## License Compliance

### GPL Compliance
This project's source code is available at: https://github.com/ivandal-77/meshbotservus

As required by GPLv3 (PyQt6), this entire project is licensed under GPLv3. The source code is freely available, and any distributed binaries are accompanied by this source code repository.

### Commercial Use
If you wish to use this software in a commercial product without GPLv3 obligations:
1. Purchase a commercial PyQt6 license from Riverbank Computing
2. Replace PyQt6 with an alternative GUI framework (e.g., Tkinter, wxPython)
3. Run in CLI mode without the GUI component

## Acknowledgments

We gratefully acknowledge the following open source projects:
- **Meshtastic** - For the excellent LoRa mesh networking platform
- **PyQt6 / Qt** - For the powerful cross-platform GUI framework
- **python-telegram-bot** - For the comprehensive Telegram Bot API wrapper
- **Google** - For the Gemini AI API and SDK
- **PyInstaller** - For enabling standalone application distribution

## License Notices

### PyQt6 GPL Notice
```
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

### Apache 2.0 Components
The Meshtastic library and Google Generative AI SDK are licensed under Apache 2.0, which is compatible with GPLv3.

### LGPL Components
The python-telegram-bot library is licensed under LGPLv3, which is compatible with GPLv3.

## Questions?

For licensing questions, please refer to:
- PyQt6 licensing: https://www.riverbankcomputing.com/commercial/license-faq
- This project's issues: https://github.com/ivandal-77/meshbotservus/issues

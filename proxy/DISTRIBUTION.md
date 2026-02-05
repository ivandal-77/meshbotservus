# Distribution Guide for MeshtasticProxy

## Distributing the Standalone Application

The `MeshtasticProxy.app` is a fully self-contained macOS application that can be distributed to other users.

### What's Included (91MB)

✅ **Complete standalone package:**
- Python 3.14 runtime
- PyQt6 GUI framework
- Meshtastic library with protocol buffers
- Google Generative AI library
- All proxy and AI handler code
- All system dependencies

### Distribution Methods

#### Option 1: Direct Copy (for local/trusted distribution)

Simply copy the entire `dist/MeshtasticProxy.app` folder to another location or Mac.

```bash
# Create a distributable folder
mkdir MeshtasticProxyDist
cp -R dist/MeshtasticProxy.app MeshtasticProxyDist/

# Optional: Add README
cp README_GUI.md MeshtasticProxyDist/README.txt
```

Recipients can drag the app to their Applications folder and run it.

#### Option 2: Create a DMG (recommended for wider distribution)

Create a disk image for easy installation:

```bash
# Create a DMG
hdiutil create -volname "Meshtastic Proxy" -srcfolder dist/MeshtasticProxy.app -ov -format UDZO MeshtasticProxy.dmg
```

Users can:
1. Open the DMG
2. Drag the app to Applications
3. Launch from Applications

#### Option 3: Compress to ZIP

For sharing via email or download:

```bash
cd dist
zip -r MeshtasticProxy.zip MeshtasticProxy.app
```

### First-Run Instructions for Recipients

When users first run the app on a new Mac, macOS may show a security warning because the app isn't signed with an Apple Developer ID.

**To allow the app to run:**

1. Try to open the app (it will be blocked)
2. Go to **System Settings** > **Privacy & Security**
3. Click **"Open Anyway"** next to the security warning
4. Confirm you want to open the app

Alternatively, users can right-click the app and select **"Open"** to bypass the warning.

### Signing the App (for official distribution)

For official distribution without security warnings, you need:

1. **Apple Developer Account** ($99/year)
2. **Code signing certificate**

```bash
# Sign the app
codesign --force --deep --sign "Developer ID Application: Your Name" MeshtasticProxy.app

# Notarize for Gatekeeper
xcrun notarytool submit MeshtasticProxy.dmg --apple-id your@email.com --team-id TEAMID --wait

# Staple the notarization
xcrun stapler staple MeshtasticProxy.app
```

### Configuration Requirements

Users will need to configure:
- Radio IP address and port
- Listen settings (usually defaults are fine)
- Gemini API key (optional, only for `/gem` AI commands)

### Network Requirements

The app requires:
- Network access to the Meshtastic radio (TCP connection)
- Internet access (for `/gem` AI features)
- No special firewall rules (uses standard TCP)

### Troubleshooting for Users

**App won't open:**
- Remove quarantine: `xattr -cr /path/to/MeshtasticProxy.app`
- Check System Settings > Privacy & Security

**Can't connect to radio:**
- Verify radio IP address
- Ensure radio has TCP networking enabled
- Check firewall settings

**AI features not working:**
- Set GEMINI_API_KEY environment variable
- Or enter it in the GUI settings

### Size Considerations

- App bundle: ~91 MB
- DMG (compressed): ~50-60 MB
- ZIP (compressed): ~45-55 MB

### License and Credits

Include appropriate license information and credits when distributing:
- Your proxy code license
- Meshtastic library license
- PyQt6 license (GPL or commercial)
- Third-party dependencies licenses

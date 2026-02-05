# Telegram Integration Setup Guide

The Meshtastic Proxy now supports bidirectional message forwarding between your Meshtastic radio network and a Telegram channel/group.

## Features

- **Radio → Telegram**: All text messages from the radio are automatically forwarded to your Telegram channel
- **Telegram → Radio**: Messages sent in the Telegram channel are forwarded to the Meshtastic radio network
- **Optional**: Only enabled if you provide both Bot Token and Chat ID

## Setup Instructions

### Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the prompts to:
   - Choose a name for your bot (e.g., "Meshtastic Bridge")
   - Choose a username for your bot (must end in 'bot', e.g., "meshtastic_bridge_bot")
4. **Save the Bot Token** - you'll receive something like:
   ```
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
   ```
   This is your **Telegram Bot Token**

### Step 2: Get Your Chat ID

#### Option A: For a Channel
1. Create a new Telegram channel (or use existing)
2. Add your bot as an administrator:
   - Go to channel settings → Administrators → Add Administrator
   - Search for your bot username and add it
   - Give it permission to "Post Messages"
3. Send a test message to the channel
4. Visit this URL in your browser (replace `YOUR_BOT_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
5. Look for `"chat":{"id":-100XXXXXXXXX}` in the response
6. The number (including the minus sign) is your **Chat ID**
   - Example: `-1001234567890`

#### Option B: For a Group
1. Create a new Telegram group (or use existing)
2. Add your bot to the group
3. Send a test message in the group
4. Visit the getUpdates URL (same as above)
5. Find the chat ID in the response (will be negative number)

#### Option C: For Direct Messages (Private Chat)
1. Start a chat with your bot
2. Send any message to the bot
3. Visit the getUpdates URL
4. Find your chat ID (will be a positive number)

### Step 3: Configure the Proxy GUI

1. Open the Meshtastic Proxy GUI
2. Fill in the Telegram fields:
   - **Telegram Bot Token**: Paste your bot token from Step 1
     - Format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789`
   - **Telegram Chat ID**: Enter your chat/channel ID from Step 2
     - Format for channels/groups: `-1001234567890` (negative number)
     - Format for private chat: `1234567890` (positive number)
3. Start the proxy

## How It Works

### Radio → Telegram
When someone sends a message on the Meshtastic network:
```
📡 Node-12345678 (14:30:45)
Hello from the radio!
```

### Telegram → Radio
When someone sends a message in the Telegram channel:
```
Message on radio will show:
[TG:username] Hello from Telegram!
```

## Testing

1. After starting the proxy, check the logs for:
   ```
   Telegram bot started, listening to chat_id: -1001234567890
   Telegram: enabled
   Radio messages are forwarded to Telegram
   Telegram messages are forwarded to radio
   ```

2. Send a test message from your Meshtastic device
   - It should appear in your Telegram channel

3. Send a test message in Telegram
   - It should appear on Meshtastic devices as `[TG:username] message`

## Troubleshooting

### Bot Token Invalid
- Error: "Failed to start Telegram bot"
- Solution: Double-check your bot token from @BotFather
- Make sure there are no extra spaces

### Wrong Chat ID
- Symptom: Telegram bot starts but messages don't appear
- Solution:
  - Ensure the Chat ID includes the minus sign for groups/channels
  - Verify the bot is an administrator in the channel/group
  - Send a new test message and re-check getUpdates

### No Permission to Post
- Error: Bot can't send messages
- Solution: In channel/group settings, make sure the bot has "Post Messages" permission

### Messages Not Forwarding
- Check that both Bot Token AND Chat ID are filled in
- Restart the proxy after entering credentials
- Check logs for any error messages

## Security Notes

- **Bot Token** and **Chat ID** are NOT saved to settings for security
- You'll need to re-enter them each time you start the GUI
- Never share your bot token publicly
- Anyone with your bot token can control your bot

## Disabling Telegram

To disable Telegram integration, simply:
1. Clear both the Bot Token and Chat ID fields
2. Restart the proxy

Or don't fill them in at all - the integration is completely optional.

## Advanced: Getting Chat ID Programmatically

You can also get your Chat ID with this Python snippet:
```python
import requests

bot_token = "YOUR_BOT_TOKEN"
url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
response = requests.get(url)
print(response.json())
```

Look for the `"chat":{"id":...}` in the output.

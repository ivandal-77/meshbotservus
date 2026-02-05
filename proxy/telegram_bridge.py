#!/usr/bin/env python3
"""
Telegram Bridge for Meshtastic Proxy
Forwards messages between Meshtastic radio and Telegram channel
"""

import asyncio
import logging
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramBridge:
    """Handles bidirectional message forwarding between Meshtastic and Telegram."""

    def __init__(self, bot_token: str, chat_id: str, message_callback: Optional[Callable] = None):
        """
        Initialize Telegram bridge.

        Args:
            bot_token: Telegram Bot API token (from @BotFather)
            chat_id: Telegram chat/channel ID (can be negative for groups/channels)
            message_callback: Async callback to send messages to radio: callback(text: str)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.message_callback = message_callback
        self.application = None
        self.running = False

    async def start(self) -> bool:
        """Start the Telegram bot."""
        try:
            from telegram import Update
            from telegram.ext import Application, MessageHandler, filters, ContextTypes

            logger.info("Initializing Telegram bot...")

            # Create application
            self.application = Application.builder().token(self.bot_token).build()

            # Add message handler for the specific chat
            async def handle_telegram_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
                """Handle incoming Telegram messages."""
                if not update.message or not update.message.text:
                    return

                # Only process messages from the configured chat
                if str(update.message.chat_id) != str(self.chat_id):
                    return

                text = update.message.text
                user = update.message.from_user
                username = user.username or user.first_name or "Unknown"

                logger.info(f"Telegram message from {username}: {text}")

                # Forward to radio via callback
                if self.message_callback:
                    try:
                        await self.message_callback(f"[TG:{username}] {text}")
                    except Exception as e:
                        logger.error(f"Failed to forward Telegram message to radio: {e}")

            # Register handler (allow all text messages including commands like /gem)
            self.application.add_handler(
                MessageHandler(filters.TEXT, handle_telegram_message)
            )

            # Start bot in background
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            self.running = True
            logger.info(f"Telegram bot started, listening to chat_id: {self.chat_id}")
            return True

        except ImportError:
            logger.error("python-telegram-bot not installed. Install with: pip install python-telegram-bot")
            return False
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            return False

    async def stop(self) -> None:
        """Stop the Telegram bot."""
        if self.application:
            try:
                logger.info("Stopping Telegram bot...")
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                self.running = False
                logger.info("Telegram bot stopped")
            except Exception as e:
                logger.error(f"Error stopping Telegram bot: {e}")

    async def send_message(self, text: str) -> bool:
        """
        Send a message to Telegram.

        Args:
            text: Message text to send

        Returns:
            True if successful, False otherwise
        """
        if not self.application or not self.running:
            logger.warning("Telegram bot not running, cannot send message")
            return False

        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                text=text,
                parse_mode='HTML'
            )
            logger.debug(f"Sent message to Telegram: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to Telegram: {e}")
            return False

    async def send_radio_message(self, sender: str, text: str) -> bool:
        """
        Format and send a radio message to Telegram.

        Args:
            sender: Message sender identifier
            text: Message content

        Returns:
            True if successful, False otherwise
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"📡 <b>{sender}</b> ({timestamp})\n{text}"
        return await self.send_message(formatted)

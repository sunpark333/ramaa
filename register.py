# register.py - Channel registration logic

import logging
from datetime import datetime
import html
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ChannelRegistration:
    def __init__(self, database):
        self.db = database

    async def handle_forwarded_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle forwarded messages"""
        message = update.message

        try:
            # Check if message is forwarded
            if not hasattr(message, 'forward_origin') or not message.forward_origin:
                return

            forward_origin = message.forward_origin
            forward_chat = None

            # Get forward chat information
            if hasattr(forward_origin, 'chat'):
                forward_chat = forward_origin.chat
            elif hasattr(forward_origin, 'sender_name'):
                # Hidden user - can't get channel info
                await message.reply_text("""
⚠️ Forward Origin Hidden

This message was forwarded from a hidden user. Channel information not available.

Please forward a message directly from your channel.
""")
                return

            # Process channel forward
            if forward_chat and forward_chat.type in ['channel', 'supergroup']:
                channel_id = forward_chat.id
                channel_name = forward_chat.title
                channel_username = forward_chat.username

                # Register channel
                is_new, status_message = self.db.register_channel(
                    channel_id, channel_name, channel_username
                )

                # Try to get member count if bot is admin in the channel
                try:
                    chat_member_count = await context.bot.get_chat_member_count(channel_id)
                    self.db.update_channel_member_count(channel_id, chat_member_count)
                    member_info = f"\n👥 Current Members: {chat_member_count}"
                except Exception as e:
                    member_info = "\n⚠️ Member count unavailable (bot needs admin rights)"
                    logger.warning(f"Could not get member count for {channel_id}: {e}")

                # Send response to user (not to channel)
                if is_new:
                    response = f"""
🎉 Channel Registered Successfully!

📋 Channel Details:
• Name: {channel_name}
• ID: {channel_id}
• Username: @{channel_username if channel_username else 'None'}
{member_info}

✅ Your channel is now registered and being tracked!
"""
                else:
                    response = f"""
📊 Channel Activity Updated!

📋 Channel: {channel_name}
{member_info}

🔄 Status: {status_message}
"""

                await message.reply_text(response)
                logger.info(f"Handled forwarded message from channel: {channel_id}")

            elif forward_chat and forward_chat.type in ['group', 'private']:
                # Only channels supported
                await message.reply_text("""
⚠️ Only Channels Supported

This bot only registers Telegram Channels, not Groups or Private Chats.

Please forward a message from your Channel.
""")

        except Exception as e:
            logger.error(f"Forwarded message error: {e}")
            await message.reply_text("""
❌ Error Processing Message

There was an error processing the forwarded message.

Please try:
• Adding bot to channel as admin
• Forwarding a message directly from channel
""")

    async def handle_bot_added_to_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle when bot is added to a channel"""
        try:
            if update.my_chat_member:
                chat_member = update.my_chat_member
                chat = chat_member.chat

                # Only process channels
                if chat.type in ['channel', 'supergroup']:
                    new_status = chat_member.new_chat_member.status

                    # If bot was added as admin/member
                    if new_status in ['administrator', 'member']:
                        channel_id = chat.id
                        channel_name = chat.title
                        channel_username = chat.username

                        # Register channel
                        is_new, status_message = self.db.register_channel(
                            channel_id, channel_name, channel_username
                        )

                        # Get member count
                        try:
                            chat_member_count = await context.bot.get_chat_member_count(channel_id)
                            self.db.update_channel_member_count(channel_id, chat_member_count)
                            member_info = f"\n👥 Current Members: {chat_member_count}"
                        except Exception as e:
                            member_info = "\n⚠️ Member count unavailable"
                            logger.warning(f"Could not get member count for {channel_id}: {e}")

                        logger.info(f"Bot added to channel: {channel_id} - {channel_name}")

                        # Send confirmation message to user who added bot (not to channel)
                        try:
                            user_id = chat_member.from_user.id
                            if is_new:
                                confirmation_msg = f"""
🎉 Channel Registration Successful!

✅ {channel_name} is now registered!
{member_info}

📊 Features:
• Member count tracking
• Channel activity monitoring
• Broadcast functionality

Thank you! Your channel has been registered successfully.
"""
                            else:
                                confirmation_msg = f"""
📊 Channel Activity Updated!

✅ {channel_name} is already registered.
{member_info}

Status: {status_message}
"""
                            await context.bot.send_message(chat_id=user_id, text=confirmation_msg)
                        except Exception as e:
                            logger.warning(f"Could not send confirmation message: {e}")

        except Exception as e:
            logger.error(f"Bot added error: {e}")

# register.py - Channel registration logic
import logging
from typing import Optional
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

class ChannelRegistration:
    def __init__(self, database):
        self.db = database
    
    async def handle_forwarded_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle forwarded messages"""
        message = update.message
        
        try:
            if not hasattr(message, 'forward_origin') or not message.forward_origin:
                return
            
            forward_origin = message.forward_origin
            forward_chat = None
            
            if hasattr(forward_origin, 'chat'):
                forward_chat = forward_origin.chat
            elif hasattr(forward_origin, 'sender_name'):
                await message.reply_text(
                    "⚠️ Forward Origin Hidden\n\n"
                    "This message was forwarded from a hidden user. Channel information not available.\n\n"
                    "Please forward a message directly from your channel."
                )
                return
            
            if forward_chat and forward_chat.type in ['channel', 'supergroup']:
                channel_id = forward_chat.id
                channel_name = forward_chat.title
                channel_username = forward_chat.username
                
                is_new, status_message = self.db.register_channel(
                    channel_id, channel_name, channel_username
                )
                
                try:
                    chat_member_count = await context.bot.get_chat_member_count(channel_id)
                    self.db.update_channel_member_count(channel_id, chat_member_count)
                    member_info = f"\n👥 Current Members: {chat_member_count}"
                except Exception as e:
                    member_info = "\n⚠️ Member count unavailable (bot needs admin rights)"
                    logger.warning(f"Could not get member count for {channel_id}: {e}")
                
                if is_new:
                    response = (
                        f"🎉 Channel Registered Successfully!\n\n"
                        f"📋 Channel Details:\n"
                        f"• Name: {channel_name}\n"
                        f"• ID: {channel_id}\n"
                        f"• Username: @{channel_username if channel_username else 'None'}\n"
                        f"{member_info}\n\n"
                        f"✅ Your channel is now registered and being tracked!"
                    )
                else:
                    response = (
                        f"📊 Channel Activity Updated!\n\n"
                        f"📋 Channel: {channel_name}\n"
                        f"{member_info}\n"
                        f"🔄 Status: {status_message}"
                    )
                
                await message.reply_text(response)
                logger.info(f"Handled forwarded message from channel: {channel_id}")
            
            elif forward_chat and forward_chat.type in ['group', 'private']:
                await message.reply_text(
                    "⚠️ Only Channels Supported\n\n"
                    "This bot only registers Telegram Channels, not Groups or Private Chats.\n\n"
                    "Please forward a message from your Channel."
                )
            
        except Exception as e:
            logger.error(f"Forwarded message error: {e}")
            await message.reply_text(
                "❌ Error Processing Message\n\n"
                "There was an error processing the forwarded message.\n\n"
                "Please try:\n"
                "• Adding bot to channel as admin\n"
                "• Forwarding a message directly from channel"
            )

    async def handle_bot_added_to_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle when bot is added to a channel"""
        try:
            if update.my_chat_member:
                chat_member = update.my_chat_member
                chat = chat_member.chat
                
                if chat.type in ['channel', 'supergroup']:
                    new_status = chat_member.new_chat_member.status
                    
                    if new_status in ['administrator', 'member']:
                        channel_id = chat.id
                        channel_name = chat.title
                        channel_username = chat.username
                        
                        is_new, status_message = self.db.register_channel(
                            channel_id, channel_name, channel_username
                        )
                        
                        try:
                            chat_member_count = await context.bot.get_chat_member_count(channel_id)
                            self.db.update_channel_member_count(channel_id, chat_member_count)
                            member_info = f"\n👥 Current Members: {chat_member_count}"
                        except Exception as e:
                            member_info = "\n⚠️ Member count unavailable"
                            logger.warning(f"Could not get member count for {channel_id}: {e}")
                        
                        logger.info(f"Bot added to channel: {channel_id} - {channel_name}")
                        
                        try:
                            user_id = chat_member.from_user.id
                            if is_new:
                                confirmation_msg = (
                                    f"🎉 Channel Registration Successful!\n\n"
                                    f"✅ {channel_name} is now registered!\n"
                                    f"{member_info}\n\n"
                                    f"📊 Features:\n"
                                    f"• Member count tracking\n"
                                    f"• Channel activity monitoring\n"
                                    f"• Broadcast functionality\n\n"
                                    f"Thank you! Your channel has been registered successfully."
                                )
                            else:
                                confirmation_msg = (
                                    f"📊 Channel Activity Updated!\n\n"
                                    f"✅ {channel_name} is already registered.\n"
                                    f"{member_info}\n\n"
                                    f"Status: {status_message}"
                                )
                            await context.bot.send_message(chat_id=user_id, text=confirmation_msg)
                        except Exception as e:
                            logger.warning(f"Could not send confirmation message: {e}")
                            
        except Exception as e:
            logger.error(f"Bot added error: {e}")

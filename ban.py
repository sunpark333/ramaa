# ban.py - User banning and unbanning functionality across all registered channels
import logging
import asyncio
from typing import Dict, List, Tuple, Any, Optional
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.error import BadRequest, Forbidden

logger = logging.getLogger(__name__)

class UserBanManager:
    def __init__(self, database):
        self.db = database
        self.broadcast_messages: Dict[str, Dict] = {}
    
    async def ban_user_from_all_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
        """Ban user from all registered channels"""
        try:
            if not user_id.isdigit():
                await update.message.reply_text("❌ Invalid user ID. Please provide a valid numeric user ID.")
                return
            
            user_id_int = int(user_id)
            channels = self.db.get_registered_channels()
            
            if not channels:
                await update.message.reply_text("❌ No channels registered yet.")
                return
            
            successful_bans = 0
            failed_bans = 0
            results: List[str] = []
            
            for channel in channels:
                channel_id, channel_name, channel_username, _, _, _, _ = channel
                
                try:
                    await context.bot.ban_chat_member(
                        chat_id=channel_id,
                        user_id=user_id_int
                    )
                    successful_bans += 1
                    results.append(f"✅ {channel_name} - Banned successfully")
                    logger.info(f"User {user_id_int} banned from channel {channel_id}")
                    
                except BadRequest as e:
                    error_msg = str(e).lower()
                    if "user not found" in error_msg:
                        results.append(f"❌ {channel_name} - User not found in this channel")
                    elif "not enough rights" in error_msg:
                        results.append(f"❌ {channel_name} - Bot doesn't have ban rights")
                    elif "user is an administrator" in error_msg:
                        results.append(f"❌ {channel_name} - User is an administrator")
                    else:
                        results.append(f"❌ {channel_name} - Error: {str(e)[:50]}...")
                    failed_bans += 1
                    logger.warning(f"Failed to ban from {channel_id}: {e}")
                    
                except Forbidden:
                    results.append(f"❌ {channel_name} - Bot was kicked from channel")
                    failed_bans += 1
                    logger.warning(f"Bot not in channel {channel_id} anymore")
                
                except Exception as e:
                    results.append(f"❌ {channel_name} - Unexpected error")
                    failed_bans += 1
                    logger.error(f"Unexpected error banning from {channel_id}: {e}")
            
            total_channels = len(channels)
            result_message = (
                f"🔨 Ban Operation Completed\n\n"
                f"👤 User ID: {user_id}\n"
                f"📊 Results:\n"
                f"• Total Channels: {total_channels}\n"
                f"• ✅ Successful Bans: {successful_bans}\n"
                f"• ❌ Failed Bans: {failed_bans}\n\n"
                f"📋 Detailed Results:\n"
            )
            
            for i, result in enumerate(results[:15], 1):
                result_message += f"{i}. {result}\n"
            
            if len(results) > 15:
                result_message += f"\n... and {len(results) - 15} more channels"
            
            await update.message.reply_text(result_message)
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format. Please provide a valid numeric ID.")
        except Exception as e:
            logger.error(f"Ban operation error: {e}")
            await update.message.reply_text("❌ Error performing ban operation.")

    async def unban_user_from_all_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str) -> None:
        """Unban user from all registered channels"""
        try:
            if not user_id.isdigit():
                await update.message.reply_text("❌ Invalid user ID. Please provide a valid numeric user ID.")
                return
            
            user_id_int = int(user_id)
            channels = self.db.get_registered_channels()
            
            if not channels:
                await update.message.reply_text("❌ No channels registered yet.")
                return
            
            successful_unbans = 0
            failed_unbans = 0
            results: List[str] = []
            
            for channel in channels:
                channel_id, channel_name, channel_username, _, _, _, _ = channel
                
                try:
                    await context.bot.unban_chat_member(
                        chat_id=channel_id,
                        user_id=user_id_int,
                        only_if_banned=True
                    )
                    successful_unbans += 1
                    results.append(f"✅ {channel_name} - Unbanned successfully")
                    logger.info(f"User {user_id_int} unbanned from channel {channel_id}")
                    
                except BadRequest as e:
                    error_msg = str(e).lower()
                    if "user not found" in error_msg:
                        results.append(f"ℹ️ {channel_name} - User not found")
                    elif "not enough rights" in error_msg:
                        results.append(f"❌ {channel_name} - Bot doesn't have unban rights")
                    elif "user not banned" in error_msg:
                        results.append(f"ℹ️ {channel_name} - User not banned")
                    elif "chat not found" in error_msg:
                        results.append(f"❌ {channel_name} - Chat not found")
                    else:
                        results.append(f"❌ {channel_name} - Error: {str(e)[:50]}...")
                    failed_unbans += 1
                    logger.warning(f"Failed to unban from {channel_id}: {e}")
                    
                except Forbidden:
                    results.append(f"❌ {channel_name} - Bot was kicked from channel")
                    failed_unbans += 1
                    logger.warning(f"Bot not in channel {channel_id} anymore")
                
                except Exception as e:
                    results.append(f"❌ {channel_name} - Unexpected error")
                    failed_unbans += 1
                    logger.error(f"Unexpected error unbanning from {channel_id}: {e}")
            
            total_channels = len(channels)
            result_message = (
                f"🔓 Unban Operation Completed\n\n"
                f"👤 User ID: {user_id}\n"
                f"📊 Results:\n"
                f"• Total Channels: {total_channels}\n"
                f"• ✅ Successful Unbans: {successful_unbans}\n"
                f"• ❌ Failed Unbans: {failed_unbans}\n\n"
                f"📋 Detailed Results:\n"
            )
            
            for i, result in enumerate(results[:15], 1):
                result_message += f"{i}. {result}\n"
            
            if len(results) > 15:
                result_message += f"\n... and {len(results) - 15} more channels"
            
            await update.message.reply_text(result_message)
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID format. Please provide a valid numeric ID.")
        except Exception as e:
            logger.error(f"Unban operation error: {e}")
            await update.message.reply_text("❌ Error performing unban operation.")

    async def broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Broadcast message to all registered channels"""
        try:
            if not update.message.reply_to_message:
                await update.message.reply_text(
                    "📢 Broadcast Usage:\n\n"
                    "Reply to a message with /broadcast command to send it to all registered channels.\n\n"
                    "Example:\n"
                    "1. Send your message in any chat\n"
                    "2. Reply to that message with /broadcast\n"
                    "3. Message will be sent to all channels\n\n"
                    "Note: Message formatting will be preserved exactly as you sent it."
                )
                return

            message_to_broadcast = update.message.reply_to_message
            channels = self.db.get_registered_channels()
            
            if not channels:
                await update.message.reply_text("❌ No channels registered yet.")
                return

            status_message = await update.message.reply_text("🔄 Starting broadcast...")
            successful_broadcasts = 0
            failed_broadcasts = 0
            broadcast_results: Dict[str, Dict] = {}
            
            for channel in channels:
                channel_id, channel_name, channel_username, _, _, _, _ = channel
                
                try:
                    sent_message = await self._send_message_to_channel(context, channel_id, message_to_broadcast)
                    
                    successful_broadcasts += 1
                    broadcast_results[channel_id] = {
                        'name': channel_name,
                        'status': 'success',
                        'message_id': sent_message.message_id
                    }
                    
                    if (successful_broadcasts + failed_broadcasts) % 5 == 0:
                        await status_message.edit_text(
                            f"🔄 Broadcasting...\n"
                            f"✅ Successful: {successful_broadcasts}\n"
                            f"❌ Failed: {failed_broadcasts}\n"
                            f"📊 Progress: {successful_broadcasts + failed_broadcasts}/{len(channels)}"
                        )
                    
                    await asyncio.sleep(0.5)
                    
                except BadRequest as e:
                    failed_broadcasts += 1
                    broadcast_results[channel_id] = {
                        'name': channel_name,
                        'status': 'failed',
                        'reason': f'BadRequest: {str(e)[:50]}'
                    }
                except Forbidden:
                    failed_broadcasts += 1
                    broadcast_results[channel_id] = {
                        'name': channel_name,
                        'status': 'failed',
                        'reason': 'Bot was kicked from channel'
                    }
                except Exception as e:
                    failed_broadcasts += 1
                    broadcast_results[channel_id] = {
                        'name': channel_name,
                        'status': 'failed',
                        'reason': f'Unexpected error: {str(e)[:50]}'
                    }

            broadcast_id = f"broadcast_{update.message.message_id}"
            self.broadcast_messages[broadcast_id] = broadcast_results

            result_message = (
                f"📢 Broadcast Completed\n\n"
                f"📊 Results:\n"
                f"• Total Channels: {len(channels)}\n"
                f"• ✅ Successful: {successful_broadcasts}\n"
                f"• ❌ Failed: {failed_broadcasts}\n\n"
                f"💾 Broadcast ID: `{broadcast_id}`\n\n"
                f"To delete this broadcast from all channels, use:\n"
                f"`/del {broadcast_id}`"
            )

            failed_channels = [result for result in broadcast_results.values() if result['status'] == 'failed']
            if failed_channels:
                result_message += "\n\n❌ Failed Channels:\n"
                for i, failed in enumerate(failed_channels[:5], 1):
                    result_message += f"{i}. {failed['name']} - {failed['reason']}\n"
                if len(failed_channels) > 5:
                    result_message += f"... and {len(failed_channels) - 5} more"

            await status_message.edit_text(result_message)

        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            await update.message.reply_text("❌ Error during broadcast operation.")

    async def _send_message_to_channel(self, context: ContextTypes.DEFAULT_TYPE, channel_id: str, message) -> Any:
        """Send message to channel with proper formatting"""
        if message.text:
            return await context.bot.send_message(
                chat_id=channel_id,
                text=message.text,
                entities=message.entities,
                parse_mode=None
            )
        elif message.caption:
            if message.photo:
                return await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    parse_mode=None
                )
            elif message.video:
                return await context.bot.send_video(
                    chat_id=channel_id,
                    video=message.video.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    parse_mode=None
                )
            elif message.document:
                return await context.bot.send_document(
                    chat_id=channel_id,
                    document=message.document.file_id,
                    caption=message.caption,
                    caption_entities=message.caption_entities,
                    parse_mode=None
                )
            else:
                return await context.bot.send_message(
                    chat_id=channel_id,
                    text=message.caption,
                    entities=message.caption_entities,
                    parse_mode=None
                )
        else:
            if message.photo:
                return await context.bot.send_photo(
                    chat_id=channel_id,
                    photo=message.photo[-1].file_id
                )
            elif message.video:
                return await context.bot.send_video(
                    chat_id=channel_id,
                    video=message.video.file_id
                )
            elif message.document:
                return await context.bot.send_document(
                    chat_id=channel_id,
                    document=message.document.file_id
                )
            else:
                raise ValueError("Unsupported message type")

    async def delete_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Delete broadcasted messages from all channels"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "🗑️ Delete Broadcast Usage:\n\n"
                    "/del <broadcast_id> - Delete messages from all channels\n\n"
                    "Example:\n"
                    "/del broadcast_123456789\n\n"
                    "To get broadcast ID, check the broadcast completion message."
                )
                return

            broadcast_id = context.args[0]
            
            if broadcast_id not in self.broadcast_messages:
                await update.message.reply_text("❌ Broadcast ID not found or already deleted.")
                return

            broadcast_results = self.broadcast_messages[broadcast_id]
            status_message = await update.message.reply_text("🔄 Starting deletion...")

            successful_deletes = 0
            failed_deletes = 0

            for channel_id, channel_data in broadcast_results.items():
                if channel_data['status'] == 'success':
                    try:
                        await context.bot.delete_message(
                            chat_id=channel_id,
                            message_id=channel_data['message_id']
                        )
                        successful_deletes += 1
                    except Exception as e:
                        failed_deletes += 1
                        logger.error(f"Delete error in {channel_id}: {e}")

                    if (successful_deletes + failed_deletes) % 5 == 0:
                        await status_message.edit_text(
                            f"🔄 Deleting...\n"
                            f"✅ Successful: {successful_deletes}\n"
                            f"❌ Failed: {failed_deletes}\n"
                            f"📊 Progress: {successful_deletes + failed_deletes}/{len(broadcast_results)}"
                        )

                    await asyncio.sleep(0.3)

            del self.broadcast_messages[broadcast_id]

            result_message = (
                f"🗑️ Deletion Completed\n\n"
                f"📊 Results:\n"
                f"• Total Messages: {len(broadcast_results)}\n"
                f"• ✅ Successful Deletes: {successful_deletes}\n"
                f"• ❌ Failed Deletes: {failed_deletes}"
            )

            await status_message.edit_text(result_message)

        except Exception as e:
            logger.error(f"Delete broadcast error: {e}")
            await update.message.reply_text("❌ Error during deletion operation.")

async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ban command"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🔨 Ban Command Usage:\n\n"
                "/ban <user_id> - Ban user from all registered channels\n\n"
                "Example:\n"
                "/ban 123456789\n"
                "/ban 987654321\n\n"
                "Note: The bot must be admin in all channels with ban permissions."
            )
            return
        
        user_id = context.args[0]
        bot_instance = context.bot_data['bot_instance']
        
        if not hasattr(bot_instance, 'ban_manager'):
            bot_instance.ban_manager = UserBanManager(bot_instance.db)
        
        await bot_instance.ban_manager.ban_user_from_all_channels(update, context, user_id)
        
    except Exception as e:
        logger.error(f"Ban command error: {e}")
        await update.message.reply_text("❌ Error processing ban command.")

async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /unban command"""
    try:
        if not context.args:
            await update.message.reply_text(
                "🔓 Unban Command Usage:\n\n"
                "/unban <user_id> - Unban user from all registered channels\n\n"
                "Example:\n"
                "/unban 123456789\n"
                "/unban 987654321\n\n"
                "Note: The bot must be admin in all channels with unban permissions."
            )
            return
        
        user_id = context.args[0]
        bot_instance = context.bot_data['bot_instance']
        
        if not hasattr(bot_instance, 'ban_manager'):
            bot_instance.ban_manager = UserBanManager(bot_instance.db)
        
        await bot_instance.ban_manager.unban_user_from_all_channels(update, context, user_id)
        
    except Exception as e:
        logger.error(f"Unban command error: {e}")
        await update.message.reply_text("❌ Error processing unban command.")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /broadcast command"""
    try:
        bot_instance = context.bot_data['bot_instance']
        
        if not hasattr(bot_instance, 'ban_manager'):
            bot_instance.ban_manager = UserBanManager(bot_instance.db)
        
        await bot_instance.ban_manager.broadcast_message(update, context)
        
    except Exception as e:
        logger.error(f"Broadcast command error: {e}")
        await update.message.reply_text("❌ Error processing broadcast command.")

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /del command"""
    try:
        bot_instance = context.bot_data['bot_instance']
        
        if not hasattr(bot_instance, 'ban_manager'):
            bot_instance.ban_manager = UserBanManager(bot_instance.db)
        
        await bot_instance.ban_manager.delete_broadcast(update, context)
        
    except Exception as e:
        logger.error(f"Delete command error: {e}")
        await update.message.reply_text("❌ Error processing delete command.")

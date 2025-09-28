# ban.py - User banning and unbanning functionality across all registered channels

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.error import BadRequest, Forbidden
import html
import asyncio

logger = logging.getLogger(__name__)

class UserBanManager:
    def __init__(self, database):
        self.db = database
        self.broadcast_messages = {}  # Store broadcast message IDs

    async def ban_user_from_all_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str):
        """Ban user from all registered channels"""
        try:
            # Validate user ID
            if not user_id.isdigit():
                await update.message.reply_text("❌ Invalid user ID. Please provide a valid numeric user ID.")
                return

            user_id_int = int(user_id)

            # Get all registered channels
            channels = self.db.get_registered_channels()
            if not channels:
                await update.message.reply_text("❌ No channels registered yet.")
                return

            successful_bans = 0
            failed_bans = 0
            results = []

            # Ban user from each channel
            for channel in channels:
                channel_id, channel_name, channel_username, _, _, _, _ = channel  # Updated for 7-tuple

                try:
                    # Ban user from channel
                    await context.bot.ban_chat_member(
                        chat_id=channel_id,
                        user_id=user_id_int
                    )

                    successful_bans += 1
                    results.append(f"✅ {channel_name} - Banned successfully")
                    logger.info(f"User {user_id_int} banned from channel {channel_id}")

                except BadRequest as e:
                    if "user not found" in str(e).lower():
                        results.append(f"❌ {channel_name} - User not found in this channel")
                    elif "not enough rights" in str(e).lower():
                        results.append(f"❌ {channel_name} - Bot doesn't have ban rights")
                    elif "user is an administrator" in str(e).lower():
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

            # Prepare result message
            total_channels = len(channels)
            result_message = f"""
🔨 Ban Operation Completed

👤 User ID: {user_id}
📊 Results:
• Total Channels: {total_channels}
• ✅ Successful Bans: {successful_bans}
• ❌ Failed Bans: {failed_bans}

📋 Detailed Results:
"""

            # Add detailed results (limit to avoid message too long error)
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

    async def unban_user_from_all_channels(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: str):
        """Unban user from all registered channels"""
        try:
            # Validate user ID
            if not user_id.isdigit():
                await update.message.reply_text("❌ Invalid user ID. Please provide a valid numeric user ID.")
                return

            user_id_int = int(user_id)

            # Get all registered channels
            channels = self.db.get_registered_channels()
            if not channels:
                await update.message.reply_text("❌ No channels registered yet.")
                return

            successful_unbans = 0
            failed_unbans = 0
            results = []

            # Unban user from each channel
            for channel in channels:
                channel_id, channel_name, channel_username, _, _, _, _ = channel  # Updated for 7-tuple

                try:
                    # Unban user from channel
                    await context.bot.unban_chat_member(
                        chat_id=channel_id,
                        user_id=user_id_int,
                        only_if_banned=True  # Only unban if currently banned
                    )

                    successful_unbans += 1
                    results.append(f"✅ {channel_name} - Unbanned successfully")
                    logger.info(f"User {user_id_int} unbanned from channel {channel_id}")

                except BadRequest as e:
                    if "user not found" in str(e).lower():
                        results.append(f"ℹ️ {channel_name} - User not found")
                    elif "not enough rights" in str(e).lower():
                        results.append(f"❌ {channel_name} - Bot doesn't have unban rights")
                    elif "user not banned" in str(e).lower():
                        results.append(f"ℹ️ {channel_name} - User not banned")
                    elif "chat not found" in str(e).lower():
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

            # Prepare result message
            total_channels = len(channels)
            result_message = f"""
🔓 Unban Operation Completed

👤 User ID: {user_id}
📊 Results:
• Total Channels: {total_channels}
• ✅ Successful Unbans: {successful_unbans}
• ❌ Failed Unbans: {failed_unbans}

📋 Detailed Results:
"""

            # Add detailed results (limit to avoid message too long error)
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

    async def broadcast_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all registered channels"""
        try:
            # Check if message is a reply to the message to broadcast
            if not update.message.reply_to_message:
                await update.message.reply_text("""
📢 Broadcast Usage:

Reply to a message with /broadcast command to send it to all registered channels.

Example:
1. Send your message in any chat
2. Reply to that message with /broadcast
3. Message will be sent to all channels

Note: Message formatting will be preserved exactly as you sent it.
""")
                return

            # Get the message to broadcast
            message_to_broadcast = update.message.reply_to_message

            # Get all registered channels
            channels = self.db.get_registered_channels()
            if not channels:
                await update.message.reply_text("❌ No channels registered yet.")
                return

            # Send initial status
            status_message = await update.message.reply_text("🔄 Starting broadcast...")

            successful_broadcasts = 0
            failed_broadcasts = 0
            broadcast_results = {}

            # Broadcast to each channel
            for channel in channels:
                channel_id, channel_name, channel_username, _, _, _, _ = channel  # Updated for 7-tuple

                try:
                    # Send message with same formatting and media
                    if message_to_broadcast.text:
                        sent_message = await context.bot.send_message(
                            chat_id=channel_id,
                            text=message_to_broadcast.text,
                            entities=message_to_broadcast.entities,
                            parse_mode=None  # Preserve original formatting
                        )

                    elif message_to_broadcast.caption:
                        # Handle media messages with caption
                        if message_to_broadcast.photo:
                            sent_message = await context.bot.send_photo(
                                chat_id=channel_id,
                                photo=message_to_broadcast.photo[-1].file_id,
                                caption=message_to_broadcast.caption,
                                caption_entities=message_to_broadcast.caption_entities,
                                parse_mode=None
                            )

                        elif message_to_broadcast.video:
                            sent_message = await context.bot.send_video(
                                chat_id=channel_id,
                                video=message_to_broadcast.video.file_id,
                                caption=message_to_broadcast.caption,
                                caption_entities=message_to_broadcast.caption_entities,
                                parse_mode=None
                            )

                        elif message_to_broadcast.document:
                            sent_message = await context.bot.send_document(
                                chat_id=channel_id,
                                document=message_to_broadcast.document.file_id,
                                caption=message_to_broadcast.caption,
                                caption_entities=message_to_broadcast.caption_entities,
                                parse_mode=None
                            )

                        else:
                            # Fallback to text
                            sent_message = await context.bot.send_message(
                                chat_id=channel_id,
                                text=message_to_broadcast.caption,
                                entities=message_to_broadcast.caption_entities,
                                parse_mode=None
                            )

                    else:
                        # Handle media without caption
                        if message_to_broadcast.photo:
                            sent_message = await context.bot.send_photo(
                                chat_id=channel_id,
                                photo=message_to_broadcast.photo[-1].file_id
                            )

                        elif message_to_broadcast.video:
                            sent_message = await context.bot.send_video(
                                chat_id=channel_id,
                                video=message_to_broadcast.video.file_id
                            )

                        elif message_to_broadcast.document:
                            sent_message = await context.bot.send_document(
                                chat_id=channel_id,
                                document=message_to_broadcast.document.file_id
                            )

                        else:
                            failed_broadcasts += 1
                            broadcast_results[channel_id] = {
                                'name': channel_name,
                                'status': 'failed',
                                'reason': 'Unsupported message type'
                            }
                            continue

                    successful_broadcasts += 1
                    broadcast_results[channel_id] = {
                        'name': channel_name,
                        'status': 'success',
                        'message_id': sent_message.message_id
                    }

                    # Update status periodically
                    if (successful_broadcasts + failed_broadcasts) % 5 == 0:
                        await status_message.edit_text(
                            f"🔄 Broadcasting...\n"
                            f"✅ Successful: {successful_broadcasts}\n"
                            f"❌ Failed: {failed_broadcasts}\n"
                            f"📊 Progress: {successful_broadcasts + failed_broadcasts}/{len(channels)}"
                        )

                    # Small delay to avoid rate limits
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

            # Store broadcast results for potential deletion
            broadcast_id = f"broadcast_{update.message.message_id}"
            self.broadcast_messages[broadcast_id] = broadcast_results

            # Prepare final result message
            result_message = f"""
📢 Broadcast Completed

📊 Results:
• Total Channels: {len(channels)}
• ✅ Successful: {successful_broadcasts}
• ❌ Failed: {failed_broadcasts}

💾 Broadcast ID: `{broadcast_id}`

To delete this broadcast from all channels, use:
`/del {broadcast_id}`
"""

            # Add failed channels details (first 5 only)
            failed_channels = [result for result in broadcast_results.values() if result['status'] == 'failed']
            if failed_channels:
                result_message += "\n❌ Failed Channels:\n"
                for i, failed in enumerate(failed_channels[:5], 1):
                    result_message += f"{i}. {failed['name']} - {failed['reason']}\n"

                if len(failed_channels) > 5:
                    result_message += f"... and {len(failed_channels) - 5} more"

            await status_message.edit_text(result_message)

        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            await update.message.reply_text("❌ Error during broadcast operation.")

    async def delete_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete broadcasted messages from all channels"""
        try:
            if not context.args:
                await update.message.reply_text("""
🗑️ Delete Broadcast Usage:

/del <broadcast_id> - Delete messages from all channels

Example:
/del broadcast_123456789

To get broadcast ID, check the broadcast completion message.
""")
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

                    # Update status periodically
                    if (successful_deletes + failed_deletes) % 5 == 0:
                        await status_message.edit_text(
                            f"🔄 Deleting...\n"
                            f"✅ Successful: {successful_deletes}\n"
                            f"❌ Failed: {failed_deletes}\n"
                            f"📊 Progress: {successful_deletes + failed_deletes}/{len(broadcast_results)}"
                        )

                    # Small delay to avoid rate limits
                    await asyncio.sleep(0.3)

            # Remove from storage
            del self.broadcast_messages[broadcast_id]

            result_message = f"""
🗑️ Deletion Completed

📊 Results:
• Total Messages: {len(broadcast_results)}
• ✅ Successful Deletes: {successful_deletes}
• ❌ Failed Deletes: {failed_deletes}
"""

            await status_message.edit_text(result_message)

        except Exception as e:
            logger.error(f"Delete broadcast error: {e}")
            await update.message.reply_text("❌ Error during deletion operation.")


async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /ban command"""
    try:
        # Check if user provided user ID
        if not context.args:
            await update.message.reply_text("""
🔨 Ban Command Usage:

/ban <user_id> - Ban user from all registered channels

Example:
/ban 123456789
/ban 987654321

Note: The bot must be admin in all channels with ban permissions.
""")
            return

        user_id = context.args[0]
        bot_instance = context.bot_data['bot_instance']

        # Check if ban manager exists, if not create one
        if not hasattr(bot_instance, 'ban_manager'):
            bot_instance.ban_manager = UserBanManager(bot_instance.db)

        await bot_instance.ban_manager.ban_user_from_all_channels(update, context, user_id)

    except Exception as e:
        logger.error(f"Ban command error: {e}")
        await update.message.reply_text("❌ Error processing ban command.")


async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unban command"""
    try:
        # Check if user provided user ID
        if not context.args:
            await update.message.reply_text("""
🔓 Unban Command Usage:

/unban <user_id> - Unban user from all registered channels

Example:
/unban 123456789
/unban 987654321

Note: The bot must be admin in all channels with unban permissions.
""")
            return

        user_id = context.args[0]
        bot_instance = context.bot_data['bot_instance']

        # Check if ban manager exists, if not create one
        if not hasattr(bot_instance, 'ban_manager'):
            bot_instance.ban_manager = UserBanManager(bot_instance.db)

        await bot_instance.ban_manager.unban_user_from_all_channels(update, context, user_id)

    except Exception as e:
        logger.error(f"Unban command error: {e}")
        await update.message.reply_text("❌ Error processing unban command.")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /broadcast command"""
    try:
        bot_instance = context.bot_data['bot_instance']

        # Check if ban manager exists, if not create one
        if not hasattr(bot_instance, 'ban_manager'):
            bot_instance.ban_manager = UserBanManager(bot_instance.db)

        await bot_instance.ban_manager.broadcast_message(update, context)

    except Exception as e:
        logger.error(f"Broadcast command error: {e}")
        await update.message.reply_text("❌ Error processing broadcast command.")


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /del command"""
    try:
        bot_instance = context.bot_data['bot_instance']

        # Check if ban manager exists, if not create one
        if not hasattr(bot_instance, 'ban_manager'):
            bot_instance.ban_manager = UserBanManager(bot_instance.db)

        await bot_instance.ban_manager.delete_broadcast(update, context)

    except Exception as e:
        logger.error(f"Delete command error: {e}")
        await update.message.reply_text("❌ Error processing delete command.")

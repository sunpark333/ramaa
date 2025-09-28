# main.py - Main bot application for Render hosting

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ChatMemberHandler, ContextTypes, CallbackQueryHandler
from mongodb_database import MongoDBDatabase
from register import ChannelRegistration
from ban import ban_command, unban_command, broadcast_command, delete_command
from flask import Flask
from threading import Thread
import time
import asyncio

# Flask app for uptimerobot pinging
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Your Bot Token - Use environment variable for security
BOT_TOKEN = os.getenv('BOT_TOKEN', "")

# Admin user IDs - Replace with your admin IDs
ADMIN_IDS = [123456789, 987654321]  # यहाँ अपने एडमिन IDs डालें

class ChannelRegistrationBot:
    def __init__(self):
        self.db = MongoDBDatabase()
        self.registration = ChannelRegistration(self.db)

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command with admin check"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते। केवल एडमिन्स ही उपयोग कर सकते हैं।")
        return

    welcome_message = "🤖 Channel Registration Bot"
    keyboard = [
        [InlineKeyboardButton("📖 How to Use", callback_data="how_to_use")],
        [InlineKeyboardButton("📋 Channel List", callback_data="list_channels")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command with admin check"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return

    await show_how_to_use(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button clicks"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not is_admin(user_id):
        await query.edit_message_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return

    if query.data == "how_to_use":
        await show_how_to_use(update, context)
    elif query.data == "list_channels":
        await show_channel_list(update, context)
    elif query.data == "stats":
        await show_stats(update, context)
    elif query.data == "back_to_main":
        await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    keyboard = [
        [InlineKeyboardButton("📖 How to Use", callback_data="how_to_use")],
        [InlineKeyboardButton("📋 Channel List", callback_data="list_channels")],
        [InlineKeyboardButton("📊 Statistics", callback_data="stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🤖 Channel Registration Bot",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("🤖 Channel Registration Bot", reply_markup=reply_markup)

async def show_how_to_use(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show how to use instructions"""
    help_text = """
📖 How to Use Guide

What this bot does:
✅ Automatically registers Telegram channels
✅ Tracks channel member counts
🔨 Ban users from all channels
📢 Broadcast messages to all channels
🗑️ Delete broadcasted messages

Registration Methods:

Method 1 - Add Bot to Channel:
• Go to your channel info
• Add this bot as administrator

Method 2 - Forward Message:
• Forward any message from your channel to this bot

Commands:
/ban - Ban user from all registered channels
/unban - Unban user from all registered channels
/broadcast - Reply to a message to broadcast it
/del - Delete broadcasted messages
/list - List all registered channels
/stats - Show bot statistics

Note: Bot needs admin rights to access channel messages and member counts.
"""

    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup)

async def show_channel_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show channel list in button interface"""
    bot_instance = context.bot_data['bot_instance']
    channels = bot_instance.db.get_registered_channels()

    if not channels:
        message = "❌ No channels registered yet."
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)
        return

    import html
    message = "📋 Registered Channels:\n\n"

    for i, channel in enumerate(channels, 1):
        channel_id, name, username, reg_date, forward_count, last_activity, current_members = channel

        name_display = html.escape(name) if name else "Unknown"
        username_display = f"@{username}" if username else "No Username"

        # Handle date formatting
        if hasattr(reg_date, 'strftime'):
            reg_date_str = reg_date.strftime('%Y-%m-%d')
        else:
            reg_date_str = str(reg_date)[:10]

        message += f"{i}. {name_display}\n"
        message += f"   👥 Members: {current_members}\n"
        message += f"   📧 Username: {username_display}\n"
        message += f"   📅 Registered: {reg_date_str}\n\n"

        # Truncate if message is too long
        if len(message) > 4000:
            message = message[:4000] + "\n\n... (list truncated)"
            break

    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics in button interface"""
    try:
        bot_instance = context.bot_data['bot_instance']

        if not bot_instance.db.channels:
            message = "❌ Database not available. Please check MongoDB connection."
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            if update.callback_query:
                await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(message, reply_markup=reply_markup)
            return

        # Total registered channels
        total_channels = bot_instance.db.channels.count_documents({'is_active': True})

        # Total member count across all channels
        pipeline = [
            {'$match': {'is_active': True}},
            {'$group': {'_id': None, 'total_members': {'$sum': '$current_members'}}}
        ]

        result = list(bot_instance.db.channels.aggregate(pipeline))
        total_members = result[0]['total_members'] if result else 0

        from datetime import datetime
        stats_message = f"""
📊 Bot Statistics

🏢 Total Channels: {total_channels}
👥 Total Members: {total_members}
🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 Bot Status: ✅ Running
"""

        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(stats_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(stats_message, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Stats error: {e}")
        error_message = "❌ Error loading statistics."
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(error_message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(error_message, reply_markup=reply_markup)

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show registered channels with member counts only"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return

    await show_channel_list(update, context)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot statistics"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return

    await show_stats(update, context)

async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle forwarded messages with admin check"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return

    bot_instance = context.bot_data['bot_instance']
    await bot_instance.registration.handle_forwarded_message(update, context)

async def handle_bot_added_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle when bot is added to a channel"""
    bot_instance = context.bot_data['bot_instance']
    await bot_instance.registration.handle_bot_added_to_channel(update, context)

# Admin commands with admin check
async def admin_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban command with admin check"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return

    await ban_command(update, context)

async def admin_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban command with admin check"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return

    await unban_command(update, context)

async def admin_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast command with admin check"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return

    await broadcast_command(update, context)

async def admin_delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete command with admin check"""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return

    await delete_command(update, context)

def main():
    """Start the bot with improved error handling"""
    logger.info("🚀 Starting Telegram Channel Registration Bot...")

    # Start Flask server in a separate thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask server started")

    try:
        # Create application with proper configuration
        application = Application.builder().token(BOT_TOKEN).build()

        # Initialize bot instance and store in bot_data
        bot_instance = ChannelRegistrationBot()
        application.bot_data['bot_instance'] = bot_instance

        logger.info("✅ Bot instance created and configured")

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("list", list_channels))
        application.add_handler(CommandHandler("stats", stats))
        application.add_handler(CommandHandler("ban", admin_ban_command))
        application.add_handler(CommandHandler("unban", admin_unban_command))
        application.add_handler(CommandHandler("broadcast", admin_broadcast_command))
        application.add_handler(CommandHandler("del", admin_delete_command))

        # Button handler
        application.add_handler(CallbackQueryHandler(button_handler))

        # Chat member handler
        application.add_handler(ChatMemberHandler(handle_bot_added_to_channel, ChatMemberHandler.MY_CHAT_MEMBER))

        # Forward message handler
        application.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded_message))

        logger.info("✅ All handlers registered")

        # Start bot with polling
        logger.info("🤖 Bot is running! Press Ctrl+C to stop.")
        print("🤖 Bot is running!")

        # Run the bot
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,
            close_loop=False
        )

    except Exception as e:
        logger.error(f"❌ Critical error starting bot: {e}")
        raise
    finally:
        # Cleanup
        try:
            if 'application' in locals() and 'bot_instance' in application.bot_data:
                application.bot_data['bot_instance'].db.close()
                logger.info("✅ Database connection closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == '__main__':
    main()

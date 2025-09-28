# main.py - Main bot application for Render hosting
import logging
import os
import time
from typing import List
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    ChatMemberHandler, ContextTypes, CallbackQueryHandler
)
from mongodb_database import MongoDBDatabase
from register import ChannelRegistration
from ban import ban_command, unban_command, broadcast_command, delete_command

# Flask app for uptimerobot pinging
app = Flask(__name__)

@app.route('/')
def home() -> str:
    return "Bot is running!"

@app.route('/health')
def health() -> str:
    return "OK"

def run_flask() -> None:
    app.run(host='0.0.0.0', port=5000)

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Your Bot Token - Use environment variable for security
BOT_TOKEN = os.getenv('BOT_TOKEN', "")

# Admin user IDs - Replace with your admin IDs
ADMIN_IDS: List[int] = [123456789, 987654321]  # यहाँ अपने एडमिन IDs डालें

class ChannelRegistrationBot:
    def __init__(self) -> None:
        self.db = MongoDBDatabase()
        self.registration = ChannelRegistration(self.db)

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Help command with admin check"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return
    
    await show_how_to_use(update, context)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

async def show_how_to_use(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show how to use instructions"""
    help_text = (
        "📖 How to Use Guide\n\n"
        "What this bot does:\n"
        "✅ Automatically registers Telegram channels\n"
        "✅ Tracks channel member counts\n"
        "🔨 Ban users from all channels\n"
        "📢 Broadcast messages to all channels\n"
        "🗑️ Delete broadcasted messages\n\n"
        "Registration Methods:\n\n"
        "Method 1 - Add Bot to Channel:\n"
        "• Go to your channel info\n"
        "• Add this bot as administrator\n\n"
        "Method 2 - Forward Message:\n"
        "• Forward any message from your channel to this bot\n\n"
        "Commands:\n"
        "/ban <user_id> - Ban user from all registered channels\n"
        "/unban <user_id> - Unban user from all registered channels\n"
        "/broadcast - Reply to a message to broadcast it\n"
        "/del <broadcast_id> - Delete broadcasted messages\n"
        "/list - List all registered channels\n"
        "/stats - Show bot statistics\n\n"
        "Note: Bot needs admin rights to access channel messages and member counts."
    )
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup)

async def show_channel_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        
        if hasattr(reg_date, 'strftime'):
            reg_date_str = reg_date.strftime('%Y-%m-%d')
        else:
            reg_date_str = str(reg_date)[:10]
        
        message += f"{i}. {name_display}\n"
        message += f"   👥 Members: {current_members}\n"
        message += f"   📧 Username: {username_display}\n"
        message += f"   📅 Registered: {reg_date_str}\n\n"
    
    if len(message) > 4000:
        message = message[:4000] + "\n\n... (list truncated)"
    
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(message, reply_markup=reply_markup)

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        
        total_channels = bot_instance.db.channels.count_documents({'is_active': True})
        
        pipeline = [
            {'$match': {'is_active': True}},
            {'$group': {'_id': None, 'total_members': {'$sum': '$current_members'}}}
        ]
        result = list(bot_instance.db.channels.aggregate(pipeline))
        total_members = result[0]['total_members'] if result else 0
        
        from datetime import datetime
        stats_message = (
            f"📊 Bot Statistics\n\n"
            f"🏢 Total Channels: {total_channels}\n"
            f"👥 Total Members: {total_members}\n"
            f"🕒 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"🤖 Bot Status: ✅ Running"
        )
        
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

async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show registered channels with member counts only"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return
    
    await show_channel_list(update, context)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return
    
    await show_stats(update, context)

async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle forwarded messages with admin check"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return
    
    bot_instance = context.bot_data['bot_instance']
    await bot_instance.registration.handle_forwarded_message(update, context)

async def handle_bot_added_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle when bot is added to a channel"""
    bot_instance = context.bot_data['bot_instance']
    await bot_instance.registration.handle_bot_added_to_channel(update, context)

# Admin commands with admin check
async def admin_ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ban command with admin check"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return
    
    await ban_command(update, context)

async def admin_unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unban command with admin check"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return
    
    await unban_command(update, context)

async def admin_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast command with admin check"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return
    
    await broadcast_command(update, context)

async def admin_delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete command with admin check"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ आप इस बॉट का उपयोग नहीं कर सकते।")
        return
    
    await delete_command(update, context)

def main() -> None:
    """Start the bot"""
    max_retries = 3
    retry_delay = 5
    application = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🚀 Starting bot (attempt {attempt + 1}/{max_retries})...")
            
            # Start Flask server in a separate thread for uptimerobot
            flask_thread = Thread(target=run_flask)
            flask_thread.daemon = True
            flask_thread.start()
            logger.info("✅ Flask server started on port 5000")
            
            # Create application
            application = Application.builder().token(BOT_TOKEN).build()
            
            # Initialize bot instance and store in bot_data
            bot_instance = ChannelRegistrationBot()
            application.bot_data['bot_instance'] = bot_instance
            
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
            
            # Start bot
            logger.info("🤖 Bot is running! Press Ctrl+C to stop.")
            print("🤖 Bot is running! Press Ctrl+C to stop.")
            
            application.run_polling(
                allowed_updates=Update.ALL_TYPES, 
                drop_pending_updates=True
            )
            break
            
        except Exception as e:
            logger.error(f"❌ Startup error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("❌ Failed to start bot after all retries")
        finally:
            # Close database
            if application and 'bot_instance' in application.bot_data:
                application.bot_data['bot_instance'].db.close()

if __name__ == '__main__':
    main()

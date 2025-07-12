import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters

from persistence.db import Database
from bot.auth import check_admin

logger = logging.getLogger(__name__)

async def admin_command_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /admincommands command to list available admin commands in DM."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in DM
    if chat_id < 0: # Negative chat_id indicates a group chat
        await update.message.reply_text("This command can only be used in a private chat with the bot.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    # List of admin commands (add more as they are implemented)
    command_list = """
Available Admin Commands (in DM):
/admincommands - List available admin commands
/manage-this-group-queue [group_id] - View pending tasks for a specific group
# TODO: Add more admin DM commands here (e.g., broadcast, stats, user lookup)
"""
    await update.message.reply_text(command_list)


def setup_admin_dm_handlers(dispatcher, bot_instance):
    """Registers admin DM command handlers."""
    # Handler for command used in Admin DM
    dispatcher.add_handler(CommandHandler("admincommands", admin_command_list, filters=filters.ChatType.PRIVATE))

    logger.info("Registered admin DM handlers.")

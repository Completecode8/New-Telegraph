import logging
import json
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters

from persistence.db import Database
from bot.auth import check_admin

logger = logging.getLogger(__name__)

async def block_website(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /block-website command to block a domain in a group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in a group
    if chat_id > 0:
        await update.message.reply_text("This command can only be used in a group.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("Only admins can block websites.")
        return

    # Check if domain is provided
    if not context.args:
        await update.message.reply_text("Usage: /block-website [domain]")
        return

    domain_to_block = context.args[0].lower() # Block case-insensitively
    db: Database = context.application.user_data['db']

    try:
        # Add the domain to the blocked_domains table for this group
        await db.execute(
            "INSERT OR IGNORE INTO blocked_domains (group_id, domain) VALUES (?, ?)",
            (chat_id, domain_to_block)
        )

        logger.info(f"Admin {user.id} blocked domain '{domain_to_block}' in group {chat_id}")
        await update.message.reply_text(f"✅ Domain `{domain_to_block}` blocked in this group.")

    except Exception as e:
        logger.error(f"Error blocking domain '{domain_to_block}' in group {chat_id}: {e}")
        await update.message.reply_text(f"An error occurred while blocking the domain: {e}")


async def unblock_website(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /unblock-website command to unblock a domain in a group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in a group
    if chat_id > 0:
        await update.message.reply_text("This command can only be used in a group.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("Only admins can unblock websites.")
        return

    # Check if domain is provided
    if not context.args:
        await update.message.reply_text("Usage: /unblock-website [domain]")
        return

    domain_to_unblock = context.args[0].lower() # Unblock case-insensitively
    db: Database = context.application.user_data['db']

    try:
        # Delete the domain from the blocked_domains table for this group
        cursor = await db.execute(
            "DELETE FROM blocked_domains WHERE group_id = ? AND domain = ?",
            (chat_id, domain_to_unblock)
        )

        if cursor.rowcount > 0:
            logger.info(f"Admin {user.id} unblocked domain '{domain_to_unblock}' in group {chat_id}")
            await update.message.reply_text(f"✅ Domain `{domain_to_unblock}` unblocked in this group.")
        else:
            await update.message.reply_text(f"Domain `{domain_to_unblock}` was not found in the blocked list for this group.")

    except Exception as e:
        logger.error(f"Error unblocking domain '{domain_to_unblock}' in group {chat_id}: {e}")
        await update.message.reply_text(f"An error occurred while unblocking the domain: {e}")


def setup_content_management_handlers(dispatcher):
    """Registers content management (block/unblock) command handlers."""
    # Handlers for commands used in Groups
    dispatcher.add_handler(CommandHandler("block-website", block_website, filters=filters.ChatType.GROUPS))
    dispatcher.add_handler(CommandHandler("unblock-website", unblock_website, filters=filters.ChatType.GROUPS))

    logger.info("Registered content management handlers.")

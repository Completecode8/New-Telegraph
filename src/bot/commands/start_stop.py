import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters

from persistence.db import Database
from bot.auth import check_admin

logger = logging.getLogger(__name__)

async def bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /bot-start command to activate the bot in a group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in a group
    if chat_id > 0:
        await update.message.reply_text("This command can only be used in a group.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("Only admins can use this command.")
        return

    db: Database = context.application.user_data['db']

    try:
        # Check if the group is approved first
        group_status = await db.fetchone("SELECT is_approved FROM groups WHERE group_id = ?", (chat_id,))
        if not group_status or not group_status[0]:
            await update.message.reply_text("This group is not approved. Please ask an admin to approve it using /groupapprovae in my DM.")
            return

        # Set the group to active
        await db.execute(
            "UPDATE groups SET is_active = 1, is_paused = 0 WHERE group_id = ?",
            (chat_id,)
        )

        logger.info(f"Admin {user.id} started bot in group {chat_id}")
        await update.message.reply_text("✅ Bot is now active in this group.")
        # TODO: Display admin menu here

    except Exception as e:
        logger.error(f"Error starting bot in group {chat_id}: {e}")
        await update.message.reply_text(f"An error occurred while starting the bot: {e}")


async def stop_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /stop-bot command to deactivate the bot in a group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in a group
    if chat_id > 0:
        await update.message.reply_text("This command can only be used in a group.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("Only admins can use this command.")
        return

    db: Database = context.application.user_data['db']

    try:
        # Set the group to inactive
        await db.execute(
            "UPDATE groups SET is_active = 0 WHERE group_id = ?",
            (chat_id,)
        )

        logger.info(f"Admin {user.id} stopped bot in group {chat_id}")
        await update.message.reply_text("⏸️ Bot is now inactive in this group.")
        # TODO: Delete admin menu here

    except Exception as e:
        logger.error(f"Error stopping bot in group {chat_id}: {e}")
        await update.message.reply_text(f"An error occurred while stopping the bot: {e}")


async def unactivate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /unactivate command to pause the bot in a group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in a group
    if chat_id > 0:
        await update.message.reply_text("This command can only be used in a group.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("Only admins can use this command.")
        return

    db: Database = context.application.user_data['db']

    try:
        # Set the group to paused
        await db.execute(
            "UPDATE groups SET is_paused = 1 WHERE group_id = ?",
            (chat_id,)
        )

        logger.info(f"Admin {user.id} paused bot in group {chat_id}")
        await update.message.reply_text("😴 Bot is now paused in this group. It will ignore messages until /activate is used.")

    except Exception as e:
        logger.error(f"Error pausing bot in group {chat_id}: {e}")
        await update.message.reply_text(f"An error occurred while pausing the bot: {e}")


async def activate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /activate command to resume the bot in a group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in a group
    if chat_id > 0:
        await update.message.reply_text("This command can only be used in a group.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("Only admins can use this command.")
        return

    db: Database = context.application.user_data['db']

    try:
        # Set the group to not paused
        await db.execute(
            "UPDATE groups SET is_paused = 0 WHERE group_id = ?",
            (chat_id,)
        )

        logger.info(f"Admin {user.id} activated bot in group {chat_id}")
        await update.message.reply_text("🥳 Bot is now active again in this group.")

    except Exception as e:
        logger.error(f"Error activating bot in group {chat_id}: {e}")
        await update.message.reply_text(f"An error occurred while activating the bot: {e}")


def setup_start_stop_handlers(dispatcher):
    """Registers start/stop/activate/unactivate command handlers."""
    # Handlers for commands used in Groups
    dispatcher.add_handler(CommandHandler("bot-start", bot_start, filters=filters.ChatType.GROUPS))
    dispatcher.add_handler(CommandHandler("stop-bot", stop_bot, filters=filters.ChatType.GROUPS))
    dispatcher.add_handler(CommandHandler("unactivate", unactivate, filters=filters.ChatType.GROUPS))
    dispatcher.add_handler(CommandHandler("activate", activate, filters=filters.ChatType.GROUPS))

    logger.info("Registered start/stop/activate/unactivate handlers.")

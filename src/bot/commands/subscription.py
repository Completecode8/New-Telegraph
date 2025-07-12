import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters
from datetime import datetime

from persistence.db import Database
from bot.auth import check_admin

logger = logging.getLogger(__name__)

async def set_subscription_plan(update: Update, context: ContextTypes.DEFAULT_TYPE, plan: str) -> None:
    """Helper function to set the subscription plan for a group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in a group
    if chat_id > 0:
        await update.message.reply_text("Subscription commands can only be used in a group.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("Only admins can change the subscription plan.")
        return

    db: Database = context.application.user_data['db']

    try:
        # Check if the group is active
        group_status = await db.fetchone("SELECT is_active FROM groups WHERE group_id = ?", (chat_id,))
        if not group_status or not group_status[0]:
            await update.message.reply_text("The bot is not active in this group. Use /bot-start first.")
            return

        # Update the subscription plan in the database
        await db.execute(
            "INSERT OR REPLACE INTO subscriptions (group_id, plan, activated_at, last_updated) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
            (chat_id, plan)
        )
        # Also update the groups table for quick access to the current plan
        await db.execute(
            "UPDATE groups SET subscription_plan = ? WHERE group_id = ?",
            (plan, chat_id)
        )


        logger.info(f"Admin {user.id} set subscription plan to '{plan}' for group {chat_id}")
        await update.message.reply_text(f"✅ Subscription plan set to '{plan}' for this group.")

    except Exception as e:
        logger.error(f"Error setting subscription plan '{plan}' for group {chat_id}: {e}")
        await update.message.reply_text(f"An error occurred while setting the subscription plan: {e}")


async def default_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /defaultsubscription command."""
    await set_subscription_plan(update, context, 'default')

async def twelve_hour_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /12hsubscription command."""
    await set_subscription_plan(update, context, '12h')

async def free_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /freesubscription command."""
    await set_subscription_plan(update, context, 'free')

async def file_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /filesubscription command."""
    await set_subscription_plan(update, context, 'file')

async def one_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /1subscription command."""
    await set_subscription_plan(update, context, '1sub')


def setup_subscription_handlers(dispatcher):
    """Registers subscription command handlers."""
    # Handlers for commands used in Groups
    dispatcher.add_handler(CommandHandler("defaultsubscription", default_subscription, filters=filters.ChatType.GROUPS))
    dispatcher.add_handler(CommandHandler("12hsubscription", twelve_hour_subscription, filters=filters.ChatType.GROUPS))
    dispatcher.add_handler(CommandHandler("freesubscription", free_subscription, filters=filters.ChatType.GROUPS))
    dispatcher.add_handler(CommandHandler("filesubscription", file_subscription, filters=filters.ChatType.GROUPS))
    dispatcher.add_handler(CommandHandler("1subscription", one_subscription, filters=filters.ChatType.GROUPS))

    logger.info("Registered subscription handlers.")

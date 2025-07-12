import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters

from persistence.db import Database
from bot.auth import check_admin

logger = logging.getLogger(__name__)

async def reset_queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /reset-queue command to reset the task queue for a group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in a group
    if chat_id > 0:
        await update.message.reply_text("This command can only be used in a group.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("Only admins can reset the queue.")
        return

    db: Database = context.application.user_data['db']

    try:
        # Delete all pending tasks for this group
        cursor = await db.execute(
            "DELETE FROM tasks WHERE group_id = ? AND status IN ('pending', 'downloading', 'uploading', 'retrying')",
            (chat_id,)
        )

        logger.info(f"Admin {user.id} reset queue for group {chat_id}. Deleted {cursor.rowcount} tasks.")
        await update.message.reply_text(f"✅ Task queue reset for this group. {cursor.rowcount} pending tasks removed.")

    except Exception as e:
        logger.error(f"Error resetting queue for group {chat_id}: {e}")
        await update.message.reply_text(f"An error occurred while resetting the queue: {e}")


async def manage_this_group_queue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /manage-this-group-queue command to manage/monitor queue for a specific group (Admin DM)."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Command must be used in DM
    if chat_id < 0: # Negative chat_id indicates a group chat
        await update.message.reply_text("This command can only be used in a private chat with the bot.")
        return

    # Check if user is admin
    if not await check_admin(user.id, context):
        await update.message.reply_text("Only admins can use this command.")
        return

    # Check if group_id is provided
    if not context.args:
        await update.message.reply_text("Usage: /manage-this-group-queue [group_id]")
        return

    try:
        group_id_str = context.args[0]
        # Telegram group IDs are negative integers
        if not group_id_str.startswith('-100'):
             await update.message.reply_text(f"Invalid group ID format: {group_id_str}. Group IDs usually start with '-100'.")
             return

        group_id = int(group_id_str)
        db: Database = context.application.user_data['db']

        # Fetch pending tasks for the specified group
        tasks = await db.fetchall(
            "SELECT task_id, user_id, original_link, status, priority, created_at FROM tasks WHERE group_id = ? ORDER BY priority DESC, created_at ASC",
            (group_id,)
        )

        if not tasks:
            await update.message.reply_text(f"No pending or in-progress tasks found for group `{group_id}`.")
            return

        # Format and send the list of tasks
        task_list = []
        for task in tasks:
            task_id, user_id, link, status, priority, created_at = task
            priority_str = "Priority" if priority == 1 else "Normal"
            task_list.append(f"- Task `{task_id}` (User: `{user_id}`, Status: `{status}`, Priority: `{priority_str}`, Added: {created_at}): {link}")

        message_text = f"Pending requests for group `{group_id}`:\n" + "\n".join(task_list)
        await update.message.reply_text(message_text)

        # TODO: Add options for managing specific tasks (e.g., delete by task_id)

    except ValueError:
        await update.message.reply_text("Invalid group ID format. Please provide a valid integer ID.")
    except Exception as e:
        logger.error(f"Error managing queue for group {context.args[0]} (admin {user.id}): {e}")
        await update.message.reply_text(f"An error occurred while fetching the queue: {e}")


def setup_queue_management_handlers(dispatcher):
    """Registers queue management command handlers."""
    # Handler for command used in Groups
    dispatcher.add_handler(CommandHandler("reset-queue", reset_queue, filters=filters.ChatType.GROUPS))

    # Handler for command used in Admin DM
    dispatcher.add_handler(CommandHandler("manage-this-group-queue", manage_this_group_queue, filters=filters.ChatType.PRIVATE))

    logger.info("Registered queue management handlers.")

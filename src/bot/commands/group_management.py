import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters

from persistence.db import Database
from bot.auth import check_admin

logger = logging.getLogger(__name__)

async def group_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /groupapprovae command to approve a new group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # 1. Check if command is used in DM
    if chat_id > 0: # Positive chat_id indicates a private chat
        if not await check_admin(user.id, context):
            await update.message.reply_text("Only admins can use this command in a private chat.")
            return

        # 2. Check if group_id is provided
        if not context.args:
            await update.message.reply_text("Usage: /groupapprovae [group_id]")
            return

        try:
            group_id_str = context.args[0]
            # Telegram group IDs are negative integers
            if not group_id_str.startswith('-100'):
                 await update.message.reply_text(f"Invalid group ID format: {group_id_str}. Group IDs usually start with '-100'.")
                 return

            group_id = int(group_id_str)
            db: Database = context.application.user_data['db']

            # 3. Insert or update the group in the database
            await db.execute(
                "INSERT OR REPLACE INTO groups (group_id, is_approved, added_at) VALUES (?, 1, CURRENT_TIMESTAMP)",
                (group_id,)
            )

            logger.info(f"Admin {user.id} approved group {group_id}")
            await update.message.reply_text(f"Group `{group_id}` approved successfully.")

        except ValueError:
            await update.message.reply_text("Invalid group ID format. Please provide a valid integer ID.")
        except Exception as e:
            logger.error(f"Error approving group {context.args[0]}: {e}")
            await update.message.reply_text(f"An error occurred while approving the group: {e}")

    else:
        await update.message.reply_text("This command can only be used in a private chat with the bot.")


async def all_approved_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /allapprovaedgroup command to list all approved groups."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # 1. Check if command is used in DM
    if chat_id > 0:
        if not await check_admin(user.id, context):
            await update.message.reply_text("Only admins can use this command in a private chat.")
            return

        db: Database = context.application.user_data['db']

        try:
            # 2. Fetch all approved groups from the database
            groups = await db.fetchall("SELECT group_id FROM groups WHERE is_approved = 1")

            if not groups:
                await update.message.reply_text("No approved groups found.")
                return

            # 3. Format and send the list
            group_list = "\n".join([f"- `{group[0]}`" for group in groups])
            await update.message.reply_text(f"Approved groups:\n{group_list}")

        except Exception as e:
            logger.error(f"Error fetching approved groups for admin {user.id}: {e}")
            await update.message.reply_text(f"An error occurred while fetching approved groups: {e}")

    else:
        await update.message.reply_text("This command can only be used in a private chat with the bot.")


async def delete_approved_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /deletethisapprovaedgroup command to delete an approved group."""
    user = update.effective_user
    chat_id = update.effective_chat.id

    # 1. Check if command is used in DM
    if chat_id > 0:
        if not await check_admin(user.id, context):
            await update.message.reply_text("Only admins can use this command in a private chat.")
            return

        # 2. Check if group_id is provided
        if not context.args:
            await update.message.reply_text("Usage: /deletethisapprovaedgroup [group_id]")
            return

        try:
            group_id_str = context.args[0]
             # Telegram group IDs are negative integers
            if not group_id_str.startswith('-100'):
                 await update.message.reply_text(f"Invalid group ID format: {group_id_str}. Group IDs usually start with '-100'.")
                 return

            group_id = int(group_id_str)
            db: Database = context.application.user_data['db']

            # 3. Delete the group from the database
            cursor = await db.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))

            if cursor.rowcount > 0:
                logger.info(f"Admin {user.id} deleted approved group {group_id}")
                await update.message.reply_text(f"Group `{group_id}` removed from approved list.")
                # TODO: If the bot is currently in this group, make it leave?
                # This might require storing bot's current chats or relying on the next message check.
            else:
                await update.message.reply_text(f"Group `{group_id}` not found in the approved list.")

        except ValueError:
            await update.message.reply_text("Invalid group ID format. Please provide a valid integer ID.")
        except Exception as e:
            logger.error(f"Error deleting approved group {context.args[0]}: {e}")
            await update.message.reply_text(f"An error occurred while deleting the approved group: {e}")

    else:
        await update.message.reply_text("This command can only be used in a private chat with the bot.")


def setup_group_management_handlers(dispatcher, bot_instance):
    """Registers group management command handlers."""
    # Handlers for commands used in Admin DM
    dispatcher.add_handler(CommandHandler("groupapprovae", group_approve, filters=filters.ChatType.PRIVATE))
    dispatcher.add_handler(CommandHandler("allapprovaedgroup", all_approved_groups, filters=filters.ChatType.PRIVATE))
    dispatcher.add_handler(CommandHandler("deletethisapprovaedgroup", delete_approved_group, filters=filters.ChatType.PRIVATE))

    logger.info("Registered group management handlers.")

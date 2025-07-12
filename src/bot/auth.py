import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def check_admin(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Checks if a user ID is in the list of authorized admins.
    Admin IDs are loaded from config/admins.json by the main Bot class.
    """
    # Access the admin_ids set stored in the Bot instance
    # The Bot instance is usually available via context.application.bot_data or similar
    # For now, we'll assume it's directly accessible via context.bot_data['admin_ids']
    # In a more structured app, you might pass this explicitly or use context.application.user_data
    admin_ids = context.application.user_data.get('admin_ids', set())

    is_admin = user_id in admin_ids
    if not is_admin:
        logger.info(f"User {user_id} attempted admin action but is not an admin.")
    return is_admin

async def check_channel_membership(user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Checks if a user is a member of all required channels.
    Required channels are loaded from config/config.json.
    Caches results to avoid hitting Telegram API rate limits.
    """
    # TODO: Implement caching mechanism (e.g., using a dictionary in context.application.user_data)
    # TODO: Implement actual Telegram API calls using context.bot.get_chat_member

    required_channels = context.application.user_data.get('recommended_channels', [])
    bot = context.bot

    if not required_channels:
        logger.warning("No recommended channels configured. Skipping channel membership check.")
        return True # Assume user is allowed if no channels are required

    all_channels_joined = True
    for channel_link in required_channels:
        try:
            # Extract channel ID/username from link (e.g., @channelname or -100123456789)
            # This requires parsing the link format (t.me/channelname or https://t.me/joinchat/...)
            # For simplicity, let's assume channel_link is the username or ID string directly for now
            channel_id = channel_link.split('/')[-1] # Basic parsing, needs refinement

            # Check membership status
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)

            # Status can be 'member', 'administrator', 'creator', 'left', 'kicked'
            if member.status not in ['member', 'administrator', 'creator']:
                all_channels_joined = False
                logger.info(f"User {user_id} is not a member of channel {channel_id}. Status: {member.status}")
                break # No need to check other channels if one is missing

        except Exception as e:
            logger.error(f"Error checking channel membership for user {user_id} in channel {channel_link}: {e}")
            # Decide how to handle API errors - maybe assume true to not block users on errors?
            # Or assume false and notify admin? For now, let's log and assume false.
            all_channels_joined = False
            break # Stop checking on error

    if all_channels_joined:
        logger.info(f"User {user_id} is a member of all required channels.")
    else:
         logger.info(f"User {user_id} is NOT a member of all required channels.")

    return all_channels_joined

async def handle_new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles when the bot is added to a new group.
    Checks if the group is approved and leaves if not.
    """
    db = context.application.user_data['db'] # Access the Database instance
    bot_id = context.bot.id
    chat_id = update.effective_chat.id
    chat_name = update.effective_chat.title
    admin_ids = context.application.user_data.get('admin_ids', set())
    bot = context.bot

    for member in update.message.new_chat_members:
        if member.id == bot_id:
            logger.info(f"Bot added to new chat: {chat_name} ({chat_id})")

            # Check if the group is approved in the database
            try:
                result = await db.fetchone("SELECT is_approved FROM groups WHERE group_id = ?", (chat_id,))
                is_approved = result[0] if result else False

                if not is_approved:
                    logger.warning(f"Bot added to unauthorized group: {chat_name} ({chat_id}). Leaving.")
                    await bot.leave_chat(chat_id)

                    # Notify admins
                    admin_message = f"⚠️ Bot added to unauthorized group!\nGroup Name: {chat_name}\nGroup ID: `{chat_id}`\nAction: Bot auto-left.\nUse /groupapprovae `{chat_id}` in my DM to authorize."
                    for admin_id in admin_ids:
                        try:
                            await bot.send_message(chat_id=admin_id, text=admin_message)
                        except Exception as e:
                            logger.error(f"Failed to notify admin {admin_id} about unauthorized group {chat_id}: {e}")
                else:
                    logger.info(f"Bot added to authorized group: {chat_name} ({chat_id}). Staying.")
                    # TODO: Potentially initialize group state (subscription, active status) in DB if not exists
                    await db.execute("INSERT OR IGNORE INTO groups (group_id, is_approved) VALUES (?, 1)", (chat_id,))


            except Exception as e:
                logger.error(f"Error checking group approval for {chat_id}: {e}")
                # Decide how to handle DB errors here - maybe leave to be safe?
                # For now, log and stay, but this needs careful consideration.
                pass # Logged above

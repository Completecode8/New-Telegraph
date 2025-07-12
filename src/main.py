import asyncio
import logging
import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from urllib.parse import urlparse # Import urlparse

from persistence.db import Database
from bot.auth import check_admin, check_channel_membership, handle_new_chat_members
from bot.commands.admin_dm import setup_admin_dm_handlers
from bot.commands.group_management import setup_group_management_handlers
from bot.commands.subscription import setup_subscription_handlers
from bot.commands.queue_management import setup_queue_management_handlers
from bot.commands.start_stop import setup_start_stop_handlers
from bot.commands.content_management import setup_content_management_handlers
# from bot.commands.admin_dm import admin_command_list_handler # Example handler import
from worker.queue_consumer import start_worker_process # Assuming worker is a separate process

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

CONFIG_PATH = "config/config.json"
ADMINS_CONFIG_PATH = "config/admins.json"
DOMAINS_CONFIG_PATH = "config/domains.json"
DATABASE_PATH = "data/bot.db"

class Bot:
    def __init__(self):
        self.config = self.load_config()
        self.db = Database(DATABASE_PATH)
        self.admin_ids = self.load_admin_ids()
        self.domains_config = self.load_domains_config()
        self.application = None # Telegram Application instance

    def load_config(self):
        """Loads configuration from config.json."""
        if not os.path.exists(CONFIG_PATH):
            logger.error(f"Config file not found: {CONFIG_PATH}. Please copy config.example.json and fill it.")
            # Exit or raise error, depending on desired behavior
            raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    def load_admin_ids(self):
        """Loads admin IDs from admins.json."""
        if not os.path.exists(ADMINS_CONFIG_PATH):
             logger.warning(f"Admins config file not found: {ADMINS_CONFIG_PATH}. Using initial_admin_ids from config.json.")
             return set(self.config.get("initial_admin_ids", []))

        try:
            with open(ADMINS_CONFIG_PATH, 'r') as f:
                config = json.load(f)
            return set(config.get("admins", []))
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding admins.json: {e}")
            return set(self.config.get("initial_admin_ids", []))


    def load_domains_config(self):
        """Loads domains configuration from domains.json."""
        if not os.path.exists(DOMAINS_CONFIG_PATH):
            logger.error(f"Domains config file not found: {DOMAINS_CONFIG_PATH}. Please create it based on the plan.")
            raise FileNotFoundError(f"Domains config file not found: {DOMAINS_CONFIG_PATH}")
        with open(DOMAINS_CONFIG_PATH, 'r') as f:
            return json.load(f)

    async def post_init(self, application: Application):
        """Post initialization hook for the Application."""
        logger.info("Bot started successfully!")
        # await self.db.initialize() # Database initialization is handled by setup.py

        # Store necessary data in application.user_data for handlers
        application.user_data['db'] = self.db
        application.user_data['admin_ids'] = self.admin_ids
        application.user_data['recommended_channels'] = self.config.get("recommended_channels", [])
        application.user_data['domains_config'] = self.domains_config
        application.user_data['config'] = self.config # Store full config as well

        await start_worker_process(self.db, self.config, self.domains_config) # Start the worker

    async def start(self):
        """Starts the Telegram bot."""
        logger.info("Starting bot...")
        token = self.config.get("telegram_bot_token")
        if not token or token == "YOUR_TELEGRAM_BOT_TOKEN":
            logger.error("Telegram bot token not configured. Please update config/config.json")
            return

        self.application = Application.builder().token(token).post_init(self.post_init).build()
        dispatcher = self.application.dispatcher

        # --- Register Handlers ---
        # Basic handler for testing
        dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        dispatcher.add_handler(CommandHandler("start", self.start_command)) # Example start command

        # Register other command handlers (uncomment and implement as modules are created)
        setup_admin_dm_handlers(dispatcher, self)
        setup_group_management_handlers(dispatcher, self)
        setup_subscription_handlers(dispatcher)
        setup_queue_management_handlers(dispatcher)
        setup_start_stop_handlers(dispatcher)
        setup_content_management_handlers(dispatcher)

        # Register handler for new chat members (bot added to group)
        dispatcher.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_chat_members))


        # --- Start the Bot ---
        logger.info("Polling for updates...")
        await self.application.run_polling(poll_interval=3.0)

    async def start_command(self, update: Update, context):
        """Handles the /start command."""
        await update.message.reply_text("Hello! I am your AssetFetch Pro bot. Send me a link from a supported website.")

    async def handle_message(self, update: Update, context):
        """Handles incoming messages."""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        text = update.message.text

        logger.info(f"Received message from user {user_id} in chat {chat_id}: {text}")

        # Check if the message contains a URL
        try:
            parsed_url = urlparse(text)
            is_url = all([parsed_url.scheme, parsed_url.netloc]) # Check if scheme and netloc are present
        except ValueError:
            is_url = False

        if is_url:
            db: Database = context.application.user_data['db']
            original_link = text.strip() # Use the original text as the link

            try:
                # Add the task to the database queue
                await db.execute(
                    "INSERT INTO tasks (group_id, user_id, original_link, status, priority) VALUES (?, ?, ?, ?, ?)",
                    (chat_id, user_id, original_link, 'pending', 0) # Default priority to 0
                )
                logger.info(f"Added task for group {chat_id}, user {user_id}: {original_link}")
                await update.message.reply_text("✅ Link received and added to the processing queue.")

            except Exception as e:
                logger.error(f"Error adding task to queue for group {chat_id}, user {user_id}: {e}")
                await update.message.reply_text(f"An error occurred while adding your link to the queue: {e}")

        else:
             # Ignore non-link messages for now, or add other handlers
             pass # await update.message.reply_text("I only process links from supported websites.")


if __name__ == "__main__":
    # Ensure data directory exists before initializing DB
    os.makedirs("data", exist_ok=True)
    # Ensure config directory exists before loading config
    os.makedirs("config", exist_ok=True)
    # Ensure credentials directory exists
    os.makedirs("config/credentials", exist_ok=True)
    # Ensure downloads directory exists
    os.makedirs("downloads", exist_ok=True)
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    # Ensure backups directory exists
    os.makedirs("data/backups", exist_ok=True)


    # Run setup script if bot.db doesn't exist or needs re-initialization
    if not os.path.exists(DATABASE_PATH):
         print("Database not found. Running setup script...")
         import scripts.setup
         scripts.setup.initialize_database()
         scripts.setup.load_initial_admins()
         scripts.setup.create_initial_config_files() # Ensure configs exist if DB was missing

    bot = Bot()
    try:
        asyncio.run(bot.start())
    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)

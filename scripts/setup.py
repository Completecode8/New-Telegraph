import sqlite3
import json
import os

def initialize_database(db_path="data/bot.db", schema_path="src/persistence/schema.sql"):
    """Initializes the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        cursor.executescript(schema_sql)
        conn.commit()
        print(f"Database initialized at {db_path}")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

def load_initial_admins(db_path="data/bot.db", admins_config_path="config/admins.json"):
    """Loads initial admin IDs from config into the database."""
    if not os.path.exists(admins_config_path):
        print(f"Admin config file not found: {admins_config_path}")
        return

    try:
        with open(admins_config_path, 'r') as f:
            config = json.load(f)
        admin_ids = config.get("admins", [])

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM admins") # Clear existing admins
        for admin_id in admin_ids:
            cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (admin_id,))
        conn.commit()
        print(f"Loaded {len(admin_ids)} initial admins.")
    except (sqlite3.Error, json.JSONDecodeError) as e:
        print(f"Error loading initial admins: {e}")
    finally:
        if conn:
            conn.close()

def create_initial_config_files():
    """Creates example config files if they don't exist."""
    config_dir = "config"
    os.makedirs(config_dir, exist_ok=True)

    config_example_path = os.path.join(config_dir, "config.example.json")
    if not os.path.exists(config_example_path):
        with open(config_example_path, "w") as f:
            f.write("""{
  "telegram_bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
  "shrinkme_api_key": "YOUR_SHRINKME_API_KEY",
  "recommended_channels": [
    "https://t.me/Channel1",
    "https://t.me/Channel2",
    "https://t.me/Channel3"
  ],
  "initial_admin_ids": [
    123456789,
    987654321
  ],
  "chrome_profile_path": "C:\\\\Users\\\\<User>\\\\AppData\\\\Local\\\\Google\\\\Chrome\\\\User Data\\\\BotProfile",
  "download_directory": "C:\\\\BotDownloads",
  "google_drive_folder_id": "YOUR_GOOGLE_DRIVE_FOLDER_ID"
}""")
        print(f"Created example config file: {config_example_path}")

    domains_path = os.path.join(config_dir, "domains.json")
    if not os.path.exists(domains_path):
         with open(domains_path, "w") as f:
            f.write("""{
  "allowed_domains": [
    "freepik.com",
    "envatoelements.com",
    "vecteezy.com",
    "pngtree.com",
    "motionarray.com",
    "pikbest.com",
    "storyblocks.com",
    "iconscout.com"
  ],
  "rewrite_map": {
    "freepik.com": "freepik-download.com",
    "envatoelements.com": "envato-download.com",
    "vecteezy.com": "vecteezy-download.com",
    "pngtree.com": "pngtree-download.com",
    "motionarray.com": "motion-download.com",
    "pikbest.com": "pikbest-download.com",
    "storyblocks.com": "storyblocks-download.com",
    "iconscout.com": "iconscout-download.com"
  }
}""")
         print(f"Created domains config file: {domains_path}")

    admins_path = os.path.join(config_dir, "admins.json")
    if not os.path.exists(admins_path):
         with open(admins_path, "w") as f:
            f.write("""{
  "admins": [
    123456789,
    987654321
  ]
}""")
         print(f"Created admins config file: {admins_path}")

    credentials_dir = os.path.join(config_dir, "credentials")
    os.makedirs(credentials_dir, exist_ok=True)
    print(f"Ensure your Google Drive API credentials (gdrive1.json, gdrive2.json) are placed in {credentials_dir}")

def create_runtime_directories():
    """Creates directories needed at runtime."""
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/backups", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    print("Created runtime directories (data, data/backups, downloads, logs).")


if __name__ == "__main__":
    print("Running setup script...")
    create_runtime_directories()
    create_initial_config_files()
    initialize_database()
    load_initial_admins()
    print("Setup complete. Please review config files and place your Google Drive credentials.")

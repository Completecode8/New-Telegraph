# AssetFetch Pro Telegram Bot

This project is a professional, multi-group, subscription-based Telegram bot designed to automate file downloads from specific websites, upload them to Google Drive, and distribute download links to users. It features robust administrative controls, error handling, and resilience mechanisms.

## Project Structure

```
│
├── README.md                          # Quick-start & architecture recap
├── LICENSE                            # MIT / Proprietary
├── .gitignore                         # Ignore secrets, downloads, logs
├── requirements.txt                   # Exact pinned packages
├── runtime.txt                        # Python 3.11.x
│
├── docker-compose.yml                 # Optional container stack
├── Dockerfile                         # Multi-stage, Chrome baked in
├── scripts/                           # One-command helpers
│   ├── start_bot.bat                  # Windows auto-restart loop
│   ├── start_bot.sh                   # Linux / WSL
│   ├── setup.py                       # First-time config generator
│   └── backup_and_cleanup.py          # Cron-able 8 h backup + 48 h purge
│
├── config/                            # ** NEVER committed to Git **
│   ├── config.example.json            # Template only
│   ├── config.json                    # LIVE – tokens, channels, admins
│   ├── domains.json                   # 8-site → rewrite map
│   ├── chrome_profile/                # Persistent Chrome user-data-dir
│   │   └── Default/                   # Pre-logged cookies & extensions
│   ├── credentials/                   # Google Drive service-account JSONs
│   │   ├── gdrive1.json
│   │   └── gdrive2.json
│   └── admins.json                    # List of admin Telegram IDs
│
├── src/                               # Core application code
│   ├── init.py
│   ├── main.py                        # Entry point (asyncio + PTB)
│   ├── bot/                           # Telegram layer
│   │   ├── init.py
│   │   ├── dispatcher.py              # Handlers & filters
│   │   ├── auth.py                    # Channel check + group allow-list
│   │   ├── commands/                  # Every command in its own file
│   │   │   ├── start_stop.py
│   │   │   ├── subscription.py
│   │   │   ├── group_management.py
│   │   │   ├── queue_management.py
│   │   │   └── admin_dm.py
│   │   └── utils.py                   # General helpers (escape, log, etc.)
│   ├── worker/                        # File-processing sub-process
│   │   ├── init.py
│   │   ├── chrome_manager.py          # Selenium factory (3–4 tab limit)
│   │   ├── downloader.py              # Download + retry + checksum
│   │   ├── uploader.py                # Google Drive API 1/2 + storage check
│   │   ├── shrinker.py                # ShrinkMe.io wrapper
│   │   └── queue_consumer.py          # SQLite queue reader (priority first)
│   ├── persistence/                   # All DB models & migrations
│   │   ├── init.py
│   │   ├── schema.sql                 # CREATE TABLE statements
│   │   ├── db.py                      # Connection pool & migrations
│   │   └── models.py                  # ORM-like dataclasses
│   ├── services/                      # Cross-cutting services
│   │   ├── init.py
│   │   ├── logger.py                  # Structured JSON logs → logs/
│   │   ├── notifier.py                # Admin DM sender
│   │   ├── file_cleanup.py            # 12 h GDrive & local purge
│   │   └── network_watcher.py         # 1.1.1.1 ping loop
│   └── constants.py                   # Magic strings & numbers centralised
│
├── data/                              # Runtime state
│   ├── bot.db                         # SQLite (groups, tasks, users)
│   └── backups/                       # Timestamped .db & .json copies
│
├── downloads/                         # Temporary downloads
│   └── .gitkeep                       # Ensure folder exists
│
├── logs/                              # Rotating logs
│   ├── bot.log                        # Current
│   └── bot.log.YYYY-MM-DD             # Daily archives
│
└── tests/                             # PyTest suite
    ├── init.py
    ├── conftest.py                    # Fixtures (DB, mock bot, fake GDrive)
    ├── test_auth.py
    ├── test_worker.py
    └── integration/                   # End-to-end happy paths
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Completecode8/New-Telegraph.git
    cd New-Telegraph
    ```
2.  **Install Python 3.11.x:** Ensure you have the correct Python version installed.
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Chrome Profile:**
    *   Manually set up a Chrome profile at `config/chrome_profile/Default/`. Log in to the required websites and install necessary extensions.
5.  **Set up Google Drive API:**
    *   Obtain two sets of OAuth 2.0 credentials from Google Cloud Platform. Place the JSON files in `config/credentials/` as `gdrive1.json` and `gdrive2.json`.
6.  **Set up ShrinkMe.io API:**
    *   Obtain your API key from ShrinkMe.io.
7.  **Configure `config.json`:**
    *   Copy `config/config.example.json` to `config/config.json`.
    *   Fill in your Telegram Bot Token, ShrinkMe.io API key, recommended channel links/IDs, and initial admin Telegram IDs.
8.  **Configure `domains.json`:**
    *   Copy `config/domains.example.json` to `config/domains.json`.
    *   Verify the domain rewrite map for the 8 supported websites.
9.  **Initialize Database:**
    ```bash
    python scripts/setup.py
    ```
10. **Run the bot:**
    *   Using the Windows auto-restart script: `scripts\start_bot.bat`
    *   Using Docker (recommended): `docker-compose up --build`

## Usage

*   Add the bot to your desired Telegram groups.
*   Use the admin commands (listed below) in the bot's DM or authorized groups to manage groups, subscriptions, and the queue.
*   Normal users send supported links in approved groups after joining the required channels.

## Admin Commands

**Group Commands:**

*   `/bot-start`: Activate bot in group
*   `/stop-bot`: Deactivate bot in group
*   `/activate`: Resume processing in group
*   `/unactivate`: Pause processing in group
*   `/defaultsubscription`: Set default subscription
*   `/12hsubscription`: Set 12-hour subscription
*   `/freesubscription`: Set free subscription
*   `/filesubscription`: Set file subscription
*   `/1subscription`: Set 1subscription
*   `/block-website [domain]`: Block domain in group
*   `/unblock-website [domain]`: Unblock domain in group
*   `/reset-queue`: Reset task queue in group

**Admin DM Commands:**

*   `/groupapprovae [group_id]`: Approve new group
*   `/allapprovaedgroup`: List approved groups
*   `/deletethisapprovaedgroup [group_id]`: Delete approved group
*   `/manage-this-group-queue [group_id]`: Manage group queue
*   `/api-start-working`: Resume GDrive operations
*   `/bot-error-fixed`: Resume after critical errors
*   `/bot-All-commandlist`: Show all commands
*   `/bot_resume_task`: Resume interrupted tasks

## Error Handling and Resilience

*   Automatic retry logic for downloads and uploads.
*   Google Drive API switching and storage checks.
*   Network monitoring and auto-resume.
*   Auto-restart script for crash recovery.
*   Database persistence for task and state recovery.
*   Regular backups of critical data.

## Contributing

(Add contribution guidelines here)

## License

(Add license information here)

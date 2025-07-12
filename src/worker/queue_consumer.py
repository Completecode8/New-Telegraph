import asyncio
import logging
import json
from persistence.db import Database

logger = logging.getLogger(__name__)

async def process_task(db: Database, task: dict, domains_config: dict, config: dict) -> None:
    """Processes a single task from the queue."""
    task_id = task['task_id']
    group_id = task['group_id']
    user_id = task['user_id']
    original_link = task['original_link']
    priority = task['priority']

    logger.info(f"Processing task {task_id} for group {group_id}, user {user_id}: {original_link}")

    try:
        # 1. Parsing the original_link to identify the domain.
        from urllib.parse import urlparse
        parsed_url = urlparse(original_link)
        domain = parsed_url.netloc.lower()

        if not domain:
            await db.execute("UPDATE tasks SET status = 'failed', error_message = 'Invalid URL: No domain found' WHERE task_id = ?", (task_id,))
            logger.warning(f"Task {task_id} failed: Invalid URL (no domain) - {original_link}")
            return

        # 2. Checking if the domain is supported and not blocked for the group.
        allowed_domains = domains_config.get("allowed_domains", [])
        if domain not in allowed_domains:
            await db.execute("UPDATE tasks SET status = 'failed', error_message = f'Domain not supported: {domain}' WHERE task_id = ?", (task_id,))
            logger.warning(f"Task {task_id} failed: Domain '{domain}' not supported - {original_link}")
            return

        # Check if the domain is blocked for this group
        is_blocked = await db.fetchone("SELECT 1 FROM blocked_domains WHERE group_id = ? AND domain = ?", (group_id, domain))
        if is_blocked:
            await db.execute("UPDATE tasks SET status = 'failed', error_message = f'Domain blocked in this group: {domain}' WHERE task_id = ?", (task_id,))
            logger.warning(f"Task {task_id} failed: Domain '{domain}' blocked in group {group_id} - {original_link}")
            return

        logger.info(f"Domain '{domain}' is supported and not blocked for group {group_id}.")

        # 3. Using appropriate fetching logic based on the domain configuration.
        # Fetch the content of the link
        import requests
        from bs4 import BeautifulSoup

        try:
            response = requests.get(original_link, timeout=10) # Add a timeout
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            soup = BeautifulSoup(response.content, 'html.parser')

            # TODO: Implement domain-specific parsing and extraction logic here
            # Use domains_config to determine how to parse the page for the specific domain.
            # Example: Extract all image URLs
            # images = [img['src'] for img in soup.find_all('img', src=True)]
            # logger.info(f"Found {len(images)} images on {original_link}")

            # For now, just log the title and a snippet of the body
            title = soup.title.string if soup.title else "No title found"
            body_snippet = soup.body.get_text(separator=' ', strip=True)[:200] + "..." if soup.body else "No body found"
            logger.info(f"Fetched content for {original_link}: Title='{title}', Snippet='{body_snippet}'")

            # 4. Downloading assets. (TODO)
            # 5. Uploading assets to Telegram (or storing them). (TODO)
            # 6. Updating task status in the database (e.g., 'completed', 'failed').

            # Update task status to completed (placeholder)
            await db.execute("UPDATE tasks SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE task_id = ?", (task_id,))
            logger.info(f"Task {task_id} completed.")

        except requests.exceptions.RequestException as req_e:
            error_message = f"HTTP/Network error fetching {original_link}: {req_e}"
            logger.error(error_message, exc_info=True)
            await db.execute("UPDATE tasks SET status = 'failed', error_message = ? WHERE task_id = ?", (error_message, task_id,))
        except Exception as e:
            error_message = f"Error during content fetching/parsing for task {task_id}: {e}"
            logger.error(error_message, exc_info=True)
            # Update task status to failed
            await db.execute("UPDATE tasks SET status = 'failed', error_message = ? WHERE task_id = ?", (error_message, task_id,))

    except Exception as e:
        error_message = f"An unexpected error occurred during task processing for task {task_id}: {e}"
        logger.error(error_message, exc_info=True)
        # Update task status to failed
        await db.execute("UPDATE tasks SET status = 'failed', error_message = ? WHERE task_id = ?", (error_message, task_id,))


async def start_worker_process(db: Database, config: dict, domains_config: dict) -> None:
    """Starts the worker process to consume tasks from the queue."""
    logger.info("Worker process started.")

    while True:
        try:
            # Fetch the next pending task with highest priority
            # Statuses: 'pending', 'downloading', 'uploading', 'completed', 'failed', 'retrying'
            task = await db.fetchone(
                "SELECT task_id, group_id, user_id, original_link, status, priority FROM tasks WHERE status = 'pending' ORDER BY priority DESC, created_at ASC LIMIT 1"
            )

            if task:
                task_dict = {
                    'task_id': task[0],
                    'group_id': task[1],
                    'user_id': task[2],
                    'original_link': task[3],
                    'status': task[4],
                    'priority': task[5]
                }
                # Update status to downloading immediately
                await db.execute("UPDATE tasks SET status = 'downloading' WHERE task_id = ?", (task_dict['task_id'],))
                await process_task(db, task_dict, domains_config, config)
            else:
                # No pending tasks, wait before checking again
                await asyncio.sleep(10) # Poll every 10 seconds

        except asyncio.CancelledError:
            logger.info("Worker process cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in worker process loop: {e}", exc_info=True)
            await asyncio.sleep(10) # Wait before retrying after an error

# Example of how to run the worker (for testing purposes, actual run is in main.py)
# async def main():
#     db = Database("data/bot.db")
#     # Load config and domains_config here for testing
#     config = {} # Placeholder
#     domains_config = {} # Placeholder
#     await start_worker_process(db, config, domains_config)

# if __name__ == "__main__":
#     asyncio.run(main())

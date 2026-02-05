from typing import Optional
from api_client.gdrive_client import GDriveClient
from persistence.store import SQLiteStore
import logging

# Key used to store the last processed page token
CHECKPOINT_TOKEN = "drive_metadata_page_token"
logger = logging.getLogger(__name__)

class MetadataSyncEngine:
    def __init__(
        self,
        client: GDriveClient,
        store: SQLiteStore,
        page_size: int = 25,
    ):
        self.client = client
        self.store = store
        self.page_size = page_size

    # Performs resumable metadata sync operation.
    # Can restart at any time.
    def sync(self) -> None:
        # Load last page token
        page_token = self.store.get_checkpoint(CHECKPOINT_TOKEN)

        if page_token:
            logger.info(
                "Resuming metadata sync from last checkpoint token!",
            )
        else:
            logger.info("No checkpoint found, starting from beginning")

        pages_processed = 0
        files_processed = 0

        # Fetch files and next page from Drive
        while True:
            logger.debug("Fetching page (token length=%s)",
                         len(page_token) if page_token else "none")

            files, next_page_token = self.client.list_files(page_token=page_token)
            if files:
                # Save files to local storage
                self.store.insert_update_files(files)
                files_processed += len(files)
            else:
                logger.debug("No files returned for this page")

            # Persist checkpoint after writing successfully
            self.store.set_checkpoint(CHECKPOINT_TOKEN, next_page_token)

            logger.debug(
                "Checkpoint updated to token: %s",
                next_page_token[:10] if next_page_token else "END",
            )
            pages_processed += 1

            logger.info(
                "Processed page %d (files so far: %d)",
                pages_processed,
                files_processed,
            )

            # Stop iterating if pages run out
            if not next_page_token:
                break

            # Move on to next page
            page_token = next_page_token
        
        logger.info(
            "Metadata sync complete (pages=%d, files=%d)",
            pages_processed,
            files_processed,
        )

    # Clear sync checkpoint to force a full resync.
    def reset(self) -> None:
        logger.warning("Resetting metadata sync checkpoint")
        self.store.clear_checkpoint(CHECKPOINT_TOKEN)

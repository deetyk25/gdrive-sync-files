from typing import Optional
from api_client.gdrive_client import GDriveClient
from persistence.store import SQLiteStore

# Key used to store the last processed page token
CHECKPOINT_TOKEN = "drive_metadata_page_token"

class MetadataSyncEngine:
    def __init__(
        self,
        client: GDriveClient,
        store: SQLiteStore,
        page_size: int = 100,
    ):
        self.client = client
        self.store = store
        self.page_size = page_size

    # Performs resumable metadata sync operation.
    # Can restart at any time.
    def sync(self) -> None:
        # Load last page token
        page_token: Optional[str] = self.store.get_checkpoint(CHECKPOINT_TOKEN)

        # Fetch files and next page from Drive
        while True:
            files, next_page_token = self.client.list_files(page_token=page_token)
            if files:
                # Save files to local storage
                self.store.insert_update_files(files)

            # Persist checkpoint after writing successfully
            self.store.set_checkpoint(CHECKPOINT_TOKEN, next_page_token)

            # Stop iterating if pages run out
            if not next_page_token:
                break

            # Move on to next page
            page_token = next_page_token

    # Clear sync checkpoint to force a full resync.
    def reset(self) -> None:
        self.store.clear_checkpoint(CHECKPOINT_TOKEN)

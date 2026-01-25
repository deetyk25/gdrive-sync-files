import tempfile
from persistence.store import SQLiteStore
from sync_engine.metadata_sync import MetadataSyncEngine

# A fake Google Drive client used for testing
class FakeGDriveClient:
    # Helps test resumable sync behavior
    # Simulates API client
    def __init__(self, pages, fail_after_pages=None):
        self.pages = pages
        self.fail_after_pages = fail_after_pages
        # Tracks number of calls
        self.calls = 0

    # Simulates listing all files from Drive
    def list_files(self, page_size=100, page_token=None):
        # Simulates failure if fail_after_pages is reached
        if self.fail_after_pages is not None and self.calls >= self.fail_after_pages:
            raise RuntimeError("Simulated crash")

        # Checks which page token to return
        index = int(page_token) if page_token else 0
        self.calls += 1

        files = self.pages[index]
        # Gets next page token or returns None if there are no more pages
        next_token = str(index + 1) if index + 1 < len(self.pages) else None

        return files, next_token

# Tests syncing same file many times 
# Should not create duplicates
def test_metadata_sync_is_idempotent(tmp_path):
    store = SQLiteStore(db_path=tmp_path / "test.db")

    # Gets single file to sync
    files = [
        {"id": "1", "name": "A", "mimeType": "text/plain", "modifiedTime": "t1"}
    ]


    # Defines simple dummy client that returns the same file
    class SimpleClient:
        def list_files(self, page_size=100, page_token=None):
            return files, None
    client = SimpleClient()

    engine = MetadataSyncEngine(client, store)

    # Syncs twice and checks for duplicate creation
    engine.sync()
    engine.sync()
    assert store.get_file_count() == 1

# Tests that MetadataSync can resume syncing after a programmed failure
def test_metadata_sync_resumes_after_failure(tmp_path):
    store = SQLiteStore(db_path=tmp_path / "test.db")

    # Defines two file pages
    page1 = (
        [{"id": "1", "name": "A", "mimeType": "text/plain", "modifiedTime": "t1"}],
        "token-1"
    )
    page2 = (
        [{"id": "2", "name": "B", "mimeType": "text/plain", "modifiedTime": "t2"}],
        None
    )

    # Defines error client that calls exception to the first call and simulates a crash
    class ErrorClient(FakeGDriveClient):
        def list_files(self, *args, **kwargs):
            if self.calls == 1:
                raise RuntimeError("Simulated crash")
            return super().list_files(*args, **kwargs)

    client = ErrorClient([page1, page2])
    engine = MetadataSyncEngine(client, store)

    # Tries fetching page1 
    try:
        engine.sync()
    except RuntimeError:
        pass

    assert store.get_file_count() == 1

    # Tries fetching from page 1
    engine.sync()
    assert store.get_file_count() == 2
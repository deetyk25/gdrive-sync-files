# gdrive-sync-files

This is a synchronization service that uses Google Drive file metadata with a local SQLite store. It includes a job system that handles system failures and has resumable and idempotent sync operations. This uses persistent local storage for files, sync checkpoints, and job states and a job runner that handles retries and failures. Also includes unit tests to ensure method correctness.

**Architecture**
![IMG_8754](https://github.com/user-attachments/assets/588fbe4c-9eca-4fc7-b0ee-0e9dcf2a6642)
- GDriveClient: Client abstraction over Google Drive API supporting sequential page access and error handling.
- MetadataSyncEngine: Resumable sync functionality with checkpoints and idempotency.
- SQLiteStore: Handles long-term data storage and stores file metadata, sync progress, and job state.
- JobRunner: Executes job updates and handles retries.

How to run tests from the root directory: PYTHONPATH=. pytest tests/ -v

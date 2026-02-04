# gdrive-sync-files

**Description:**  
This is a synchronization service that uses Google Drive file metadata with a local SQLite store. It includes a job system that handles system failures and has resumable and idempotent sync operations. This uses persistent local storage for files, sync checkpoints, and job states and a job runner that handles retries and failures. Also includes unit tests to ensure method correctness.

**Architecture:**  
![IMG_8754](https://github.com/user-attachments/assets/588fbe4c-9eca-4fc7-b0ee-0e9dcf2a6642)
- GDriveClient: Client abstraction over Google Drive API supporting sequential page access and error handling.
- MetadataSyncEngine: Resumable sync functionality with checkpoints and idempotency.
- SQLiteStore: Handles long-term data storage and stores file metadata, sync progress, and job state.
- JobRunner: Executes job updates and handles retries.

**Running Tests:**  
From the root directory: PYTHONPATH=. pytest tests/ -v

**How to run a job:**  
python -m sync_engine.cli initiate --> makes a new job  
python -m sync_engine.cli status --> returns the status of the last 25 jobs  
python -m sync_engine.cli reset --> resets failed or dead jobs to pending   

# gdrive-sync-files

**Description:**  
This is a synchronization service that uses Google Drive file metadata with a local SQLite store. It includes a job system that handles system failures and has resumable and idempotent sync operations. This uses persistent local storage for files, sync checkpoints, and job states and a job runner that handles retries and failures. Also includes unit tests to ensure method correctness.

**Architecture:**  
![IMG_8754](https://github.com/user-attachments/assets/588fbe4c-9eca-4fc7-b0ee-0e9dcf2a6642)
- GDriveClient: Client abstraction over Google Drive API supporting sequential page access and error handling.
- MetadataSyncEngine: Resumable sync functionality with checkpoints and idempotency.
- SQLiteStore: Handles long-term data storage and stores file metadata, sync progress, and job state.
- JobRunner/Cli:
  - JobRunner: Executes job updates and handles retries.
  - Cli: Allows for client interactions with the job running system

**Dependencies:**  
Run from root directory:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

**Running Tests:**  
From the root directory: PYTHONPATH=. pytest tests/ -v

**How to run a job (CLI commands):**  
python -m sync_engine.cli initiate --> makes a new job  
python -m sync_engine.cli status --> returns the status of the last 25 jobs  
python -m sync_engine.cli reset --> resets failed or dead jobs to pending
python -m sync_engine.cli delete --> deletes pending or failed jobs

**Reliability Strategy:**

This application is meant to handle failures and restarts through the following strategies:  
- Checkpoints are persisted with each successful page write  
- File metadata is safe to re-run without creating duplicates  
- Jobs that are stuck as RUNNING are automatically restarted and recovered  
- Each job has a maximum retry count  
- All job progress and sync updates are stored with SQLite  
- Any manual termination or crash results in the job resuming from the last saved checkpoint  

**Acknowledged Limitations and Future Improvements:**  
- Only analyzes metadata, not file contents
- Does not support parallelism yet (i.e. no multiple jobs running concurrently)
- Not tested with very large data sets
- Job cancellation is limited

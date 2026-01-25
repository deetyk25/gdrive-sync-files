# gdrive-sync-files

This is a synchronization service that uses Google Drive file metadata with a local SQLite store. It includes a job system that handles system failures and has resumable and idempotent sync operations. This uses persistent local storage for files, sync checkpoints, and job states and a job runner that handles retries and failures. Also includes unit tests to ensure method correctness.

How to run tests from the root directory: PYTHONPATH=. pytest tests/ -v
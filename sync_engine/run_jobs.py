import time
from persistence.store import SQLiteStore
from sync_engine.metadata_sync import MetadataSyncEngine
from api_client.gdrive_client import GDriveClient

class JobRunner:
    # Polls job queue, executes job requests, retries, and updates

    # Initializes JobRunner
    def __init__(self, store: SQLiteStore, poll_interval: int = 2):
        self.store = store
        self.poll_interval = poll_interval
        # Initializes a client and runs metadata sync
        client = GDriveClient()
        sync = MetadataSyncEngine(client, self.store)
        sync.sync()

    # Loops to fetch and execute all pending jobs
    # Handles status updates, retries, and failure logs
    def run(self):
        while True:
            # Fetch up to 5 jobs
            jobs = self.store.fetch_pending_jobs(limit=5)

            # No pending jobs, begin sleep for poll_interval
            if not jobs:
                print("No pending jobs. On pause now.")
                time.sleep(self.poll_interval)
                continue

            # Goes through each pending job
            for job in jobs:
                job_id = job["id"]
                attempts = job["attempts"]
                max_attempts = job["max_attempts"]

                try:
                    # Marks job as RUNNING
                    # Increases attempts
                    self.store.update_job(job_id, "RUNNING", attempts + 1)
                    # Executes job type
                    # Not integrated client yet
                    if job["type"] == "metadata_sync":
                        sync = MetadataSyncEngine(self.store)
                        sync.sync()
                    else:
                        # Flags error if job type isn't known
                        raise ValueError(f"Error: Unknown job type {job['type']}")

                    # Marks job as done if successfully done
                    self.store.update_job(job_id, "DONE", attempts + 1)
                    print(f"Job {job_id} is done.")

                except Exception as e:
                    # Handles errors during job execution
                    print(f"Job {job_id} failed: {e}")

                    # Mark job as dead if max attempts are reached
                    if attempts + 1 >= max_attempts:
                        self.store.update_job(job_id, "DEAD", attempts + 1, str(e))
                        print(f"Job {job_id} marked as DEAD.")
                    # Marks job as failed and to be retried later
                    else:
                        self.store.update_job(job_id, "FAILED", attempts + 1, str(e))
                        print(f"Job {job_id} failed, will retry it later.")

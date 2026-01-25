import logging
import time
from persistence.store import SQLiteStore
from sync_engine.metadata_sync import MetadataSyncEngine
from api_client.gdrive_client import GDriveClient

logger = logging.getLogger(__name__)

class JobRunner:
    # Polls job queue, executes job requests, retries, and updates

    # Initializes JobRunner
    def __init__(self, store: SQLiteStore, poll_interval: int = 2):
        self.store = store
        self.poll_interval = poll_interval
        
    # Loops to fetch and execute all pending jobs
    # Handles status updates, retries, and failure logs
    def run(self):
        # Initializes a client and runs metadata sync
        client = GDriveClient()

        while True:
            # Fetch up to 5 jobs
            jobs = self.store.fetch_pending_jobs(limit=5)

            # No pending jobs, begin sleep for poll_interval
            if not jobs:
                logger.info("No pending jobs. Sleeping now.")
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
                        sync = MetadataSyncEngine(client, self.store)
                        sync.sync()
                    else:
                        # Flags error if job type isn't known
                        raise ValueError(f"Error: Unknown job type {job['type']}")

                    # Marks job as done if successfully done
                    self.store.update_job(job_id, "DONE", attempts + 1)
                    logger.info("Completed Job: %s", job_id)

                except Exception as e:
                    # Handles errors during job execution
                    logger.error("Failed job: %s", job_id, exc_info=True)

                    # Mark job as dead if max attempts are reached
                    if attempts + 1 >= max_attempts:
                        self.store.update_job(job_id, "DEAD", attempts + 1, str(e))
                        logger.error("Job %s is now DEAD", job_id)
                    # Marks job as failed and to be retried later
                    else:
                        self.store.update_job(job_id, "FAILED", attempts + 1, str(e))
                        logger.warning("Job %s FAILED, will retry", job_id)

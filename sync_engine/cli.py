import logging
import argparse
from persistence.store import SQLiteStore
from sync_engine.run_jobs import JobRunner

logger = logging.getLogger(__name__)

def main():
    # Sets up logger.info for application entry
    logging.basicConfig(level=logging.INFO)

    # Sets up argument parser
    parser = argparse.ArgumentParser()
    # Sets up job types
    # Initiate creates and runs a job
    # Status allows viewing in-progress jobs
    # Retry allows resetting failded jobs to pending
    parser.add_argument("command", choices=["initiate", "status", "retry"])
    # Defines job type as an arg to accept initiate, status, and retry
    parser.add_argument("--job-type", default="metadata_sync")
    parsed_args = parser.parse_args()

    # Connects to SQLite store class
    store = SQLiteStore()

    # Initiates new job
    if parsed_args.command == "initiate":
        # Creates new job record
        # Starts job runner and executes
        job_id = store.create_job(parsed_args.job_type)
        print(f"Created job: {job_id}. Initiating runner now!")
        logger.info("Starting runner for job %s", job_id)
        JobRunner(store).run()

    # Checks status of jobs
    elif parsed_args.command == "status":
        # Fetches 25 jobs in progress
        jobs = store.fetch_pending_jobs(limit=25)
        print("Jobs in progress: ")
        # Prints each in progress job
        for job in jobs:
            print(job)

    # Retrying failed jobs
    elif parsed_args.command == "retry":
        # Marks retried/failed jobs as pending
        # Resets all jobs with FAILED as pending
        # Resets counter as 0
        with store._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status='PENDING', attempts=0 WHERE status IN ('FAILED', 'DEAD')"
            )
        print("All failed/dead jobs reset to PENDING.")
        logger.info("Resets failed and dead jobs")

if __name__ == "__main__":
    main()

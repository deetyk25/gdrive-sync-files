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
    # Delete allows deletion of pending or running jobs
    parser.add_argument("command", choices=["initiate", "status", "retry", "delete"])
    # Defines job type as an arg to accept initiate, status, and retry
    parser.add_argument("--job-type", default="metadata_sync")
    parsed_args = parser.parse_args()

    # Connects to SQLite store class
    store = SQLiteStore()

    # Initiates new job
    if parsed_args.command == "initiate":
        # Creates new job record
        # Starts job runner and executes
        
        with store._conn() as conn:
            existing = conn.execute(
                """
                SELECT 1 FROM jobs
                WHERE type = ? AND status IN ('PENDING', 'RUNNING')
                """,
                (parsed_args.job_type,),
            ).fetchone()

        if existing:
            print("A metadata_sync job is already active and pending/running. Use status to inspect it.")
            print("Starting worker...")
            JobRunner(store).run()
            return

        job_id = store.create_job(parsed_args.job_type)
        print(f"Created job: {job_id}. Initiating runner now!")
        JobRunner(store).run()

    # Checks status of jobs
    elif parsed_args.command == "status":
        # Fetches 25 jobs in progress
        with store._conn() as conn:
            jobs = conn.execute(
                """
                SELECT id, type, status, attempts, max_attempts
                FROM jobs
                ORDER BY created_at DESC
                LIMIT 25
                """
            ).fetchall()

        if not jobs:
            print("No jobs found.")
            return

        for job in jobs:
            print(
                f"Job {job['id']} | "
                f"type={job['type']} | "
                f"status={job['status']} | "
                f"attempts={job['attempts']}/{job['max_attempts']}"
            )

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

    # Deletes running or pending jobs
    elif parsed_args.command == "delete":
        with store._conn() as conn:
            deleted = conn.execute(
                "DELETE FROM jobs WHERE type=? AND status IN ('PENDING','RUNNING')",
                (parsed_args.job_type,)
            ).rowcount
        print(f"Deleted {deleted} pending and running job(s).")
        logger.info("Deleted pending and running jobs")


if __name__ == "__main__":
    main()

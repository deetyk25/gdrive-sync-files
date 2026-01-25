import argparse
from persistence.store import SQLiteStore
from sync_engine.run_jobs import JobRunner

def main():
    # sets up argument parser
    parser = argparse.ArgumentParser()
    # sets up job types
    # initiate creates and runs a job
    # status allows viewing in-progress jobs
    # retry allows resetting failded jobs to pending
    parser.add_argument("command", choices=["initiate", "status", "retry"])
    parsed_args = parser.parse_args()

    # connects to SQLite store class
    store = SQLiteStore()

    # initiates new job
    if parsed_args.command == "initiate":
        # creates new job record
        # starts job runner and executes
        job_id = store.create_job(parsed_args.job_type)
        print(f"Created job {job_id}. Initiating runner now!")
        runner = JobRunner(store)
        runner.run()

    # checks status of jobs
    elif parsed_args.command == "status":
        # fetches 25 jobs in progress
        jobs = store.fetch_pending_jobs(limit=25)
        print("Jobs in progress: ")
        # prints each in progress job
        for job in jobs:
            print(job)

    # retrying failed jobs
    elif parsed_args.command == "retry":
        # marks retried/failed jobs as pending
        # resets all jobs with FAILED as pending
        # resets counter as 0
        with store._conn() as conn:
            conn.execute(
                "UPDATE jobs SET status='PENDING', attempts=0 WHERE status IN ('FAILED', 'DEAD')"
            )
        print("All failed/dead jobs reset to PENDING.")

if __name__ == "__main__":
    main()

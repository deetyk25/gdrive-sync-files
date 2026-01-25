from persistence.store import SQLiteStore
from sync_engine.run_jobs import JobRunner

# Tests entire life cycle of job within SQLiteStore from creation to completion
def test_job_lifecycle(tmp_path):
    sql_store = SQLiteStore(db_path=tmp_path / "test.db")

    # Creates new job with type
    curr_job_id = sql_store.create_job("metadata_sync")

    # Fetches pending jobs and checks if new job is in
    # Should be just one job that is pending
    curr_jobs = sql_store.fetch_pending_jobs(limit=10)
    assert len(curr_jobs) == 1
    assert curr_jobs[0]["status"] == "PENDING"

    # Updates the job's status to RUNNING with one attempt
    sql_store.update_job(curr_job_id, "RUNNING", attempts=1)
    # Updates the job's status to DONE with one attempt
    sql_store.update_job(curr_job_id, "DONE", attempts=1)

    # Fetches pending jobs to check that status was updated successfully
    curr_jobs = sql_store.fetch_pending_jobs(limit=10)
    assert curr_jobs == []

# Tests successful recovery of running jobs 
def test_runner_recovers_running_jobs(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")

    job_id = store.create_job("metadata_sync")
    store.update_job(job_id, "RUNNING", attempts=1)

    # Ensures job status is changed after recovery
    runner = JobRunner(store)
    recovered = runner.recover_stuck_jobs()
    assert recovered == 1

# Tests job creation and fetching of all pending jobs
def test_create_job_and_fetch_pending(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    # Creates job with maximum attempts of 2
    job_id = store.create_job("metadata_sync", max_attempts=2)

    # Fetch all pending jobs and validates fields
    pending_jobs = store.fetch_pending_jobs(limit=10)
    assert len(pending_jobs) == 1
    assert pending_jobs[0]["id"] == job_id
    assert pending_jobs[0]["status"] == "PENDING"
    assert pending_jobs[0]["attempts"] == 0
    assert pending_jobs[0]["max_attempts"] == 2

# Tests successful updating of a job status, attempts, and error
def test_update_job_status_and_attempts(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    job_id = store.create_job("metadata_sync")
    
    # Update job status to RUNNING, sets attempts to one, and records error
    store.update_job(job_id, "RUNNING", attempts=1, last_error="first_err")

    # Verify updates in the database
    with store._conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        assert row["status"] == "RUNNING"
        assert row["attempts"] == 1
        assert row["last_error"] == "first_err"

# Tests that maximum attempts are met
def test_fetch_pending_jobs_respects_attempts(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    first_id = store.create_job("metadata_sync", max_attempts=1)
    second_id = store.create_job("metadata_sync", max_attempts=2)

    # Mark first job as failed with max attempts reached
    store.update_job(first_id, "FAILED", attempts=1)
    
    # Retrieves pending jobs and returns second job
    pending_jobs = store.fetch_pending_jobs(limit=10)
    # Only job2 should be returned
    assert len(pending_jobs) == 1
    assert pending_jobs[0]["id"] == second_id

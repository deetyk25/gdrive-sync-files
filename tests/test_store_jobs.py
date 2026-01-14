from persistence.store import SQLiteStore

def test_job_lifecycle(tmp_path):
    # Tests entire life cycle of job within SQLiteStore from creation to completion
    # Defines new SQLiteStore with temporary database
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
    # Asserts that pending jobs should be 0
    curr_jobs = sql_store.fetch_pending_jobs(limit=10)
    assert curr_jobs == []

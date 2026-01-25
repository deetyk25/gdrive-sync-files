from persistence.store import SQLiteStore

# Tests that checkpoint is set and cleared correctly
def test_clear_checkpoint(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    store.set_checkpoint("tester_key", "tester_value")
    assert store.get_checkpoint("tester_key") == "tester_value"
    store.clear_checkpoint("tester_key")
    assert store.get_checkpoint("tester_key") is None

# Tests that checkpoint is set and retrieved correctly
def test_set_and_get_checkpoint(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    store.set_checkpoint("first_key", "first_val")
    assert store.get_checkpoint("first_key") == "first_val"

# Tests that checkpoint is set and overwritten correctly
def test_set_checkpoint_overwrite(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    store.set_checkpoint("key", "first_val")
    store.set_checkpoint("key", "second_val")
    assert store.get_checkpoint("key") == "second_val"

# Tests that file is inserted and updated successfully
def test_insert_update_file_overwrite(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    file = {"id": "1", "name": "A", "mimeType": "text/plain", "modifiedTime": "t1"}
    store.insert_update_files([file])

    # Update file name and modified time
    file_updated = {"id": "1", "name": "B", "mimeType": "text/plain", "modifiedTime": "t2"}
    store.insert_update_files([file_updated])

    # Verify successful update
    with store._conn() as conn:
        row = conn.execute("SELECT * FROM files WHERE id='1'").fetchone()
        assert row["name"] == "B"
        assert row["modified_time"] == "t2"
        assert store.get_file_count() == 1  # Count should not increase

# Test get_file_count starts at 0 with no files inserted 
def test_get_file_count_empty(tmp_path):
    store = SQLiteStore(tmp_path / "test.db")
    assert store.get_file_count() == 0

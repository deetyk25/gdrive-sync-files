from api_client.gdrive_client import GDriveClient

def test_list_files():
    client = GDriveClient()
    files, token = client.list_files(page_size=5)
    assert isinstance(files, list)

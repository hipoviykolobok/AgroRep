def test_export_observations_creates_export_record(client, create_version, valid_csv_bytes):
    created = create_version()
    version_id = created["version"]["version_id"]
    upload_response = client.post(
        f"/versions/{version_id}/files",
        files={"file": ("valid.csv", valid_csv_bytes, "text/csv")},
        data={"uploaded_by": str(created["user_id"])},
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["file"]["file_id"]

    import_response = client.post(f"/files/{file_id}/import-observations")
    assert import_response.status_code == 200
    assert import_response.json()["imported_count"] == 1

    export_response = client.get(
        f"/versions/{version_id}/export-observations",
        params={"user_id": created["user_id"]},
    )
    assert export_response.status_code == 200

    exports_response = client.get("/exports")
    assert exports_response.status_code == 200
    exports = exports_response.json()
    assert any(item["version_id"] == version_id and item["export_scope"] == "observations" for item in exports)

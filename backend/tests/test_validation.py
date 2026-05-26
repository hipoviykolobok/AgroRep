def test_valid_csv_passes_validation(client, create_version, valid_csv_bytes):
    created = create_version()
    version_id = created["version"]["version_id"]
    response = client.post(
        f"/versions/{version_id}/files",
        files={"file": ("valid.csv", valid_csv_bytes, "text/csv")},
        data={"uploaded_by": str(created["user_id"])},
    )

    assert response.status_code == 201
    validation = response.json()["validation"]
    assert validation["status"] == "success"
    assert validation["errors_count"] == 0


def test_missing_required_column_fails_and_records_error(client, create_version):
    created = create_version()
    version_id = created["version"]["version_id"]
    invalid_csv = (
        "region,agro_object,unit,period_year,value\n"
        "Краснодарский край,пшеница,ц/га,2024,56.2\n"
    ).encode("utf-8")

    response = client.post(
        f"/versions/{version_id}/files",
        files={"file": ("invalid.csv", invalid_csv, "text/csv")},
        data={"uploaded_by": str(created["user_id"])},
    )

    assert response.status_code == 201
    validation = response.json()["validation"]
    assert validation["status"] == "failed"
    assert validation["errors_count"] >= 1
    assert any(error["error_type"] == "missing_column" for error in validation["errors"])


def test_duplicate_file_upload_warns_and_import_replaces_observations(client, create_version, valid_csv_bytes):
    created = create_version()
    version_id = created["version"]["version_id"]

    first_upload = client.post(
        f"/versions/{version_id}/files",
        files={"file": ("valid.csv", valid_csv_bytes, "text/csv")},
        data={"uploaded_by": str(created["user_id"])},
    )
    assert first_upload.status_code == 201
    first_file_id = first_upload.json()["file"]["file_id"]
    assert first_upload.json()["duplicate_file_ids"] == []

    second_upload = client.post(
        f"/versions/{version_id}/files",
        files={"file": ("valid.csv", valid_csv_bytes, "text/csv")},
        data={"uploaded_by": str(created["user_id"])},
    )
    assert second_upload.status_code == 201
    second_payload = second_upload.json()
    second_file_id = second_payload["file"]["file_id"]
    assert second_payload["duplicate_file_ids"] == [first_file_id]
    assert second_payload["duplicate_message"]

    detail_response = client.get(f"/datasets/{created['dataset']['dataset_id']}")
    assert detail_response.status_code == 200
    assert [item["display_file_name"] for item in detail_response.json()["files"]] == ["valid.csv", "valid (2).csv"]

    first_import = client.post(f"/files/{first_file_id}/import-observations")
    assert first_import.status_code == 200
    assert first_import.json()["imported_count"] == 1

    second_import = client.post(f"/files/{second_file_id}/import-observations")
    assert second_import.status_code == 200
    assert second_import.json()["imported_count"] == 1
    assert "заменены" in second_import.json()["validation"]["message"]

    observations_response = client.get(f"/versions/{version_id}/observations")
    assert observations_response.status_code == 200
    observations = observations_response.json()
    assert len(observations) == 1
    assert observations[0]["source_file_id"] == second_file_id

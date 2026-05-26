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


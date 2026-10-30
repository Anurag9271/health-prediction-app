import pytest

import config
import database

DATA = {"full_name": "Robyn Pears", "dob": "28/01/1960", "email": "robyn@gmail.com",
        "glucose": 232.0, "haemoglobin": 13.5, "cholesterol": 180.0}


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "test.db"))
    database.init_db()


def test_crud_cycle():
    pid = database.create_patient(DATA, "remark")
    assert database.get_patient(pid)["full_name"] == "Robyn Pears"
    database.update_patient(pid, {**DATA, "email": "gokul@infocare.com"}, "remark")
    assert database.get_patient(pid)["email"] == "gokul@infocare.com"
    assert database.delete_patient(pid) is True
    assert database.get_all_patients() == []


def test_duplicate_email_rejected_case_insensitive():
    database.create_patient(DATA, "x")
    with pytest.raises(database.DuplicateEmailError):
        database.create_patient({**DATA, "email": "ROBYN@gmail.com"}, "x")




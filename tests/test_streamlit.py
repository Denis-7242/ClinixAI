"""Smoke tests for the Streamlit pages."""

from streamlit.testing.v1 import AppTest
from pathlib import Path
import pytest

from database.db import init_db

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path / 'streamlit.db'}"
    monkeypatch.setenv("CLINIXAI_DB_URL", db_url)
    init_db(db_url)


def test_home_page_loads():
    app = AppTest.from_file(ROOT / "app.py")
    app.run(timeout=10)
    assert not app.exception
    assert app.warning


def test_assessment_page_loads():
    app = AppTest.from_file(ROOT / "pages" / "1_Assessment.py")
    app.run(timeout=10)
    assert not app.exception
    assert app.warning


def test_free_text_flow_requires_symptom_confirmation():
    app = AppTest.from_file(ROOT / "pages" / "1_Assessment.py")
    app.run(timeout=10)
    app.radio[0].set_value("Describe your symptoms").run(timeout=10)
    app.text_area[0].input("I have a fever and cough").run(timeout=10)
    app.button[0].click().run(timeout=10)
    assert not app.exception
    assert any(item.value == "Confirm detected symptoms" for item in app.subheader)
    assert any(item.label == "Assess" for item in app.button)


def test_results_page_loads_without_assessment():
    app = AppTest.from_file(ROOT / "pages" / "2_Results.py")
    app.run(timeout=10)
    assert not app.exception
    assert app.info


def test_history_page_loads():
    app = AppTest.from_file(ROOT / "pages" / "3_History.py")
    app.run(timeout=10)
    assert not app.exception
    assert app.warning


def test_about_page_loads():
    app = AppTest.from_file(ROOT / "pages" / "4_About_and_Safety.py")
    app.run(timeout=10)
    assert not app.exception
    assert app.warning
    assert app.error


def test_red_flag_result_alert_is_first():
    app = AppTest.from_file(ROOT / "pages" / "2_Results.py")
    app.session_state["latest_assessment"] = {
        "valid": True,
        "red_flag_triggered": True,
        "red_flag_message": "Seek emergency care now.",
        "models_disagree": False,
        "errors": [],
        "results": [],
        "suggested_questions": [],
    }
    app.run(timeout=10)
    assert not app.exception
    assert app.error

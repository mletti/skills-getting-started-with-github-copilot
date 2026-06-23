from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module
from src.app import app

client = TestClient(app)
INITIAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activity_data():
    app_module.activities = deepcopy(INITIAL_ACTIVITIES)
    yield


def test_get_activities_returns_activity_list():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert expected_activity in activities
    assert "description" in activities[expected_activity]
    assert isinstance(activities[expected_activity]["participants"], list)


def test_signup_adds_new_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.post(f"/activities/{encoded_activity}/signup?email={quote(email, safe='')}")

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for {activity_name}"

    refreshed = client.get("/activities").json()
    assert email in refreshed[activity_name]["participants"]


def test_duplicate_signup_returns_bad_request():
    # Arrange
    activity_name = "Chess Club"
    email = "duplicate.student@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    first_response = client.post(f"/activities/{encoded_activity}/signup?email={quote(email, safe='')}")
    duplicate_response = client.post(f"/activities/{encoded_activity}/signup?email={quote(email, safe='')}")

    # Assert
    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student already signed up for this activity"


def test_remove_participant_from_activity():
    # Arrange
    activity_name = "Chess Club"
    email_to_remove = "michael@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.delete(f"/activities/{encoded_activity}/participants?email={quote(email_to_remove, safe='')}" )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email_to_remove} from {activity_name}"

    refreshed = client.get("/activities").json()
    assert email_to_remove not in refreshed[activity_name]["participants"]


def test_remove_missing_participant_returns_not_found():
    # Arrange
    activity_name = "Chess Club"
    missing_email = "missing.student@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity}/participants?email={quote(missing_email, safe='')}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"

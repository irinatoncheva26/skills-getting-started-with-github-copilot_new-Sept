from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    original_activities = deepcopy(app_module.activities)
    with TestClient(app_module.app) as test_client:
        yield test_client
    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 9
    assert activities["Chess Club"]["max_participants"] == 12
    assert "participants" in activities["Chess Club"]


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Soccer%20Team/signup",
        params={"email": "alex@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up alex@mergington.edu for Soccer Team"
    }
    assert "alex@mergington.edu" in app_module.activities["Soccer Team"]["participants"]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Club/signup",
        params={"email": "alex@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_signup_rejects_full_activity(client):
    activity = app_module.activities["Soccer Team"]
    activity["participants"] = [
        f"student-{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]

    response = client.post(
        "/activities/Soccer%20Team/signup",
        params={"email": "late@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}


def test_remove_participant_removes_email(client):
    response = client.delete(
        "/activities/Chess%20Club/participants/michael%40mergington.edu"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in app_module.activities["Chess Club"]["participants"]


def test_remove_participant_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Club/participants/alex%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_remove_participant_rejects_non_participant(client):
    response = client.delete(
        "/activities/Chess%20Club/participants/alex%40mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
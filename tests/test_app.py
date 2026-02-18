"""
Tests for the Mergington High School Activities API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the in-memory activities dict to its original state after each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_all_activities(self):
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9

    def test_activity_has_required_fields(self):
        response = client.get("/activities")
        for activity in response.json().values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity

    def test_chess_club_has_preloaded_participants(self):
        response = client.get("/activities")
        chess = response.json()["Chess Club"]
        assert "michael@mergington.edu" in chess["participants"]
        assert "daniel@mergington.edu" in chess["participants"]


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_successful_signup(self):
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self):
        client.post("/activities/Art Club/signup?email=alice@mergington.edu")
        response = client.get("/activities")
        assert "alice@mergington.edu" in response.json()["Art Club"]["participants"]

    def test_signup_unknown_activity_returns_404(self):
        response = client.post(
            "/activities/Nonexistent Club/signup?email=x@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_returns_400(self):
        # michael is already in Chess Club from preloaded data
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_different_students(self):
        client.post("/activities/Soccer Club/signup?email=student1@mergington.edu")
        client.post("/activities/Soccer Club/signup?email=student2@mergington.edu")
        response = client.get("/activities")
        participants = response.json()["Soccer Club"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_successful_unregister(self):
        response = client.delete(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" in response.json()["message"]

    def test_unregister_removes_participant(self):
        client.delete("/activities/Chess Club/signup?email=michael@mergington.edu")
        response = client.get("/activities")
        assert "michael@mergington.edu" not in response.json()["Chess Club"]["participants"]

    def test_unregister_unknown_activity_returns_404(self):
        response = client.delete(
            "/activities/Nonexistent Club/signup?email=x@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_registered_returns_400(self):
        response = client.delete(
            "/activities/Chess Club/signup?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_signup_then_unregister(self):
        client.post("/activities/Art Club/signup?email=temp@mergington.edu")
        client.delete("/activities/Art Club/signup?email=temp@mergington.edu")
        response = client.get("/activities")
        assert "temp@mergington.edu" not in response.json()["Art Club"]["participants"]

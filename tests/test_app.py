from copy import deepcopy

import pytest
from httpx import ASGITransport, AsyncClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_state = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(deepcopy(original_state))


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_get_activities_returns_activity_catalog():
    # Arrange
    expected_activity_names = set(app_module.activities.keys())

    # Act
    async with AsyncClient(transport=ASGITransport(app=app_module.app), base_url="http://testserver") as client:
        response = await client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert set(response.json().keys()) == expected_activity_names


@pytest.mark.anyio
async def test_signup_adds_participant_to_activity():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    original_participants = list(app_module.activities[activity_name]["participants"])

    # Act
    async with AsyncClient(transport=ASGITransport(app=app_module.app), base_url="http://testserver") as client:
        response = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert app_module.activities[activity_name]["participants"] == original_participants + [email]


@pytest.mark.anyio
async def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    email = app_module.activities[activity_name]["participants"][0]

    # Act
    async with AsyncClient(transport=ASGITransport(app=app_module.app), base_url="http://testserver") as client:
        response = await client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


@pytest.mark.anyio
async def test_unregister_removes_participant_from_activity():
    # Arrange
    activity_name = "Chess Club"
    email = app_module.activities[activity_name]["participants"][0]

    # Act
    async with AsyncClient(transport=ASGITransport(app=app_module.app), base_url="http://testserver") as client:
        response = await client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]
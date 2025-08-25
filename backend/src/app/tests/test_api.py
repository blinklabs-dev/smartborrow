from fastapi.testclient import TestClient

def test_register_user(client: TestClient):
    response = client.post(
        "/users/register",
        json={"email": "test-register@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test-register@example.com"
    assert "id" in data
    assert "hashed_password" not in data

def test_register_existing_user(client: TestClient):
    client.post(
        "/users/register",
        json={"email": "test-existing@example.com", "password": "testpassword"},
    )
    response = client.post(
        "/users/register",
        json={"email": "test-existing@example.com", "password": "testpassword"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_login_for_access_token(client: TestClient):
    # Register a user
    client.post(
        "/users/register",
        json={"email": "test-login@example.com", "password": "testpassword"},
    )
    # Then, log in
    response = client.post(
        "/users/login",
        data={"username": "test-login@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_password(client: TestClient):
    client.post(
        "/users/register",
        json={"email": "test-badpass@example.com", "password": "testpassword"},
    )
    response = client.post(
        "/users/login",
        data={"username": "test-badpass@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}

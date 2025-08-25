import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Create a TestClient
client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    # Create the database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop the database tables
    Base.metadata.drop_all(bind=engine)

def test_register_user():
    response = client.post(
        "/users/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "hashed_password" not in data

def test_register_existing_user():
    client.post(
        "/users/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    response = client.post(
        "/users/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}

def test_login_for_access_token():
    # First, register a user
    client.post(
        "/users/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    # Then, log in
    response = client.post(
        "/users/login",
        data={"username": "test@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_password():
    client.post(
        "/users/register",
        json={"email": "test@example.com", "password": "testpassword"},
    )
    response = client.post(
        "/users/login",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}

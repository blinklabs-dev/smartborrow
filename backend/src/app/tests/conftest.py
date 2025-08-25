import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Assuming the directory structure allows this import path
# We run pytest from `backend` dir with `PYTHONPATH=src`
from app.main import app
from app.core.database import Base, get_db
from app.schemas import UserCreate
from app.services import user_service

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # Use a static pool for in-memory DB
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables for each test session
Base.metadata.create_all(bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def client():
    # Setup: Create tables once per session
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    # Teardown: Drop tables once per session
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    # Setup: Create tables for the function scope
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    # Teardown: Drop tables after the function
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_user(db_session: sessionmaker):
    # Use a unique email for the fixture to avoid conflicts
    user_in = UserCreate(email="fixture-user@example.com", password="testpassword")
    user = user_service.create_user(db=db_session, user=user_in)
    return user

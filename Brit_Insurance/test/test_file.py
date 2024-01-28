import pytest
from fastapi.testclient import TestClient

import models
from app import app, get_db
from database import SessionLocal, engine


# Create a test database session
def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# Create test data setup and teardown functions
@pytest.fixture(scope="module")
def test_db():
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_token():
    return "test_token"


# Test case for Health endpoint
def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "OK"}


# Run tests
if __name__ == "__main__":
    pytest.main()

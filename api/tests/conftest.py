import pytest
from app import create_app, db

@pytest.fixture
def client():
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///tests.db",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }

    app = create_app(test_config)
    app.testing = True

    with app.app_context():
        db.create_all()
    yield app.test_client()
    with app.app_context():
        db.drop_all()
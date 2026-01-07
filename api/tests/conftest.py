import pytest
from app import create_app, db

@pytest.fixture
def app():
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///tests.db",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    }
    app = create_app(test_config)
    return app

@pytest.fixture
def client(app):
    with app.app_context():
        db.create_all()
    yield app.test_client()
    with app.app_context():
        db.drop_all()

@pytest.fixture
def db_session(app):
    with app.app_context():
        yield db.session
        db.session.rollback()
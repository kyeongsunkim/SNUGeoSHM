import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    return app.test_client()

def test_app(client):
    # Test if app loads
    rv = client.get('/')
    assert rv.status_code == 200  # Assuming basic test, extend for Dash
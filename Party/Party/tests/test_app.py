import pytest
from unittest.mock import patch
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

@pytest.fixture
def client():
    """Creates a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@patch('database.create_hero_record')
def test_create_hero_success(mock_create_hero_record, client):
    """Test that a valid hero creation payload returns a 201."""
    mock_create_hero_record.return_value = "64f1a2b3c4d5e6f7a8b9c0d1"
    
    response = client.post('/hero/create', json={
        "username": "player1",
        "hero_name": "Arthur",
        "initial_class": "Warrior"
    })
    
    assert response.status_code == 201
    assert response.get_json()["hero_id"] == "64f1a2b3c4d5e6f7a8b9c0d1"
    mock_create_hero_record.assert_called_once_with("player1", "Arthur", "Warrior")

@patch('database.create_hero_record')
def test_create_hero_invalid_class(mock_create_hero_record, client):
    """Test that an invalid starting class is rejected."""
    response = client.post('/hero/create', json={
        "username": "player1",
        "hero_name": "Arthur",
        "initial_class": "Necromancer"
    })
    
    assert response.status_code == 400
    assert "error" in response.get_json()
    mock_create_hero_record.assert_not_called()

@patch('database.get_hero_record')
def test_get_hero_not_found(mock_get_hero_record, client):
    """Test fetching a non-existent hero."""
    mock_get_hero_record.return_value = None
    
    response = client.get('/hero/invalid_id')
    assert response.status_code == 404
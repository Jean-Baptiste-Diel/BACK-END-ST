import pytest

# Test with incorrect input parameters
@pytest.mark.parametrize("payload", [
    # Scenario 1: farm_name is None
    {"farm_name": None, "mail": "sotilma@gmail.com", "password": "soltima"},
    # Scenario 2: mail is an empty list
    {"farm_name": "Sotilma Farm", "mail": [], "password": "soltima"},
    # Scenario 3: password is an empty dict
    {"farm_name": "Sotilma Farm", "mail": "sotilma@gmail.com", "password": {}},
    # Scenario 4: not str data type
    {'farm_name': 1233, 'mail': 'sotilma@gmail.com', 'password': 'soltima'},
    # Scenario 5: no phone number
    {'farm_name': "Sotilma Farm", 'mail': 'sotilma@gmail.com', 'password': 'soltima', "address": "Zack Mbao"},
    # Scenario 6: no address
    {'farm_name': "Sotilma Farm", 'mail': 'sotilma@gmail.com', 'password': 'soltima', "phone_number": "+221783456720"}
])
def test_create_user_invalid_payloads(client, payload):
    response = client.post("/create-user", json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert "message" in data

# Test correct creation with correct parameters
def test_create_user_success(client):
    payload = {
        "farm_name": "Sotilma Farm",
        "mail": "sotilma@gmail.com",
        "password": "soltima",
        "phone_number": "+221783456720",
        "address": "Zack Mbao"
    }
    response = client.post("/create-user", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Account created successfully."
    assert "token" in data
    assert isinstance(data["token"], str)

# Test creating user already existing
def test_create_user_already_exists(client):
    payload = {
        "farm_name": "Sotilma Farm",
        "mail": "sotilma@gmail.com",
        "password": "soltima",
        "phone_number": "+221783456720",
        "address": "Zack Mbao"
    }

    # First creation should succeed
    response1 = client.post("/create-user", json=payload)
    assert response1.status_code == 201
    data1 = response1.get_json()
    assert data1["message"] == "Account created successfully."
    assert "token" in data1

    # Second creation with same email should fail
    response2 = client.post("/create-user", json=payload)
    assert response2.status_code == 409
    data2 = response2.get_json()
    assert "message" in data2
    assert data2["message"] == "Account already exists."
    # No token expected in error case
    assert "token" not in data2

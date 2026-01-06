import pytest


@pytest.mark.parametrize(
    "payload",
    [
        {"mail": "", "password": "soltima"}, # Empty mail
        {"mail": "sotilma", "password": ""}, # Empty password with wrong mail format
        {'mail': 'sotilma@gmail.com'}, # No password
    ])

def test_login_wrong_input(client, payload):
    response = client.post('/login', json=payload)
    assert response.status_code == 400
    data = response.get_json()
    assert 'message' in data


@pytest.mark.parametrize('bad_payload',
                             [{'mail': 'stilma@gmail.com', 'password': 'SotilmaFarm'},
                              {'mail': 'sotilma@gmail.com', 'password': 'Sotilma'}])
def test_login_incorrect_credentials(client, bad_payload):
    payload = {'mail': 'sotilma@gmail.com', 'password': 'SotilmaFarm', 'farm_name': 'Sotilma'}
    client.post('/create-user', json=payload)

    response = client.post('/login', json=bad_payload)
    assert response.status_code == 401
    data = response.get_json()
    assert 'message' in data


def test_login_correct(client):
    client.post('/create-user', json={'mail': 'sotilma@gmail.com', 'password': 'SotilmaFarm', 'farm_name': 'Sotilma'})

    response = client.post('/login', json={'mail': 'sotilma@gmail.com', 'password': 'SotilmaFarm'})
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'token' in data
    assert isinstance(data['token'], str)

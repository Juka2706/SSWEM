from app import app

def test_register_and_login():
    client = app.test_client()
    response = client.post("/register", data={
        "username": "testuser",
        "password": "Test123!"
    }, follow_redirects=True)
    assert response.status_code == 200

    response = client.post("/login", data={
        "username": "testuser",
        "password": "Test123!"
    }, follow_redirects=True)
    assert b"2FA" in response.data

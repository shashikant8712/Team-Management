import uuid
from fastapi.testclient import TestClient

def test_register_and_login(client: TestClient):
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "name": "Alex Mercer",
        "email": unique_email,
        "password": "Password@123",
        "organization_name": "Apex Innovations",
        "organization_type": "COMPANY"
    }
    
    # 1. Register
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["role"] == "ADMIN"
    assert data["organization"]["name"] == "Apex Innovations"
    
    # 2. Duplicate registration should fail
    dup_res = client.post("/api/auth/register", json=reg_payload)
    assert dup_res.status_code == 400
    
    # 3. Successful Login
    login_res = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "Password@123"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    token = login_data["access_token"]
    
    # 4. Invalid Password Login
    bad_login = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": "WrongPassword"
    })
    assert bad_login.status_code == 401
    
    # 5. Access /api/auth/me with valid Bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == unique_email

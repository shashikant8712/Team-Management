import uuid
from fastapi.testclient import TestClient

def test_organization_isolation(client: TestClient):
    suffix_a = uuid.uuid4().hex[:6]
    suffix_b = uuid.uuid4().hex[:6]
    
    # 1. Create Organization A
    res_a = client.post("/api/auth/register", json={
        "name": f"Admin A {suffix_a}",
        "email": f"admin_a_{suffix_a}@org-a.com",
        "password": "Password@123",
        "organization_name": f"Organization Alpha {suffix_a}",
        "organization_type": "COMPANY"
    })
    assert res_a.status_code == 201
    token_a = res_a.json()["access_token"]
    org_a_id = res_a.json()["organization"]["id"]
    headers_a = {"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_a_id}
    
    # 2. Create Organization B
    res_b = client.post("/api/auth/register", json={
        "name": f"Admin B {suffix_b}",
        "email": f"admin_b_{suffix_b}@org-b.com",
        "password": "Password@123",
        "organization_name": f"Organization Beta {suffix_b}",
        "organization_type": "COMPANY"
    })
    assert res_b.status_code == 201
    token_b = res_b.json()["access_token"]
    org_b_id = res_b.json()["organization"]["id"]
    headers_b = {"Authorization": f"Bearer {token_b}", "X-Organization-Id": org_b_id}
    
    # 3. Create Department in Org A
    dept_a_res = client.post("/api/departments/", json={
        "name": f"Secret Tech {suffix_a}",
        "description": "Proprietary Org A R&D"
    }, headers=headers_a)
    assert dept_a_res.status_code == 201
    dept_a_id = dept_a_res.json()["id"]
    
    # 4. Org B lists departments -> MUST NOT see Dept A
    b_depts = client.get("/api/departments/", headers=headers_b).json()
    b_dept_ids = [d["id"] for d in b_depts]
    assert dept_a_id not in b_dept_ids
    
    # 5. Org B tries to access Dept A by ID -> MUST return 404
    b_get_dept_a = client.get(f"/api/departments/{dept_a_id}", headers=headers_b)
    assert b_get_dept_a.status_code == 404
    
    # 6. Create Project in Org A
    proj_a_res = client.post("/api/projects/", json={
        "name": f"Top Secret Project {suffix_a}",
        "department_id": dept_a_id,
        "priority": "HIGH",
        "status": "IN_PROGRESS"
    }, headers=headers_a)
    assert proj_a_res.status_code == 201
    proj_a_id = proj_a_res.json()["id"]
    
    # 7. Org B lists projects -> MUST NOT see Project A
    b_projects = client.get("/api/projects/", headers=headers_b).json()
    b_proj_ids = [p["id"] for p in b_projects]
    assert proj_a_id not in b_proj_ids
    
    # 8. Org B tries to access Project A -> MUST return 404
    b_get_proj_a = client.get(f"/api/projects/{proj_a_id}", headers=headers_b)
    assert b_get_proj_a.status_code == 404
    
    # 9. Org B tries to delete Project A -> MUST return 404
    b_del_proj_a = client.delete(f"/api/projects/{proj_a_id}", headers=headers_b)
    assert b_del_proj_a.status_code == 404
    
    # 10. User A cannot spoof X-Organization-Id as Org B
    spoofed_headers = {"Authorization": f"Bearer {token_a}", "X-Organization-Id": org_b_id}
    spoof_res = client.get("/api/departments/", headers=spoofed_headers)
    assert spoof_res.status_code == 403

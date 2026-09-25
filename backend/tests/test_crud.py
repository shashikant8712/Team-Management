import uuid
from fastapi.testclient import TestClient

def test_crud_full_matrix(client: TestClient):
    suffix = uuid.uuid4().hex[:6]
    # 1. Register
    reg = client.post("/api/auth/register", json={
        "name": f"Admin CRUD {suffix}",
        "email": f"crud_{suffix}@company.com",
        "password": "Password@123",
        "organization_name": f"CRUD Org {suffix}",
        "organization_type": "COMPANY"
    }).json()
    token = reg["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-Id": reg["organization"]["id"]}
    
    # 2. Department CRUD
    d_create = client.post("/api/departments/", json={"name": f"Dept {suffix}", "description": "Desc"}, headers=headers)
    assert d_create.status_code == 201
    d_id = d_create.json()["id"]
    
    d_get = client.get(f"/api/departments/{d_id}", headers=headers)
    assert d_get.status_code == 200
    assert d_get.json()["name"] == f"Dept {suffix}"
    
    d_update = client.put(f"/api/departments/{d_id}", json={"name": f"Dept Up {suffix}", "description": "New Desc"}, headers=headers)
    assert d_update.status_code == 200
    assert d_update.json()["name"] == f"Dept Up {suffix}"
    
    # 3. Team CRUD
    t_create = client.post("/api/teams/", json={"department_id": d_id, "name": f"Team {suffix}", "description": "TDesc"}, headers=headers)
    assert t_create.status_code == 201
    t_id = t_create.json()["id"]
    
    t_update = client.put(f"/api/teams/{t_id}", json={"name": f"Team Up {suffix}"}, headers=headers)
    assert t_update.status_code == 200
    assert t_update.json()["name"] == f"Team Up {suffix}"
    
    # 4. Member CRUD
    m_create = client.post("/api/members/", json={
        "name": f"Member {suffix}",
        "email": f"member_{suffix}@company.com",
        "role_name": "TEAM_MEMBER",
        "department_id": d_id
    }, headers=headers)
    assert m_create.status_code == 201
    m_id = m_create.json()["id"]
    u_id = m_create.json()["user_id"]
    
    # Add member to team
    tm_add = client.post(f"/api/teams/{t_id}/members", json={"user_id": u_id}, headers=headers)
    assert tm_add.status_code == 201
    
    # 5. Project CRUD
    p_create = client.post("/api/projects/", json={
        "name": f"Project {suffix}",
        "department_id": d_id,
        "team_id": t_id,
        "priority": "MEDIUM",
        "status": "NOT_STARTED"
    }, headers=headers)
    assert p_create.status_code == 201
    p_id = p_create.json()["id"]
    
    p_update = client.put(f"/api/projects/{p_id}", json={"priority": "HIGH", "status": "IN_PROGRESS"}, headers=headers)
    assert p_update.status_code == 200
    assert p_update.json()["priority"] == "HIGH"
    assert p_update.json()["status"] == "IN_PROGRESS"
    
    # 6. Task CRUD
    tsk_create = client.post("/api/tasks/", json={
        "project_id": p_id,
        "team_id": t_id,
        "title": f"Task {suffix}",
        "assigned_to": u_id,
        "status": "TODO",
        "priority": "LOW"
    }, headers=headers)
    assert tsk_create.status_code == 201
    tsk_id = tsk_create.json()["id"]
    
    tsk_up = client.put(f"/api/tasks/{tsk_id}", json={"priority": "URGENT", "title": f"Task Up {suffix}"}, headers=headers)
    assert tsk_up.status_code == 200
    assert tsk_up.json()["priority"] == "URGENT"
    
    # Delete task
    del_tsk = client.delete(f"/api/tasks/{tsk_id}", headers=headers)
    assert del_tsk.status_code == 204
    
    # Delete project
    del_proj = client.delete(f"/api/projects/{p_id}", headers=headers)
    assert del_proj.status_code == 204
    
    # Delete team
    del_team = client.delete(f"/api/teams/{t_id}", headers=headers)
    assert del_team.status_code == 204
    
    # Delete department
    del_dept = client.delete(f"/api/departments/{d_id}", headers=headers)
    assert del_dept.status_code == 204

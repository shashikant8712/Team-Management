import uuid
from fastapi.testclient import TestClient

def test_project_progress_and_completion_lifecycle(client: TestClient):
    suffix = uuid.uuid4().hex[:6]
    admin_email = f"lead_{suffix}@acme.com"
    
    # 1. Register organization and admin
    res = client.post("/api/auth/register", json={
        "name": f"Manager {suffix}",
        "email": admin_email,
        "password": "Password@123",
        "organization_name": f"Acme Corp {suffix}",
        "organization_type": "COMPANY"
    })
    assert res.status_code == 201
    auth_data = res.json()
    token = auth_data["access_token"]
    org_id = auth_data["organization"]["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-Id": org_id}
    
    # 2. Create department
    dept_res = client.post("/api/departments/", json={
        "name": f"Engineering {suffix}",
        "description": "Core software engineering"
    }, headers=headers)
    assert dept_res.status_code == 201
    dept_id = dept_res.json()["id"]
    
    # 3. Create team
    team_res = client.post("/api/teams/", json={
        "department_id": dept_id,
        "name": f"Backend Team {suffix}",
        "description": "API and database systems"
    }, headers=headers)
    assert team_res.status_code == 201
    team_id = team_res.json()["id"]
    
    # 4. Create member
    member_email = f"dev_{suffix}@acme.com"
    mem_res = client.post("/api/members/", json={
        "name": "Jane Developer",
        "email": member_email,
        "role_name": "TEAM_MEMBER",
        "department_id": dept_id,
        "team_id": team_id
    }, headers=headers)
    assert mem_res.status_code == 201
    dev_user_id = mem_res.json()["user_id"]
    
    # 5. Create project
    proj_res = client.post("/api/projects/", json={
        "name": f"Project Titan {suffix}",
        "description": "Next-gen platform launch",
        "department_id": dept_id,
        "team_id": team_id,
        "priority": "HIGH",
        "status": "IN_PROGRESS"
    }, headers=headers)
    assert proj_res.status_code == 201
    project = proj_res.json()
    proj_id = project["id"]
    assert project["progress"] == 0
    
    # 6. Create 5 tasks
    task_ids = []
    for i in range(1, 6):
        t_res = client.post("/api/tasks/", json={
            "project_id": proj_id,
            "team_id": team_id,
            "title": f"Task {i} - Implementation {suffix}",
            "assigned_to": dev_user_id,
            "status": "TODO",
            "priority": "MEDIUM"
        }, headers=headers)
        assert t_res.status_code == 201
        task_ids.append(t_res.json()["id"])
    
    assert len(task_ids) == 5
    
    # Verify initial project progress is 0%
    proj_check = client.get(f"/api/projects/{proj_id}", headers=headers).json()
    assert proj_check["progress"] == 0
    assert proj_check["total_tasks"] == 5
    assert proj_check["completed_tasks"] == 0
    
    # 7 & 8. Complete 3 tasks
    for i in range(3):
        patch_res = client.patch(
            f"/api/tasks/{task_ids[i]}/status",
            json={"status": "COMPLETED"},
            headers=headers
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "COMPLETED"
        assert patch_res.json()["completed_at"] is not None
        
    # 9. Verify progress = 60% (3 / 5 * 100)
    proj_60 = client.get(f"/api/projects/{proj_id}", headers=headers).json()
    assert proj_60["completed_tasks"] == 3
    assert proj_60["total_tasks"] == 5
    assert proj_60["progress"] == 60
    
    # 10. Complete remaining 2 tasks
    for i in range(3, 5):
        patch_res = client.patch(
            f"/api/tasks/{task_ids[i]}/status",
            json={"status": "COMPLETED"},
            headers=headers
        )
        assert patch_res.status_code == 200
        
    # 11. Verify progress = 100% (5 / 5 * 100)
    proj_100 = client.get(f"/api/projects/{proj_id}", headers=headers).json()
    assert proj_100["completed_tasks"] == 5
    assert proj_100["progress"] == 100
    
    # 12. Complete project
    comp_res = client.post(f"/api/projects/{proj_id}/complete", headers=headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()
    assert comp_data["status"] == "COMPLETED"
    assert comp_data["progress"] == 100
    
    # 13. Verify completion_date is stored
    assert comp_data["completion_date"] is not None
    
    # 14. Verify project appears in Project History (is_history=True)
    hist_res = client.get("/api/projects/?is_history=true", headers=headers)
    assert hist_res.status_code == 200
    history_ids = [p["id"] for p in hist_res.json()]
    assert proj_id in history_ids
    
    # Ensure it no longer appears in current active projects
    curr_res = client.get("/api/projects/?is_history=false", headers=headers)
    assert curr_res.status_code == 200
    current_ids = [p["id"] for p in curr_res.json()]
    assert proj_id not in current_ids
    
    # 15. Verify dashboard updates
    dash_res = client.get("/api/dashboard/", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["counts"]["departments_count"] >= 1
    assert dash_data["counts"]["teams_count"] >= 1
    assert dash_data["counts"]["members_count"] >= 2
    assert len(dash_data["recent_activity"]) > 0

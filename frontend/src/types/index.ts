export type RoleName = 'ADMIN' | 'DEPARTMENT_HEAD' | 'TEAM_LEADER' | 'TEAM_MEMBER';
export type ProjectPriority = 'LOW' | 'MEDIUM' | 'HIGH';
export type ProjectStatus = 'PLANNING' | 'NOT_STARTED' | 'IN_PROGRESS' | 'ON_HOLD' | 'COMPLETED' | 'ARCHIVED';
export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'REVIEW' | 'COMPLETED';
export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  profile_photo?: string;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string;
}

export interface OrgBrief {
  id: string;
  name: string;
  organization_type: string;
  role: RoleName;
}

export interface Organization {
  id: string;
  name: string;
  organization_type: string;
  description?: string;
  logo?: string;
  timezone?: string;
  status: 'ACTIVE' | 'INACTIVE';
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  department_head_id?: string;
  head_name?: string;
  status: 'ACTIVE' | 'INACTIVE';
  teams_count: number;
  members_count: number;
  created_at: string;
  updated_at: string;
}

export interface Team {
  id: string;
  organization_id: string;
  department_id: string;
  department_name?: string;
  name: string;
  description?: string;
  team_leader_id?: string;
  leader_name?: string;
  status: 'ACTIVE' | 'INACTIVE';
  members_count: number;
  created_at: string;
  updated_at: string;
}

export interface TeamMemberItem {
  id: string;
  team_id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  user_role?: string;
  joined_at: string;
  status: string;
}

export interface Member {
  id: string;
  user_id: string;
  organization_id: string;
  name: string;
  email: string;
  phone?: string;
  profile_photo?: string;
  role_id: string;
  role_name: RoleName;
  department_id?: string;
  department_name?: string;
  status: 'ACTIVE' | 'INACTIVE';
  joining_date: string;
  created_at: string;
}

export interface Project {
  id: string;
  organization_id: string;
  department_id?: string;
  department_name?: string;
  team_id?: string;
  team_name?: string;
  name: string;
  description?: string;
  project_manager_id?: string;
  manager_name?: string;
  start_date?: string;
  deadline?: string;
  priority: ProjectPriority;
  status: ProjectStatus;
  progress: number;
  completion_date?: string;
  archive_date?: string;
  created_by?: string;
  creator_name?: string;
  total_tasks: number;
  completed_tasks: number;
  members_count: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  organization_id: string;
  project_id: string;
  project_name?: string;
  team_id?: string;
  team_name?: string;
  title: string;
  description?: string;
  assigned_to?: string;
  assignee_name?: string;
  created_by?: string;
  start_date?: string;
  due_date?: string;
  status: TaskStatus;
  priority: TaskPriority;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Activity {
  id: string;
  organization_id: string;
  user_id?: string;
  user_name?: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  description: string;
  created_at: string;
}

export interface DashboardData {
  counts: {
    departments_count: number;
    teams_count: number;
    members_count: number;
    active_projects_count: number;
    pending_tasks_count: number;
  };
  current_projects: {
    id: string;
    name: string;
    status: ProjectStatus;
    priority: ProjectPriority;
    progress: number;
    deadline?: string;
    manager_name?: string;
    team_name?: string;
  }[];
  upcoming_tasks: {
    id: string;
    title: string;
    project_name?: string;
    status: TaskStatus;
    priority: TaskPriority;
    due_date?: string;
    assignee_name?: string;
  }[];
  recent_activity: {
    id: string;
    action: string;
    entity_type: string;
    description: string;
    created_at: string;
    user_name?: string;
  }[];
  user_role: RoleName;
  department_name?: string;
  team_name?: string;
}

import {
  User, Organization, OrgBrief, Department, Team, TeamMemberItem,
  Member, Project, Task, Activity, DashboardData
} from '../types';

const API_BASE = '/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const orgId = localStorage.getItem('org_id');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (orgId) {
    headers['X-Organization-Id'] = orgId;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const errorMsg = data?.detail || response.statusText || 'An error occurred';
    if (response.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('org_id');
      if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/login';
      }
    }
    throw new Error(errorMsg);
  }

  return data as T;
}

export const api = {
  // Auth
  auth: {
    register: (body: any) => request<any>('/auth/register', { method: 'POST', body: JSON.stringify(body) }),
    login: (body: any) => request<any>('/auth/login', { method: 'POST', body: JSON.stringify(body) }),
    getMe: () => request<any>('/auth/me'),
    getMyOrgs: () => request<OrgBrief[]>('/auth/my-organizations'),
    switchOrg: (orgId: string) => request<any>('/auth/switch-organization', {
      method: 'POST',
      body: JSON.stringify({ organization_id: orgId })
    }),
  },

  // Organizations
  organizations: {
    getCurrent: () => request<Organization>('/organizations/current'),
    updateCurrent: (body: any) => request<Organization>('/organizations/current', { method: 'PUT', body: JSON.stringify(body) }),
    create: (body: any) => request<Organization>('/organizations/', { method: 'POST', body: JSON.stringify(body) }),
  },

  // Departments
  departments: {
    list: (search?: string) => request<Department[]>(`/departments/${search ? `?search=${encodeURIComponent(search)}` : ''}`),
    get: (id: string) => request<Department>(`/departments/${id}`),
    create: (body: any) => request<Department>('/departments/', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: string, body: any) => request<Department>(`/departments/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
    delete: (id: string) => request<void>(`/departments/${id}`, { method: 'DELETE' }),
  },

  // Teams
  teams: {
    list: (params?: { department_id?: string; search?: string }) => {
      const q = new URLSearchParams();
      if (params?.department_id) q.append('department_id', params.department_id);
      if (params?.search) q.append('search', params.search);
      const qs = q.toString();
      return request<Team[]>(`/teams/${qs ? `?${qs}` : ''}`);
    },
    get: (id: string) => request<Team>(`/teams/${id}`),
    create: (body: any) => request<Team>('/teams/', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: string, body: any) => request<Team>(`/teams/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
    delete: (id: string) => request<void>(`/teams/${id}`, { method: 'DELETE' }),
    getMembers: (id: string) => request<TeamMemberItem[]>(`/teams/${id}/members`),
    addMember: (id: string, userId: string) => request<TeamMemberItem>(`/teams/${id}/members`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId })
    }),
    removeMember: (id: string, userId: string) => request<void>(`/teams/${id}/members/${userId}`, { method: 'DELETE' }),
  },

  // Members
  members: {
    list: (params?: { department_id?: string; role_name?: string; search?: string }) => {
      const q = new URLSearchParams();
      if (params?.department_id) q.append('department_id', params.department_id);
      if (params?.role_name) q.append('role_name', params.role_name);
      if (params?.search) q.append('search', params.search);
      const qs = q.toString();
      return request<Member[]>(`/members/${qs ? `?${qs}` : ''}`);
    },
    getRoles: () => request<{ id: string; name: string; description: string }[]>('/members/roles'),
    get: (id: string) => request<Member>(`/members/${id}`),
    add: (body: any) => request<Member>('/members/', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: string, body: any) => request<Member>(`/members/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
    delete: (id: string) => request<void>(`/members/${id}`, { method: 'DELETE' }),
  },

  // Projects
  projects: {
    list: (params?: { is_history?: boolean; status?: string; priority?: string; department_id?: string; team_id?: string; search?: string }) => {
      const q = new URLSearchParams();
      if (params?.is_history !== undefined) q.append('is_history', String(params.is_history));
      if (params?.status) q.append('status', params.status);
      if (params?.priority) q.append('priority', params.priority);
      if (params?.department_id) q.append('department_id', params.department_id);
      if (params?.team_id) q.append('team_id', params.team_id);
      if (params?.search) q.append('search', params.search);
      const qs = q.toString();
      return request<Project[]>(`/projects/${qs ? `?${qs}` : ''}`);
    },
    get: (id: string) => request<Project>(`/projects/${id}`),
    create: (body: any) => request<Project>('/projects/', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: string, body: any) => request<Project>(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
    complete: (id: string) => request<Project>(`/projects/${id}/complete`, { method: 'POST' }),
    archive: (id: string) => request<Project>(`/projects/${id}/archive`, { method: 'POST' }),
    delete: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE' }),
    getMembers: (id: string) => request<any[]>(`/projects/${id}/members`),
    addMember: (id: string, userId: string) => request<any>(`/projects/${id}/members`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId })
    }),
    removeMember: (id: string, userId: string) => request<void>(`/projects/${id}/members/${userId}`, { method: 'DELETE' }),
  },

  // Tasks
  tasks: {
    list: (params?: { project_id?: string; team_id?: string; assigned_to?: string; status?: string; priority?: string; search?: string }) => {
      const q = new URLSearchParams();
      if (params?.project_id) q.append('project_id', params.project_id);
      if (params?.team_id) q.append('team_id', params.team_id);
      if (params?.assigned_to) q.append('assigned_to', params.assigned_to);
      if (params?.status) q.append('status', params.status);
      if (params?.priority) q.append('priority', params.priority);
      if (params?.search) q.append('search', params.search);
      const qs = q.toString();
      return request<Task[]>(`/tasks/${qs ? `?${qs}` : ''}`);
    },
    get: (id: string) => request<Task>(`/tasks/${id}`),
    create: (body: any) => request<Task>('/tasks/', { method: 'POST', body: JSON.stringify(body) }),
    update: (id: string, body: any) => request<Task>(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
    updateStatus: (id: string, status: string) => request<Task>(`/tasks/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status })
    }),
    delete: (id: string) => request<void>(`/tasks/${id}`, { method: 'DELETE' }),
  },

  // Dashboard
  dashboard: {
    get: () => request<DashboardData>('/dashboard/'),
  },

  // Activities
  activities: {
    list: (limit = 50) => request<Activity[]>(`/activities/?limit=${limit}`),
  },

  // Settings
  settings: {
    getProfile: () => request<User>('/settings/profile'),
    updateProfile: (body: any) => request<User>('/settings/profile', { method: 'PUT', body: JSON.stringify(body) }),
    changePassword: (body: any) => request<{ message: string }>('/settings/change-password', { method: 'POST', body: JSON.stringify(body) }),
    updateOrgSettings: (body: any) => request<Organization>('/settings/organization', { method: 'PUT', body: JSON.stringify(body) }),
  }
};

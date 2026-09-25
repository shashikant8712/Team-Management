import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, OrgBrief, RoleName } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  organization: OrgBrief | null;
  myOrganizations: OrgBrief[];
  role: RoleName | null;
  permissions: string[];
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  switchOrg: (orgId: string) => Promise<void>;
  refreshUser: () => Promise<void>;
  hasPermission: (perm: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<OrgBrief | null>(null);
  const [myOrganizations, setMyOrganizations] = useState<OrgBrief[]>([]);
  const [role, setRole] = useState<RoleName | null>(null);
  const [permissions, setPermissions] = useState<string[]>([]);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState<boolean>(true);

  const initAuth = async () => {
    const savedToken = localStorage.getItem('token');
    if (!savedToken) {
      setLoading(false);
      return;
    }

    try {
      const data = await api.auth.getMe();
      setUser(data.user);
      setRole(data.role);
      setPermissions(data.permissions || []);
      if (data.organization) {
        setOrganization(data.organization);
        localStorage.setItem('org_id', data.organization.id);
      }
      const orgs = await api.auth.getMyOrgs().catch(() => []);
      setMyOrganizations(orgs);
    } catch (err) {
      console.error('Session expired or invalid token', err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    setLoading(true);
    try {
      const res = await api.auth.login({ email, password });
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      setRole(res.role);
      setPermissions(res.permissions || []);
      if (res.organization) {
        setOrganization(res.organization);
        localStorage.setItem('org_id', res.organization.id);
      }
      const orgs = await api.auth.getMyOrgs().catch(() => []);
      setMyOrganizations(orgs);
    } finally {
      setLoading(false);
    }
  };

  const register = async (data: any) => {
    setLoading(true);
    try {
      const res = await api.auth.register(data);
      localStorage.setItem('token', res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      setRole(res.role);
      setPermissions(res.permissions || []);
      if (res.organization) {
        setOrganization(res.organization);
        localStorage.setItem('org_id', res.organization.id);
      }
      const orgs = await api.auth.getMyOrgs().catch(() => []);
      setMyOrganizations(orgs);
    } finally {
      setLoading(false);
    }
  };

  const switchOrg = async (orgId: string) => {
    setLoading(true);
    try {
      const res = await api.auth.switchOrg(orgId);
      localStorage.setItem('token', res.access_token);
      localStorage.setItem('org_id', orgId);
      setToken(res.access_token);
      setUser(res.user);
      setRole(res.role);
      setPermissions(res.permissions || []);
      setOrganization(res.organization);
    } finally {
      setLoading(false);
    }
  };

  const refreshUser = async () => {
    await initAuth();
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('org_id');
    setToken(null);
    setUser(null);
    setOrganization(null);
    setMyOrganizations([]);
    setRole(null);
    setPermissions([]);
  };

  const hasPermission = (perm: string) => {
    if (role === 'ADMIN') return true;
    return permissions.includes(perm);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        myOrganizations,
        role,
        permissions,
        token,
        loading,
        login,
        register,
        logout,
        switchOrg,
        refreshUser,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Building2,
  Users2,
  UserCheck,
  FolderKanban,
  CheckSquare,
  ArrowUpRight,
  Clock,
  Activity as ActivityIcon,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { DashboardData } from '../types';
import { useAuth } from '../hooks/useAuth';

export const Dashboard: React.FC = () => {
  const { organization, role } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.dashboard.get();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [organization?.id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-3 text-sm text-slate-500 font-medium">Fetching real PostgreSQL metrics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-white rounded-xl border border-rose-200 text-rose-700 flex items-center gap-3">
        <AlertCircle className="w-6 h-6 flex-shrink-0" />
        <div>
          <h3 className="font-bold">Error loading dashboard</h3>
          <p className="text-sm">{error || 'Data unavailable'}</p>
        </div>
      </div>
    );
  }

  const statCards = [
    { label: 'Departments', value: data.counts.departments_count, icon: Building2, color: 'text-blue-600', bg: 'bg-blue-50', link: '/departments' },
    { label: 'Teams', value: data.counts.teams_count, icon: Users2, color: 'text-indigo-600', bg: 'bg-indigo-50', link: '/teams' },
    { label: 'Members', value: data.counts.members_count, icon: UserCheck, color: 'text-emerald-600', bg: 'bg-emerald-50', link: '/members' },
    { label: 'Active Projects', value: data.counts.active_projects_count, icon: FolderKanban, color: 'text-amber-600', bg: 'bg-amber-50', link: '/projects' },
    { label: 'Pending Tasks', value: data.counts.pending_tasks_count, icon: CheckSquare, color: 'text-rose-600', bg: 'bg-rose-50', link: '/tasks' },
  ];

  const getPriorityBadge = (p: string) => {
    switch (p) {
      case 'URGENT':
      case 'HIGH':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'MEDIUM':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Organization Overview</h1>
          <p className="text-sm text-slate-500 mt-1">
            {organization?.name} • Logged in as <span className="font-semibold text-slate-700">{role?.replace('_', ' ')}</span>
            {data.department_name && ` • Department: ${data.department_name}`}
            {data.team_name && ` • Team: ${data.team_name}`}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            to="/projects"
            className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold shadow-sm transition"
          >
            Manage Projects
          </Link>
          <Link
            to="/tasks"
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-semibold transition"
          >
            Tasks Board
          </Link>
        </div>
      </div>

      {/* 5 Real DB Counts */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {statCards.map((stat, i) => (
          <Link
            key={i}
            to={stat.link}
            className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-indigo-300 hover:shadow-md transition group"
          >
            <div className="flex items-center justify-between">
              <span className={`p-2.5 rounded-xl ${stat.bg} ${stat.color}`}>
                <stat.icon className="w-5 h-5" />
              </span>
              <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 transition" />
            </div>
            <div className="mt-4">
              <span className="text-2xl font-extrabold text-slate-900">{stat.value}</span>
              <p className="text-xs font-semibold text-slate-500 mt-0.5">{stat.label}</p>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Current Projects & Progress (2 cols) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <FolderKanban className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-bold text-slate-900">Current Projects</h2>
              </div>
              <Link to="/projects" className="text-xs font-semibold text-indigo-600 hover:underline">
                View All
              </Link>
            </div>

            {data.current_projects.length === 0 ? (
              <div className="text-center py-10 text-slate-400 text-sm">
                No active projects yet.{' '}
                <Link to="/projects" className="text-indigo-600 font-semibold underline">
                  Create the first project
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {data.current_projects.map((proj) => (
                  <div key={proj.id} className="p-4 rounded-xl border border-slate-100 hover:border-slate-200 bg-slate-50/50 transition">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm">{proj.name}</h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {proj.team_name ? `Team: ${proj.team_name}` : 'No team assigned'}
                          {proj.manager_name && ` • PM: ${proj.manager_name}`}
                        </p>
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-semibold border ${getPriorityBadge(proj.priority)}`}>
                        {proj.priority}
                      </span>
                    </div>

                    {/* Progress Bar (Real formula) */}
                    <div className="mt-3">
                      <div className="flex items-center justify-between text-xs mb-1 font-medium text-slate-600">
                        <span>Progress (Real calculated)</span>
                        <span className="font-bold text-indigo-600">{proj.progress}%</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-slate-200 overflow-hidden">
                        <div
                          className="h-full bg-indigo-600 transition-all duration-500 rounded-full"
                          style={{ width: `${proj.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Upcoming Tasks */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-bold text-slate-900">Upcoming Tasks</h2>
              </div>
              <Link to="/tasks" className="text-xs font-semibold text-indigo-600 hover:underline">
                View All
              </Link>
            </div>

            {data.upcoming_tasks.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-sm">No pending tasks.</div>
            ) : (
              <div className="divide-y divide-slate-100">
                {data.upcoming_tasks.map((task) => (
                  <div key={task.id} className="py-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-800 truncate">{task.title}</p>
                      <p className="text-xs text-slate-400 truncate mt-0.5">
                        {task.project_name || 'Project'} • Assignee: {task.assignee_name || 'Unassigned'}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className={`text-[10px] px-2 py-0.5 rounded font-semibold border ${getPriorityBadge(task.priority)}`}>
                        {task.priority}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-slate-100 text-slate-700">
                        {task.status.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Activity Feed (1 col) */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs flex flex-col h-full">
          <div className="flex items-center gap-2 mb-5">
            <ActivityIcon className="w-5 h-5 text-indigo-600" />
            <h2 className="text-lg font-bold text-slate-900">Recent Activity</h2>
          </div>

          {data.recent_activity.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-sm">No activity recorded yet.</div>
          ) : (
            <div className="space-y-4 flex-1 overflow-y-auto max-h-[600px] pr-1">
              {data.recent_activity.map((act) => (
                <div key={act.id} className="flex items-start gap-3 text-xs pb-3 border-b border-slate-100 last:border-b-0">
                  <div className="w-2 h-2 rounded-full bg-indigo-500 mt-1.5 flex-shrink-0"></div>
                  <div className="flex-1 min-w-0">
                    <p className="text-slate-800 font-medium leading-relaxed">{act.description}</p>
                    <p className="text-[11px] text-slate-400 mt-1">
                      by <span className="font-semibold text-slate-600">{act.user_name || 'System'}</span> •{' '}
                      {new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

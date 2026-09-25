import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  History,
  CheckCircle2,
  Archive,
  Calendar,
  Building2,
  Users2,
  UserCheck,
  Search,
  ArrowLeft,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';
import { Project } from '../types';

export const ProjectHistory: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'COMPLETED' | 'ARCHIVED'>('ALL');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.projects.list({
        is_history: true,
        status: statusFilter === 'ALL' ? undefined : statusFilter,
        search: search || undefined,
      });
      setProjects(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load project history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchHistory();
    }, 250);
    return () => clearTimeout(timer);
  }, [statusFilter, search]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link to="/projects" className="text-slate-400 hover:text-slate-600 transition">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Project History</h1>
          </div>
          <p className="text-sm text-slate-500">Historical archive of completed deliverables and archived projects</p>
        </div>

        <Link
          to="/projects"
          className="px-3.5 py-2 text-sm font-semibold bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg shadow-xs transition"
        >
          View Active Projects
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[240px] max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search past projects..."
            className="w-full pl-9 pr-4 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="inline-flex p-1 bg-slate-200/70 rounded-xl text-xs font-semibold text-slate-600">
          <button
            onClick={() => setStatusFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg transition ${
              statusFilter === 'ALL' ? 'bg-white text-slate-900 shadow-xs' : 'hover:text-slate-900'
            }`}
          >
            All Past Projects
          </button>
          <button
            onClick={() => setStatusFilter('COMPLETED')}
            className={`px-3 py-1.5 rounded-lg transition ${
              statusFilter === 'COMPLETED' ? 'bg-white text-emerald-700 shadow-xs' : 'hover:text-slate-900'
            }`}
          >
            Completed
          </button>
          <button
            onClick={() => setStatusFilter('ARCHIVED')}
            className={`px-3 py-1.5 rounded-lg transition ${
              statusFilter === 'ARCHIVED' ? 'bg-white text-slate-700 shadow-xs' : 'hover:text-slate-900'
            }`}
          >
            Archived
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* History Grid */}
      {loading ? (
        <div className="text-center py-20 text-slate-400 text-sm">Loading project history from database...</div>
      ) : projects.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500">
          <History className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No project history recorded yet</h3>
          <p className="text-sm mt-1">When an active project is completed or archived, it is preserved here automatically.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((proj) => (
            <div
              key={proj.id}
              className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <span
                    className={`inline-flex items-center gap-1 text-[10px] px-2.5 py-1 rounded font-semibold border ${
                      proj.status === 'COMPLETED'
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                        : 'bg-slate-100 text-slate-700 border-slate-200'
                    }`}
                  >
                    {proj.status === 'COMPLETED' ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    ) : (
                      <Archive className="w-3.5 h-3.5 text-slate-500" />
                    )}
                    <span>{proj.status}</span>
                  </span>

                  <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                    Priority: {proj.priority}
                  </span>
                </div>

                <div className="mt-3">
                  <h3 className="font-bold text-base text-slate-900 leading-snug">{proj.name}</h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">{proj.description || 'No description recorded.'}</p>
                </div>

                <div className="mt-4 space-y-1.5 text-xs text-slate-600">
                  {proj.department_name && (
                    <div className="flex items-center gap-2">
                      <Building2 className="w-3.5 h-3.5 text-slate-400" />
                      <span>{proj.department_name}</span>
                    </div>
                  )}
                  {proj.team_name && (
                    <div className="flex items-center gap-2">
                      <Users2 className="w-3.5 h-3.5 text-slate-400" />
                      <span>{proj.team_name}</span>
                    </div>
                  )}
                  {proj.manager_name && (
                    <div className="flex items-center gap-2">
                      <UserCheck className="w-3.5 h-3.5 text-slate-400" />
                      <span>PM: <strong>{proj.manager_name}</strong></span>
                    </div>
                  )}
                </div>

                {/* Historical Dates */}
                <div className="mt-4 pt-3 border-t border-slate-100 text-xs text-slate-500 space-y-1">
                  {proj.completion_date && (
                    <div className="flex items-center gap-2 text-emerald-700 font-medium">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Completed on: {new Date(proj.completion_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  {proj.archive_date && (
                    <div className="flex items-center gap-2 text-slate-600">
                      <Archive className="w-3.5 h-3.5" />
                      <span>Archived on: {new Date(proj.archive_date).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>

                {/* Final Progress */}
                <div className="mt-4 pt-3 border-t border-slate-100">
                  <div className="flex items-center justify-between text-xs mb-1 font-medium text-slate-600">
                    <span>Final Progress ({proj.completed_tasks}/{proj.total_tasks} tasks)</span>
                    <span className="font-bold text-slate-900">{proj.progress}%</span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${proj.status === 'COMPLETED' ? 'bg-emerald-500' : 'bg-slate-400'}`}
                      style={{ width: `${proj.progress}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

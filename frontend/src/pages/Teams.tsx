import React, { useState, useEffect } from 'react';
import {
  Users2,
  Plus,
  Search,
  Edit2,
  Trash2,
  UserCheck,
  Building2,
  UserPlus,
  UserMinus,
  AlertCircle,
  X
} from 'lucide-react';
import { api } from '../services/api';
import { Team, Department, Member, TeamMemberItem } from '../types';
import { useAuth } from '../hooks/useAuth';

export const Teams: React.FC = () => {
  const { hasPermission } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [selectedDept, setSelectedDept] = useState<string>('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State for Team Create/Edit
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState<Team | null>(null);
  const [formData, setFormData] = useState({
    department_id: '',
    name: '',
    description: '',
    team_leader_id: '',
  });
  const [modalSubmitting, setModalSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Manage Team Members Modal State
  const [membersModalOpen, setMembersModalOpen] = useState(false);
  const [activeTeamForMembers, setActiveTeamForMembers] = useState<Team | null>(null);
  const [teamMemberList, setTeamMemberList] = useState<TeamMemberItem[]>([]);
  const [selectedUserToAdd, setSelectedUserToAdd] = useState<string>('');
  const [teamMembersLoading, setTeamMembersLoading] = useState(false);
  const [teamMembersError, setTeamMembersError] = useState<string | null>(null);

  const fetchTeams = async () => {
    try {
      setLoading(true);
      setError(null);
      const [teamsRes, deptRes, memRes] = await Promise.all([
        api.teams.list({ department_id: selectedDept || undefined, search: search || undefined }),
        api.departments.list(),
        api.members.list().catch(() => []),
      ]);
      setTeams(teamsRes);
      setDepartments(deptRes);
      setMembers(memRes);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch teams');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchTeams();
    }, 250);
    return () => clearTimeout(timer);
  }, [selectedDept, search]);

  const handleOpenCreateModal = () => {
    setEditingTeam(null);
    setFormData({
      department_id: departments[0]?.id || '',
      name: '',
      description: '',
      team_leader_id: '',
    });
    setModalError(null);
    setModalOpen(true);
  };

  const handleOpenEditModal = (team: Team) => {
    setEditingTeam(team);
    setFormData({
      department_id: team.department_id,
      name: team.name,
      description: team.description || '',
      team_leader_id: team.team_leader_id || '',
    });
    setModalError(null);
    setModalOpen(true);
  };

  const handleModalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    setModalSubmitting(true);
    try {
      const payload: any = {
        department_id: formData.department_id,
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        team_leader_id: formData.team_leader_id || null,
      };

      if (editingTeam) {
        await api.teams.update(editingTeam.id, payload);
      } else {
        await api.teams.create(payload);
      }
      setModalOpen(false);
      fetchTeams();
    } catch (err: any) {
      setModalError(err.message || 'Operation failed');
    } finally {
      setModalSubmitting(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete the team "${name}"?`)) return;
    try {
      await api.teams.delete(id);
      fetchTeams();
    } catch (err: any) {
      alert(err.message || 'Failed to delete team');
    }
  };

  // Manage Team Members
  const handleOpenMembersModal = async (team: Team) => {
    setActiveTeamForMembers(team);
    setSelectedUserToAdd('');
    setTeamMembersError(null);
    setMembersModalOpen(true);
    await loadTeamMembers(team.id);
  };

  const loadTeamMembers = async (teamId: string) => {
    setTeamMembersLoading(true);
    try {
      const list = await api.teams.getMembers(teamId);
      setTeamMemberList(list);
    } catch (err: any) {
      setTeamMembersError(err.message || 'Failed to load team members');
    } finally {
      setTeamMembersLoading(false);
    }
  };

  const handleAddMemberToTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeTeamForMembers || !selectedUserToAdd) return;
    setTeamMembersError(null);
    try {
      await api.teams.addMember(activeTeamForMembers.id, selectedUserToAdd);
      setSelectedUserToAdd('');
      await loadTeamMembers(activeTeamForMembers.id);
      fetchTeams();
    } catch (err: any) {
      setTeamMembersError(err.message || 'Failed to add member to team');
    }
  };

  const handleRemoveMemberFromTeam = async (userId: string) => {
    if (!activeTeamForMembers) return;
    try {
      await api.teams.removeMember(activeTeamForMembers.id, userId);
      await loadTeamMembers(activeTeamForMembers.id);
      fetchTeams();
    } catch (err: any) {
      alert(err.message || 'Failed to remove member from team');
    }
  };

  return (
    <div className="space-y-6">
      {/* Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Teams</h1>
          <p className="text-sm text-slate-500 mt-0.5">Manage operational teams across departments</p>
        </div>

        {hasPermission('team.create') && (
          <button
            onClick={handleOpenCreateModal}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm shadow-sm transition"
          >
            <Plus className="w-4 h-4" />
            <span>Create Team</span>
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search teams by name..."
            className="w-full pl-9 pr-4 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <select
          value={selectedDept}
          onChange={(e) => setSelectedDept(e.target.value)}
          className="px-3.5 py-2 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Departments</option>
          {departments.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-lg flex items-center gap-2">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Teams Grid */}
      {loading ? (
        <div className="text-center py-20 text-slate-400 text-sm">Loading teams from database...</div>
      ) : teams.length === 0 ? (
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500">
          <Users2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-slate-800">No teams found</h3>
          <p className="text-sm mt-1">Create teams to organize members into active work units.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {teams.map((team) => (
            <div
              key={team.id}
              className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs hover:border-slate-300 transition flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div className="p-2.5 bg-indigo-50 text-indigo-600 rounded-xl">
                    <Users2 className="w-5 h-5" />
                  </div>
                  <div className="flex items-center gap-1.5">
                    {hasPermission('team.edit') && (
                      <button
                        onClick={() => handleOpenEditModal(team)}
                        title="Edit Team"
                        className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-50 rounded-md transition"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    )}
                    {hasPermission('team.delete') && (
                      <button
                        onClick={() => handleDelete(team.id, team.name)}
                        title="Delete Team"
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-md transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="mt-4">
                  <div className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100 mb-1.5">
                    <Building2 className="w-3 h-3" />
                    <span>{team.department_name || 'Department'}</span>
                  </div>
                  <h3 className="font-bold text-base text-slate-900">{team.name}</h3>
                  <p className="text-xs text-slate-500 mt-1 line-clamp-2">{team.description || 'No description provided.'}</p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center gap-2 text-xs text-slate-600">
                  <UserCheck className="w-4 h-4 text-slate-400" />
                  <span>Leader: <strong className="text-slate-800">{team.leader_name || 'Unassigned'}</strong></span>
                </div>
              </div>

              {/* Members Button and Count */}
              <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-600">
                  {team.members_count} {team.members_count === 1 ? 'Member' : 'Members'}
                </span>
                <button
                  onClick={() => handleOpenMembersModal(team)}
                  className="font-semibold text-indigo-600 hover:text-indigo-700 hover:underline flex items-center gap-1"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Manage Members</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Team Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-md rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-lg font-bold text-slate-900">
                {editingTeam ? 'Edit Team' : 'Create Team'}
              </h2>
              <button onClick={() => setModalOpen(false)} className="text-slate-400 hover:text-slate-600 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {modalError}
              </div>
            )}

            <form onSubmit={handleModalSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Department *
                </label>
                <select
                  required
                  value={formData.department_id}
                  onChange={(e) => setFormData({ ...formData, department_id: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Select Department --</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Team Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Frontend Team, QA Team"
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Description
                </label>
                <textarea
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Team responsibilities..."
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                ></textarea>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Team Leader
                </label>
                <select
                  value={formData.team_leader_id}
                  onChange={(e) => setFormData({ ...formData, team_leader_id: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Unassigned --</option>
                  {members.map((m) => (
                    <option key={m.user_id} value={m.user_id}>
                      {m.name} ({m.email}) - {m.role_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="pt-3 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-lg transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalSubmitting}
                  className="px-4 py-2 text-sm font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-sm transition disabled:opacity-60"
                >
                  {modalSubmitting ? 'Saving...' : editingTeam ? 'Save Changes' : 'Create Team'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Manage Team Members Modal */}
      {membersModalOpen && activeTeamForMembers && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white w-full max-w-lg rounded-2xl shadow-xl border border-slate-100 overflow-hidden flex flex-col max-h-[85vh]">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">
                  {activeTeamForMembers.name} — Members
                </h2>
                <p className="text-xs text-slate-500">Manage members assigned to this team</p>
              </div>
              <button onClick={() => setMembersModalOpen(false)} className="text-slate-400 hover:text-slate-600 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            {teamMembersError && (
              <div className="mx-6 mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {teamMembersError}
              </div>
            )}

            {/* Add Member Form */}
            {hasPermission('team.assign') && (
              <form onSubmit={handleAddMemberToTeam} className="p-6 pb-2 border-b border-slate-100 flex gap-2">
                <select
                  required
                  value={selectedUserToAdd}
                  onChange={(e) => setSelectedUserToAdd(e.target.value)}
                  className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">-- Select Member to Add --</option>
                  {members
                    .filter((m) => !teamMemberList.some((tm) => tm.user_id === m.user_id))
                    .map((m) => (
                      <option key={m.user_id} value={m.user_id}>
                        {m.name} ({m.email}) - {m.role_name}
                      </option>
                    ))}
                </select>
                <button
                  type="submit"
                  disabled={!selectedUserToAdd}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-semibold transition disabled:opacity-50 flex items-center gap-1"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Add</span>
                </button>
              </form>
            )}

            {/* Members List */}
            <div className="p-6 overflow-y-auto flex-1 divide-y divide-slate-100">
              {teamMembersLoading ? (
                <div className="text-center py-8 text-slate-400 text-sm">Loading team members...</div>
              ) : teamMemberList.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-sm">No members in this team yet.</div>
              ) : (
                teamMemberList.map((tm) => (
                  <div key={tm.id} className="py-3 flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{tm.user_name}</p>
                      <p className="text-xs text-slate-500">{tm.user_email}</p>
                    </div>
                    {hasPermission('team.assign') && (
                      <button
                        onClick={() => handleRemoveMemberFromTeam(tm.user_id)}
                        title="Remove member from team"
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition"
                      >
                        <UserMinus className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
              <button
                type="button"
                onClick={() => setMembersModalOpen(false)}
                className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-200 rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

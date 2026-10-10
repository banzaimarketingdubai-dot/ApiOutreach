import React, { useState, useEffect } from 'react';
import { Shield, UserPlus, Mail, ShieldAlert, Trash2, ShieldCheck, User } from 'lucide-react';
import { fetchUsers, updateUserRole, inviteUser, deleteUser } from '../services/api';

export default function UserManagementDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('OPERATOR');
  const [inviting, setInviting] = useState(false);
  const [error, setError] = useState(null);
  
  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await fetchUsers();
      setUsers(data);
      setError(null);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки пользователей');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleRoleChange = async (userId, newRole) => {
    try {
      await updateUserRole(userId, newRole);
      setUsers(users.map(u => u.id === userId ? { ...u, role: newRole } : u));
    } catch (err) {
      alert(err.message || 'Ошибка изменения роли');
    }
  };

  const handleDelete = async (userId) => {
    if (!window.confirm('Вы уверены, что хотите безвозвратно удалить этого пользователя?')) return;
    try {
      await deleteUser(userId);
      setUsers(users.filter(u => u.id !== userId));
    } catch (err) {
      alert(err.message || 'Ошибка удаления пользователя');
    }
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail) return;
    setInviting(true);
    try {
      await inviteUser(inviteEmail, inviteRole);
      setInviteEmail('');
      loadUsers();
    } catch (err) {
      alert(err.message || 'Ошибка приглашения');
    } finally {
      setInviting(false);
    }
  };

  const getRoleBadge = (role) => {
    switch (role) {
      case 'SUPER_ADMIN':
        return <span className="px-2 py-1 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded text-xs font-semibold flex items-center gap-1"><ShieldAlert className="w-3 h-3"/> Super Admin</span>;
      case 'ADMIN':
        return <span className="px-2 py-1 bg-violet-500/20 text-violet-400 border border-violet-500/30 rounded text-xs font-semibold flex items-center gap-1"><ShieldCheck className="w-3 h-3"/> Admin</span>;
      case 'OPERATOR':
        return <span className="px-2 py-1 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded text-xs font-semibold flex items-center gap-1"><User className="w-3 h-3"/> Operator</span>;
      default:
        return <span className="px-2 py-1 bg-slate-500/20 text-slate-400 border border-slate-500/30 rounded text-xs font-semibold">{role}</span>;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in pb-12">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
            <Shield className="w-6 h-6 text-violet-500" />
            Команда и Доступы
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Управление ролями и приглашение новых сотрудников (доступно только для SUPER_ADMIN)
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Column - Invite Form */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 to-teal-500"></div>
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <UserPlus className="w-4 h-4 text-emerald-400" />
              Пригласить сотрудника
            </h3>
            
            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    type="email"
                    required
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-sm text-white placeholder-slate-600 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all"
                    placeholder="colleague@company.com"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Роль</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 outline-none transition-all"
                >
                  <option value="OPERATOR">Operator (Чтение и работа с лидами)</option>
                  <option value="ADMIN">Admin (Настройка кампаний)</option>
                  <option value="SUPER_ADMIN">Super Admin (Полный доступ)</option>
                </select>
              </div>
              
              <button
                type="submit"
                disabled={inviting || !inviteEmail}
                className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 text-white font-medium py-2 rounded-xl transition-colors flex justify-center items-center gap-2 text-sm"
              >
                {inviting ? 'Отправка...' : 'Пригласить'}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column - Users List */}
        <div className="lg:col-span-3">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
            {error && (
              <div className="p-4 bg-rose-500/10 text-rose-400 text-sm border-b border-rose-500/20">
                {error}
              </div>
            )}
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead className="bg-slate-950/50 text-slate-400 text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4 font-medium">Сотрудник</th>
                    <th className="px-6 py-4 font-medium">Роль</th>
                    <th className="px-6 py-4 font-medium">Дата регистрации</th>
                    <th className="px-6 py-4 font-medium text-right">Действия</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {loading ? (
                    <tr>
                      <td colSpan="4" className="px-6 py-8 text-center text-slate-500">Загрузка...</td>
                    </tr>
                  ) : users.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="px-6 py-8 text-center text-slate-500">Пользователи не найдены.</td>
                    </tr>
                  ) : (
                    users.map(u => (
                      <tr key={u.id} className="hover:bg-slate-800/20 transition-colors">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold shrink-0 shadow-inner">
                              {(u.full_name || u.email).charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-medium text-slate-200">{u.full_name || 'Без имени'}</div>
                              <div className="text-xs text-slate-500">{u.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          {getRoleBadge(u.role)}
                        </td>
                        <td className="px-6 py-4 text-slate-400">
                          {new Date(u.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <select
                              value={u.role}
                              onChange={(e) => handleRoleChange(u.id, e.target.value)}
                              className="bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 text-xs text-slate-300 focus:border-violet-500 focus:ring-1 focus:ring-violet-500 outline-none transition-all cursor-pointer hover:border-slate-700"
                            >
                              <option value="OPERATOR">Operator</option>
                              <option value="ADMIN">Admin</option>
                              <option value="SUPER_ADMIN">Super Admin</option>
                            </select>
                            
                            <button
                              onClick={() => handleDelete(u.id)}
                              className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-400/10 rounded-lg transition-colors"
                              title="Удалить пользователя"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

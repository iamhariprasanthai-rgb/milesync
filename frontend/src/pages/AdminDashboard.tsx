import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { User } from '../types/user';

interface UserAdminView extends User {
    token_limit: number;
    tokens_used: number;
    quota_reset_at: string | null;
}

interface SystemPrompt {
    id: number;
    key: string;
    description: string;
    content: string;
    updated_at: string;
}

export default function AdminDashboard() {
    const [activeTab, setActiveTab] = useState<'users' | 'prompts'>('users');
    const [users, setUsers] = useState<UserAdminView[]>([]);
    const [prompts, setPrompts] = useState<SystemPrompt[]>([]);
    const [loading, setLoading] = useState(true);

    // User editing state
    const [editingUser, setEditingUser] = useState<UserAdminView | null>(null);
    const [newQuota, setNewQuota] = useState<number>(0);

    // Prompt editing state
    const [editingPrompt, setEditingPrompt] = useState<SystemPrompt | null>(null);
    const [newPromptContent, setNewPromptContent] = useState('');

    useEffect(() => {
        fetchData();
    }, [activeTab]);

    async function fetchData() {
        setLoading(true);
        try {
            if (activeTab === 'users') {
                const response = await api.get('/api/admin/users');
                setUsers(response.data);
            } else {
                const response = await api.get('/api/admin/prompts');
                setPrompts(response.data);
            }
        } catch (err) {
            console.error('Failed to fetch data:', err);
        } finally {
            setLoading(false);
        }
    }

    async function toggleStatus(user: UserAdminView) {
        try {
            const response = await api.put(`/api/admin/users/${user.id}`, {
                is_active: !user.is_active
            });
            setUsers(users.map(u => u.id === user.id ? { ...u, is_active: response.data.is_active } : u));
        } catch (err) {
            console.error('Failed to update status:', err);
        }
    }

    async function updateRole(user: UserAdminView, isSuperuser: boolean) {
        try {
            const response = await api.put(`/api/admin/users/${user.id}`, {
                is_superuser: isSuperuser
            });
            setUsers(users.map(u => u.id === user.id ? { ...u, is_superuser: response.data.is_superuser } : u));
        } catch (err) {
            console.error('Failed to update role:', err);
        }
    }

    async function updateQuota() {
        if (!editingUser) return;
        try {
            const response = await api.put(`/api/admin/users/${editingUser.id}`, {
                token_limit: newQuota
            });
            setUsers(users.map(u => u.id === editingUser.id ? { ...u, token_limit: response.data.token_limit } : u));
            setEditingUser(null);
        } catch (err) {
            console.error('Failed to update quota:', err);
        }
    }

    async function savePrompt() {
        if (!editingPrompt) return;
        try {
            const response = await api.put(`/api/admin/prompts/${editingPrompt.key}`, {
                content: newPromptContent
            });
            setPrompts(prompts.map(p => p.key === editingPrompt.key ? response.data : p));
            setEditingPrompt(null);
        } catch (err) {
            console.error('Failed to update prompt:', err);
        }
    }

    if (loading && users.length === 0 && prompts.length === 0) return <div className="p-8">Loading...</div>;

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>

            {/* Tabs */}
            <div className="border-b border-gray-200 mb-6">
                <nav className="-mb-px flex space-x-8">
                    <button
                        onClick={() => setActiveTab('users')}
                        className={`${activeTab === 'users'
                                ? 'border-primary-500 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                    >
                        User Management
                    </button>
                    <button
                        onClick={() => setActiveTab('prompts')}
                        className={`${activeTab === 'prompts'
                                ? 'border-primary-500 text-primary-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm`}
                    >
                        System Prompts
                    </button>
                </nav>
            </div>

            {activeTab === 'users' ? (
                /* User Table */
                <div className="bg-white shadow-sm rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Quota Usage</th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {users.map((user) => (
                                <tr key={user.id}>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <div className="flex-shrink-0 h-10 w-10">
                                                <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold">
                                                    {user.name[0]}
                                                </div>
                                            </div>
                                            <div className="ml-4">
                                                <div className="text-sm font-medium text-gray-900">{user.name}</div>
                                                <div className="text-sm text-gray-500">{user.email}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                            {user.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        <select
                                            value={user.is_superuser ? 'admin' : 'user'}
                                            onChange={(e) => updateRole(user, e.target.value === 'admin')}
                                            className="text-sm border-gray-300 rounded-md shadow-sm focus:border-primary-500 focus:ring-primary-500 p-1"
                                        >
                                            <option value="user">User</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-900">{user.tokens_used.toLocaleString()} / {user.token_limit.toLocaleString()}</div>
                                        <div className="w-full bg-gray-200 rounded-full h-1.5 mt-1">
                                            <div className="bg-primary-600 h-1.5 rounded-full" style={{ width: `${Math.min((user.tokens_used / user.token_limit) * 100, 100)}%` }}></div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button onClick={() => toggleStatus(user)} className={`text-${user.is_active ? 'red' : 'green'}-600 hover:text-${user.is_active ? 'red' : 'green'}-900 mr-4`}>
                                            {user.is_active ? 'Deactivate' : 'Activate'}
                                        </button>
                                        <button onClick={() => { setEditingUser(user); setNewQuota(user.token_limit); }} className="text-primary-600 hover:text-primary-900">
                                            Edit Quota
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                /* System Prompts List */
                <div className="space-y-6">
                    {prompts.map((prompt) => (
                        <div key={prompt.id} className="bg-white shadow-sm rounded-lg p-6">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-lg font-medium text-gray-900">{prompt.key}</h3>
                                    <p className="text-sm text-gray-500">{prompt.description}</p>
                                </div>
                                <button
                                    onClick={() => {
                                        setEditingPrompt(prompt);
                                        setNewPromptContent(prompt.content);
                                    }}
                                    className="text-primary-600 hover:text-primary-900 text-sm font-medium"
                                >
                                    Edit Prompt
                                </button>
                            </div>
                            <div className="bg-gray-50 rounded p-4">
                                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono">
                                    {prompt.content}
                                </pre>
                            </div>
                            <div className="mt-2 text-xs text-gray-400">
                                Last updated: {new Date(prompt.updated_at).toLocaleString()}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Edit Quota Modal */}
            {editingUser && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
                    <div className="bg-white p-5 rounded-lg shadow-xl w-96">
                        <h3 className="text-lg font-medium mb-4">Edit Quota for {editingUser.name}</h3>
                        <input
                            type="number"
                            value={newQuota}
                            onChange={(e) => setNewQuota(Number(e.target.value))}
                            className="w-full border rounded px-3 py-2 mb-4"
                        />
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setEditingUser(null)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">Cancel</button>
                            <button onClick={updateQuota} className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700">Save</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Edit Prompt Modal */}
            {editingPrompt && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
                    <div className="bg-white p-6 rounded-lg shadow-xl w-3/4 max-w-4xl">
                        <h3 className="text-lg font-medium mb-2">Edit System Prompt: {editingPrompt.key}</h3>
                        <p className="text-sm text-gray-500 mb-4">{editingPrompt.description}</p>

                        <textarea
                            value={newPromptContent}
                            onChange={(e) => setNewPromptContent(e.target.value)}
                            className="w-full h-96 border rounded-md p-4 font-mono text-sm mb-4 focus:border-primary-500 focus:ring-primary-500"
                        />

                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setEditingPrompt(null)}
                                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md font-medium"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={savePrompt}
                                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 font-medium"
                            >
                                Save Changes
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

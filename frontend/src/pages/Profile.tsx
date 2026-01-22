import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';

interface QuotaInfo {
  token_limit: number;
  tokens_used: number;
  tokens_remaining: number;
  quota_reset_at: string | null;
  usage_percentage: number;
  was_reset: boolean;
}

export default function Profile() {
  const { user, isLoading, setUser } = useAuth();
  const [name, setName] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [quotaLoading, setQuotaLoading] = useState(true);

  useEffect(() => {
    if (user) {
      setName(user.name);
      setAvatarUrl(user.avatar_url ?? '');
      fetchQuota();
    }
  }, [user]);

  async function fetchQuota() {
    try {
      setQuotaLoading(true);
      const response = await api.get('/api/dashboard/quota');
      setQuota(response.data);
    } catch (err) {
      console.error('Failed to fetch quota:', err);
    } finally {
      setQuotaLoading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await api.put('/api/auth/me', {
        name: name.trim(),
        avatar_url: avatarUrl.trim() || null,
      });
      setUser(response.data);
      setSuccess('Profile updated successfully.');
    } catch (err) {
      console.error('Update profile error:', err);
      setError('Failed to update profile. Please try again.');
    } finally {
      setSaving(false);
    }
  }

  function formatDate(dateString: string | null) {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  }

  function getProgressColor(percentage: number) {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 70) return 'bg-yellow-500';
    return 'bg-green-500';
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Profile</h1>
      <p className="text-gray-600 mb-6">
        Update your basic account information.
      </p>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
          {success}
        </div>
      )}

      {/* Quota Usage Card */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          API Usage
        </h2>
        
        {quotaLoading ? (
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-3 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          </div>
        ) : quota ? (
          <div className="space-y-4">
            {/* Progress Bar */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Token Usage</span>
                <span className="font-medium text-gray-900">{quota.usage_percentage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-300 ${getProgressColor(quota.usage_percentage)}`}
                  style={{ width: `${Math.min(quota.usage_percentage, 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4 pt-2">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Used</p>
                <p className="text-xl font-bold text-gray-900">{quota.tokens_used.toLocaleString()}</p>
                <p className="text-xs text-gray-500">tokens</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 uppercase tracking-wide">Remaining</p>
                <p className="text-xl font-bold text-green-600">{quota.tokens_remaining.toLocaleString()}</p>
                <p className="text-xs text-gray-500">tokens</p>
              </div>
            </div>

            {/* Limit and Reset Info */}
            <div className="flex justify-between text-sm text-gray-500 pt-2 border-t border-gray-100">
              <span>Limit: {quota.token_limit.toLocaleString()} tokens</span>
              <span>Resets: {formatDate(quota.quota_reset_at)}</span>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Unable to load quota information.</p>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 bg-white rounded-xl shadow-sm p-6">
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input
            type="email"
            value={user.email}
            disabled
            className="mt-1 block w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            placeholder="Your name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Avatar URL <span className="text-gray-400 font-normal">(optional)</span>
          </label>
          <input
            type="url"
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            placeholder="https://example.com/avatar.png"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Sign-in method</label>
          <input
            type="text"
            value={user.auth_provider}
            disabled
            className="mt-1 block w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-500"
          />
        </div>

        <div className="flex items-center justify-end gap-3">
          <button
            type="submit"
            disabled={!name.trim() || saving}
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md shadow-sm hover:bg-primary-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save changes'}
          </button>
        </div>
      </form>
    </div>
  );
}

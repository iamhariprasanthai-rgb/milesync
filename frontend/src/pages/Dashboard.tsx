import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import * as dashboardApi from '../api/dashboard';
import * as goalsApi from '../api/goals';
import type { DashboardStats, UpcomingTask, TaskPriority } from '../types/goal';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await dashboardApi.getDashboardStats();
      setStats(data);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard load error:', err);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleTaskToggle(task: UpcomingTask) {
    try {
      await goalsApi.completeTask(task.goal_id, task.id);
      loadDashboardData();
    } catch (err) {
      console.error('Task toggle error:', err);
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600 mb-4">{error || 'Failed to load dashboard'}</p>
          <button
            onClick={loadDashboardData}
            className="text-primary-600 hover:underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Welcome back, {user?.name?.split(' ')[0] || 'there'}!
        </h1>
        <p className="mt-2 text-gray-600">Here's your progress overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <StatCard title="Active Goals" value={stats.active_goals} icon="🎯" color="blue" />
        <StatCard title="Tasks Done" value={stats.completed_tasks} icon="✅" color="green" />
        <StatCard title="Day Streak" value={stats.current_streak} icon="🔥" color="orange" />
        <StatCard title="Completion Rate" value={`${stats.completion_rate}%`} icon="📈" color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Today's Tasks */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Upcoming Tasks</h2>
            <Link to="/goals" className="text-sm text-primary-600 hover:text-primary-700">
              View all
            </Link>
          </div>
          <div className="space-y-3">
            {stats.upcoming_tasks.length > 0 ? (
              stats.upcoming_tasks.map((task) => (
                <TaskItem key={task.id} task={task} onToggle={handleTaskToggle} />
              ))
            ) : (
              <p className="text-gray-500 text-sm text-center py-4">
                No pending tasks. Start a chat to create new goals!
              </p>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <Link
              to="/chat"
              className="flex items-center p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
            >
              <span className="text-2xl mr-4">💬</span>
              <div>
                <p className="font-medium text-gray-900">Start New Goal</p>
                <p className="text-sm text-gray-600">Chat with AI to define your next goal</p>
              </div>
            </Link>
            <Link
              to="/goals"
              className="flex items-center p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
            >
              <span className="text-2xl mr-4">📋</span>
              <div>
                <p className="font-medium text-gray-900">View My Goals</p>
                <p className="text-sm text-gray-600">Track progress on existing goals</p>
              </div>
            </Link>
            <Link
              to="/analytics"
              className="flex items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
            >
              <span className="text-2xl mr-4">📊</span>
              <div>
                <p className="font-medium text-gray-900">AI Analytics</p>
                <p className="text-sm text-gray-600">View coaching quality & performance metrics</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: string | number;
  icon: string;
  color: 'blue' | 'green' | 'orange' | 'purple';
}) {
  const colorClasses = {
    blue: 'bg-primary-50 text-primary-600',
    green: 'bg-green-50 text-green-600',
    orange: 'bg-orange-50 text-orange-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center text-2xl ${colorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

function TaskItem({
  task,
  onToggle
}: {
  task: UpcomingTask;
  onToggle: (task: UpcomingTask) => void;
}) {
  const priorityColors: Record<TaskPriority, string> = {
    high: 'bg-red-100 text-red-700',
    medium: 'bg-yellow-100 text-yellow-700',
    low: 'bg-gray-100 text-gray-600',
  };

  function formatDueDate(dateStr: string | null): string {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) return 'Today';
    if (date.toDateString() === tomorrow.toDateString()) return 'Tomorrow';
    return date.toLocaleDateString();
  }

  return (
    <div
      className="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
      onClick={() => onToggle(task)}
    >
      <input
        type="checkbox"
        className="w-5 h-5 text-primary-600 rounded border-gray-300 focus:ring-primary-500 cursor-pointer"
        onChange={() => { }}
      />
      <div className="ml-3 flex-1">
        <p className="text-sm font-medium text-gray-900">{task.title}</p>
        <Link
          to={`/goals/${task.goal_id}`}
          className="text-xs text-primary-600 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {task.goal_title}
        </Link>
      </div>
      <div className="flex items-center gap-2">
        {task.priority !== 'medium' && (
          <span className={`text-xs px-2 py-0.5 rounded ${priorityColors[task.priority]}`}>
            {task.priority}
          </span>
        )}
        {task.due_date && (
          <span className="text-xs text-gray-500">{formatDueDate(task.due_date)}</span>
        )}
      </div>
    </div>
  );
}

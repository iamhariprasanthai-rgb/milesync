import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { GoalListItem, GoalCategory } from '../types/goal';
import * as goalsApi from '../api/goals';

export default function Goals() {
  const [goals, setGoals] = useState<GoalListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadGoals();
  }, []);

  async function loadGoals() {
    setIsLoading(true);
    setError(null);
    try {
      const data = await goalsApi.listGoals();
      setGoals(data);
    } catch (err) {
      setError('Failed to load goals. Please try again.');
      console.error('Load goals error:', err);
    } finally {
      setIsLoading(false);
    }
  }

  const activeGoals = goals.filter((g) => g.status === 'active');
  const completedGoals = goals.filter((g) => g.status === 'completed');
  const otherGoals = goals.filter((g) => g.status !== 'active' && g.status !== 'completed');

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Goals</h1>
          <p className="mt-2 text-gray-600">Track and manage your goals</p>
        </div>
        <Link
          to="/chat"
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
        >
          + New Goal
        </Link>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadGoals}
            className="mt-2 text-sm text-red-700 underline hover:no-underline"
          >
            Try again
          </button>
        </div>
      )}

      {/* Active Goals */}
      {activeGoals.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Active Goals ({activeGoals.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {activeGoals.map((goal) => (
              <GoalCard key={goal.id} goal={goal} />
            ))}
          </div>
        </section>
      )}

      {/* Other Goals (Paused, Abandoned) */}
      {otherGoals.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Other Goals</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {otherGoals.map((goal) => (
              <GoalCard key={goal.id} goal={goal} />
            ))}
          </div>
        </section>
      )}

      {/* Completed Goals */}
      {completedGoals.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Completed Goals ({completedGoals.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {completedGoals.map((goal) => (
              <GoalCard key={goal.id} goal={goal} />
            ))}
          </div>
        </section>
      )}

      {/* Empty State */}
      {goals.length === 0 && !error && (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">Target</div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No goals yet</h3>
          <p className="text-gray-600 mb-6">
            Start by chatting with your AI coach to define your first goal
          </p>
          <Link
            to="/chat"
            className="inline-block px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Create Your First Goal
          </Link>
        </div>
      )}
    </div>
  );
}

function GoalCard({ goal }: { goal: GoalListItem }) {
  const categoryEmoji: Record<GoalCategory, string> = {
    health: 'Fitness',
    education: 'Books',
    finance: 'Money',
    career: 'Briefcase',
    personal: 'Star',
    other: 'Target',
  };

  const categoryLabels: Record<GoalCategory, string> = {
    health: 'Health',
    education: 'Education',
    finance: 'Finance',
    career: 'Career',
    personal: 'Personal',
    other: 'Other',
  };

  const statusColors: Record<string, string> = {
    active: 'bg-primary-100 text-primary-700',
    completed: 'bg-green-100 text-green-700',
    paused: 'bg-yellow-100 text-yellow-700',
    abandoned: 'bg-gray-100 text-gray-700',
  };

  return (
    <Link
      to={`/goals/${goal.id}`}
      className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow block"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-gray-500">
            {categoryLabels[goal.category]}
          </span>
        </div>
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[goal.status]}`}
        >
          {goal.status.charAt(0).toUpperCase() + goal.status.slice(1)}
        </span>
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{goal.title}</h3>
      {goal.description && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-2">{goal.description}</p>
      )}

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">Progress</span>
          <span className="font-medium text-gray-900">{goal.progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${goal.status === 'completed' ? 'bg-green-500' : 'bg-primary-600'
              }`}
            style={{ width: `${goal.progress}%` }}
          />
        </div>
      </div>

      {/* Stats */}
      <div className="flex justify-between text-xs text-gray-500">
        <span>
          {goal.completed_task_count}/{goal.task_count} tasks
        </span>
        <span>{goal.milestone_count} milestones</span>
      </div>

      {goal.target_date && (
        <p className="text-xs text-gray-500 mt-2">
          Target: {new Date(goal.target_date).toLocaleDateString()}
        </p>
      )}
    </Link>
  );
}

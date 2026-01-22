import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import type {
  GoalWithMilestones,
  Milestone,
  Task,
  GoalCategory,
  TaskPriority,
  TaskCreate,
  MilestoneCreate,
  TaskUpdate,
  MilestoneUpdate,
} from '../types/goal';
import * as goalsApi from '../api/goals';

export default function GoalDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [goal, setGoal] = useState<GoalWithMilestones | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadGoal(parseInt(id));
    }
  }, [id]);

  async function loadGoal(goalId: number) {
    setIsLoading(true);
    setError(null);
    try {
      const data = await goalsApi.getGoal(goalId);
      setGoal(data);
    } catch (err) {
      setError('Failed to load goal. Please try again.');
      console.error('Load goal error:', err);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleTaskToggle(task: Task) {
    if (!goal) return;

    try {
      if (task.status === 'completed') {
        await goalsApi.uncompleteTask(goal.id, task.id);
      } else {
        await goalsApi.completeTask(goal.id, task.id);
      }
      // Reload goal to get updated progress
      loadGoal(goal.id);
    } catch (err) {
      console.error('Toggle task error:', err);
    }
  }

  async function handleDeleteGoal() {
    if (!goal) return;

    if (!window.confirm('Are you sure you want to delete this goal? This action cannot be undone.')) {
      return;
    }

    try {
      await goalsApi.deleteGoal(goal.id);
      navigate('/goals');
    } catch (err) {
      console.error('Delete goal error:', err);
      setError('Failed to delete goal. Please try again.');
    }
  }

  async function handleAddMilestone(data: MilestoneCreate) {
    if (!goal) return;

    try {
      await goalsApi.createMilestone(goal.id, data);
      loadGoal(goal.id);
    } catch (err) {
      console.error('Add milestone error:', err);
    }
  }

  async function handleDeleteMilestone(milestoneId: number) {
    if (!goal) return;

    if (!window.confirm('Delete this milestone and all its tasks?')) {
      return;
    }

    try {
      await goalsApi.deleteMilestone(goal.id, milestoneId);
      loadGoal(goal.id);
    } catch (err) {
      console.error('Delete milestone error:', err);
    }
  }

  async function handleAddTask(milestoneId: number, data: TaskCreate) {
    if (!goal) return;

    try {
      await goalsApi.createTask(goal.id, milestoneId, data);
      loadGoal(goal.id);
    } catch (err) {
      console.error('Add task error:', err);
    }
  }

  async function handleDeleteTask(taskId: number) {
    if (!goal) return;

    try {
      await goalsApi.deleteTask(goal.id, taskId);
      loadGoal(goal.id);
    } catch (err) {
      console.error('Delete task error:', err);
    }
  }

  async function handleUpdateTask(taskId: number, data: TaskUpdate) {
    if (!goal) return;

    try {
      await goalsApi.updateTask(goal.id, taskId, data);
      await loadGoal(goal.id);
    } catch (err) {
      console.error('Update task error:', err);
    }
  }

  async function handleUpdateMilestone(milestoneId: number, data: MilestoneUpdate) {
    if (!goal) return;

    try {
      await goalsApi.updateMilestone(goal.id, milestoneId, data);
      await loadGoal(goal.id);
    } catch (err) {
      console.error('Update milestone error:', err);
    }
  }

  const categoryLabels: Record<GoalCategory, string> = {
    health: 'Health',
    education: 'Education',
    finance: 'Finance',
    career: 'Career',
    personal: 'Personal',
    other: 'Other',
  };

  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-700',
    completed: 'bg-green-100 text-green-700',
    paused: 'bg-yellow-100 text-yellow-700',
    abandoned: 'bg-gray-100 text-gray-700',
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-center py-16">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      </div>
    );
  }

  if (error || !goal) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link to="/goals" className="text-primary-600 hover:text-primary-700 text-sm mb-4 inline-block">
          Back to Goals
        </Link>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600 mb-4">{error || 'Goal not found'}</p>
          <Link
            to="/goals"
            className="text-primary-600 hover:underline"
          >
            Return to Goals
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Link */}
      <Link to="/goals" className="text-primary-600 hover:text-primary-700 text-sm mb-4 inline-block">
        Back to Goals
      </Link>

      {/* Goal Header */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-medium text-gray-500">
                {categoryLabels[goal.category]}
              </span>
              <span
                className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[goal.status]}`}
              >
                {goal.status.charAt(0).toUpperCase() + goal.status.slice(1)}
              </span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">{goal.title}</h1>
            {goal.description && (
              <p className="text-gray-600 mt-2">{goal.description}</p>
            )}
          </div>
          <button
            onClick={handleDeleteGoal}
            className="text-red-600 hover:text-red-700 text-sm"
          >
            Delete
          </button>
        </div>

        {/* Progress */}
        <div className="mt-6">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-gray-600">Overall Progress</span>
            <span className="font-semibold text-gray-900">{goal.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all ${goal.status === 'completed' ? 'bg-green-500' : 'bg-primary-600'
                }`}
              style={{ width: `${goal.progress}%` }}
            />
          </div>
        </div>

        {/* Meta */}
        <div className="mt-6 flex flex-wrap gap-6 text-sm text-gray-600">
          {goal.target_date && (
            <div>
              <span className="font-medium">Target:</span>{' '}
              {new Date(goal.target_date).toLocaleDateString()}
            </div>
          )}
          <div>
            <span className="font-medium">Started:</span>{' '}
            {new Date(goal.created_at).toLocaleDateString()}
          </div>
          <div>
            <span className="font-medium">Milestones:</span> {goal.milestones.length}
          </div>
        </div>
      </div>

      {/* Roadmap */}
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900">Roadmap</h2>
        <AddMilestoneButton onAdd={handleAddMilestone} />
      </div>
      {goal.milestones.length > 0 ? (
        <div className="space-y-4">
          {goal.milestones.map((milestone, index) => (
            <MilestoneCard
              key={milestone.id}
              milestone={milestone}
              index={index}
              onTaskToggle={handleTaskToggle}
              onDeleteMilestone={handleDeleteMilestone}
              onAddTask={handleAddTask}
              onDeleteTask={handleDeleteTask}
              onUpdateTask={handleUpdateTask}
              onUpdateMilestone={handleUpdateMilestone}
            />
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm p-6 text-center text-gray-500">
          No milestones yet. Click "Add Milestone" to create one.
        </div>
      )}
    </div>
  );
}

interface MilestoneCardProps {
  milestone: Milestone;
  index: number;
  onTaskToggle: (task: Task) => void;
  onDeleteMilestone: (milestoneId: number) => void;
  onAddTask: (milestoneId: number, data: TaskCreate) => void;
  onDeleteTask: (taskId: number) => void;
  onUpdateTask: (taskId: number, data: TaskUpdate) => Promise<void> | void;
  onUpdateMilestone: (milestoneId: number, data: MilestoneUpdate) => Promise<void> | void;
}

function MilestoneCard({
  milestone,
  index,
  onTaskToggle,
  onDeleteMilestone,
  onAddTask,
  onDeleteTask,
  onUpdateTask,
  onUpdateMilestone,
}: MilestoneCardProps) {
  const [showAddTask, setShowAddTask] = useState(false);
  const [isEditingMilestone, setIsEditingMilestone] = useState(false);
  const [milestoneTitle, setMilestoneTitle] = useState(milestone.title);
  const [milestoneDescription, setMilestoneDescription] = useState(milestone.description ?? '');
  const completedTasks = milestone.tasks.filter((t) => t.status === 'completed').length;
  const totalTasks = milestone.tasks.length;

  async function handleMilestoneSave(e: React.FormEvent) {
    e.preventDefault();
    if (!milestoneTitle.trim()) return;

    await onUpdateMilestone(milestone.id, {
      title: milestoneTitle.trim(),
      description: milestoneDescription.trim() || undefined,
    });
    setIsEditingMilestone(false);
  }

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      {/* Milestone Header */}
      <div className={`p-4 ${milestone.is_completed ? 'bg-green-50' : 'bg-gray-50'}`}>
        <div className="flex items-center">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 text-sm font-medium ${milestone.is_completed
                ? 'bg-green-500 text-white'
                : 'bg-gray-300 text-gray-600'
              }`}
          >
            {milestone.is_completed ? '✓' : index + 1}
          </div>
          <div className="flex-1">
            {isEditingMilestone ? (
              <form onSubmit={handleMilestoneSave} className="space-y-2">
                <input
                  type="text"
                  value={milestoneTitle}
                  onChange={(e) => setMilestoneTitle(e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Milestone title"
                  autoFocus
                />
                <textarea
                  value={milestoneDescription}
                  onChange={(e) => setMilestoneDescription(e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="Description (optional)"
                  rows={2}
                />
                <div className="flex items-center gap-2">
                  <button
                    type="submit"
                    disabled={!milestoneTitle.trim()}
                    className="px-3 py-1 text-xs bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
                  >
                    Save
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditingMilestone(false);
                      setMilestoneTitle(milestone.title);
                      setMilestoneDescription(milestone.description ?? '');
                    }}
                    className="px-3 py-1 text-xs text-gray-600 hover:text-gray-800"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <>
                <h3 className="font-semibold text-gray-900">{milestone.title}</h3>
                {milestone.description && (
                  <p className="text-sm text-gray-600">{milestone.description}</p>
                )}
              </>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              {milestone.target_date && (
                <span className="text-sm text-gray-500 block">
                  {new Date(milestone.target_date).toLocaleDateString()}
                </span>
              )}
              <span className="text-xs text-gray-400">
                {completedTasks}/{totalTasks} tasks
              </span>
            </div>
            <button
              onClick={() => setIsEditingMilestone((prev) => !prev)}
              className="text-gray-400 hover:text-primary-600 p-1"
              title="Edit milestone"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"
                />
              </svg>
            </button>
            <button
              onClick={() => onDeleteMilestone(milestone.id)}
              className="text-gray-400 hover:text-red-600 p-1"
              title="Delete milestone"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Tasks */}
      <div className="p-4 space-y-2">
        {milestone.tasks.map((task) => (
          <TaskRow
            key={task.id}
            task={task}
            onTaskToggle={onTaskToggle}
            onDeleteTask={onDeleteTask}
            onUpdateTask={onUpdateTask}
          />
        ))}

        {/* Add Task Form */}
        {showAddTask ? (
          <AddTaskForm
            onSubmit={(data) => {
              onAddTask(milestone.id, data);
              setShowAddTask(false);
            }}
            onCancel={() => setShowAddTask(false)}
          />
        ) : (
          <button
            onClick={() => setShowAddTask(true)}
            className="w-full py-2 text-sm text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded flex items-center justify-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Task
          </button>
        )}
      </div>
    </div>
  );
}

interface TaskRowProps {
  task: Task;
  onTaskToggle: (task: Task) => void;
  onDeleteTask: (taskId: number) => void;
  onUpdateTask: (taskId: number, data: TaskUpdate) => Promise<void> | void;
}

function TaskRow({ task, onTaskToggle, onDeleteTask, onUpdateTask }: TaskRowProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(task.title);
  const [description, setDescription] = useState(task.description ?? '');
  const [priority, setPriority] = useState<TaskPriority>(task.priority);
  const [isSaving, setIsSaving] = useState(false);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setIsSaving(true);
    try {
      await onUpdateTask(task.id, {
        title: title.trim(),
        description: description.trim() || undefined,
        priority,
      });
      setIsEditing(false);
    } finally {
      setIsSaving(false);
    }
  }

  function handleCancel() {
    setIsEditing(false);
    setTitle(task.title);
    setDescription(task.description ?? '');
    setPriority(task.priority);
  }

  if (isEditing) {
    return (
      <form
        onSubmit={handleSave}
        className="flex flex-col md:flex-row items-stretch md:items-center p-2 gap-2 bg-gray-50 rounded"
      >
        <div className="flex items-center md:w-1/2">
          <input
            type="checkbox"
            checked={task.status === 'completed'}
            onChange={() => onTaskToggle(task)}
            className="w-4 h-4 text-primary-600 rounded border-gray-300 cursor-pointer"
          />
          <div className="ml-3 flex-1">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Task title"
              autoFocus
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full mt-1 px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Description (optional)"
              rows={2}
            />
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 md:w-1/2">
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as TaskPriority)}
            className="px-2 py-1 text-xs border border-gray-300 rounded"
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
          <button
            type="submit"
            disabled={!title.trim() || isSaving}
            className="px-3 py-1 text-xs bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
          >
            Save
          </button>
          <button
            type="button"
            onClick={handleCancel}
            className="px-3 py-1 text-xs text-gray-600 hover:text-gray-800"
          >
            Cancel
          </button>
        </div>
      </form>
    );
  }

  return (
    <div className="flex items-center p-2 hover:bg-gray-50 rounded group">
      <input
        type="checkbox"
        checked={task.status === 'completed'}
        onChange={() => onTaskToggle(task)}
        className="w-4 h-4 text-primary-600 rounded border-gray-300 cursor-pointer"
      />
      <div className="ml-3 flex-1">
        <span
          className={`text-sm ${task.status === 'completed' ? 'text-gray-400 line-through' : 'text-gray-700'
            }`}
        >
          {task.title}
        </span>
        {task.description && (
          <p className="text-xs text-gray-500">{task.description}</p>
        )}
      </div>
      <div className="flex items-center gap-2">
        {task.priority !== 'medium' && (
          <span
            className={`text-xs px-2 py-0.5 rounded ${task.priority === 'high'
                ? 'bg-red-100 text-red-700'
                : 'bg-gray-100 text-gray-600'
              }`}
          >
            {task.priority}
          </span>
        )}
        {task.due_date && (
          <span className="text-xs text-gray-500">
            {new Date(task.due_date).toLocaleDateString()}
          </span>
        )}
        <button
          type="button"
          onClick={() => setIsEditing(true)}
          className="text-gray-400 hover:text-primary-600 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
          title="Edit task"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"
            />
          </svg>
        </button>
        <button
          onClick={() => onDeleteTask(task.id)}
          className="text-gray-400 hover:text-red-600 p-1 opacity-0 group-hover:opacity-100 transition-opacity"
          title="Delete task"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}

function AddTaskForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (data: TaskCreate) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('medium');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    onSubmit({ title: title.trim(), priority });
    setTitle('');
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Task title..."
        className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
        autoFocus
      />
      <select
        value={priority}
        onChange={(e) => setPriority(e.target.value as TaskPriority)}
        className="px-2 py-1 text-sm border border-gray-300 rounded"
      >
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
      </select>
      <button
        type="submit"
        disabled={!title.trim()}
        className="px-3 py-1 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50"
      >
        Add
      </button>
      <button
        type="button"
        onClick={onCancel}
        className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
      >
        Cancel
      </button>
    </form>
  );
}

function AddMilestoneButton({ onAdd }: { onAdd: (data: MilestoneCreate) => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    onAdd({
      title: title.trim(),
      description: description.trim() || undefined,
    });
    setTitle('');
    setDescription('');
    setIsOpen(false);
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-1"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        Add Milestone
      </button>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <input
        type="text"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="Milestone title..."
        className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
        autoFocus
      />
      <button
        type="submit"
        disabled={!title.trim()}
        className="px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
      >
        Add
      </button>
      <button
        type="button"
        onClick={() => setIsOpen(false)}
        className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
      >
        Cancel
      </button>
    </form>
  );
}

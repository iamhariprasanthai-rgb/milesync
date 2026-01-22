/**
 * Analytics Dashboard - Opik LLM Observability & Evaluation Metrics
 * 
 * Showcases comprehensive AI performance monitoring including:
 * - Coaching quality evaluation
 * - Goal extraction metrics
 * - User satisfaction tracking
 * - SMART goal alignment scores
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
    getAnalyticsStatus,
    getAIPerformanceSummary,
    getCoachingMetrics,
    type EvaluationMetrics,
    type AIPerformanceSummary,
    type CoachingMetrics,
} from '../api/analytics';

// Score color helper
function getScoreColor(score: number): string {
    if (score >= 0.8) return '#10b981'; // green
    if (score >= 0.6) return '#f59e0b'; // amber
    return '#ef4444'; // red
}

function getScoreLabel(score: number): string {
    if (score >= 0.9) return 'Excellent';
    if (score >= 0.7) return 'Good';
    if (score >= 0.5) return 'Average';
    return 'Needs Improvement';
}

// Circular Progress Component
function CircularProgress({ score, label, size = 120 }: { score: number; label: string; size?: number }) {
    const percentage = Math.round(score * 100);
    const circumference = 2 * Math.PI * 45;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;
    const color = getScoreColor(score);

    return (
        <div className="flex flex-col items-center">
            <svg width={size} height={size} className="transform -rotate-90">
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r="45"
                    fill="none"
                    stroke="rgba(255,255,255,0.1)"
                    strokeWidth="8"
                />
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r="45"
                    fill="none"
                    stroke={color}
                    strokeWidth="8"
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    style={{ transition: 'stroke-dashoffset 0.5s ease' }}
                />
            </svg>
            <div className="absolute flex flex-col items-center justify-center" style={{ width: size, height: size }}>
                <span className="text-2xl font-bold" style={{ color }}>{percentage}%</span>
                <span className="text-xs text-gray-400">{getScoreLabel(score)}</span>
            </div>
            <span className="mt-2 text-sm text-gray-300">{label}</span>
        </div>
    );
}

// Progress Bar Component
function ProgressBar({ label, value, color }: { label: string; value: number; color?: string }) {
    const percentage = Math.round(value * 100);
    const barColor = color || getScoreColor(value);

    return (
        <div className="mb-4">
            <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-300">{label}</span>
                <span className="text-sm font-medium" style={{ color: barColor }}>{percentage}%</span>
            </div>
            <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${percentage}%`, backgroundColor: barColor }}
                />
            </div>
        </div>
    );
}

// Stat Card Component
function StatCard({ title, value, subtitle, icon }: { title: string; value: string | number; subtitle: string; icon: string }) {
    return (
        <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl p-6 border border-gray-700">
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-gray-400 text-sm">{title}</p>
                    <p className="text-3xl font-bold text-white mt-1">{value}</p>
                    <p className="text-gray-500 text-xs mt-1">{subtitle}</p>
                </div>
                <span className="text-3xl">{icon}</span>
            </div>
        </div>
    );
}

// SMART Score Breakdown Component
function SMARTBreakdown({ scores }: { scores: { specific: number; measurable: number; achievable: number; relevant: number; time_bound: number } }) {
    const items = [
        { key: 'Specific', value: scores.specific, description: 'Clear and well-defined goals' },
        { key: 'Measurable', value: scores.measurable, description: 'Quantifiable progress indicators' },
        { key: 'Achievable', value: scores.achievable, description: 'Realistic and attainable targets' },
        { key: 'Relevant', value: scores.relevant, description: 'Aligned with user priorities' },
        { key: 'Time-bound', value: scores.time_bound, description: 'Clear deadlines and milestones' },
    ];

    return (
        <div className="space-y-4">
            {items.map(item => (
                <div key={item.key} className="group">
                    <div className="flex justify-between items-center mb-1">
                        <div>
                            <span className="text-sm font-medium text-white">{item.key}</span>
                            <span className="text-xs text-gray-500 ml-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                {item.description}
                            </span>
                        </div>
                        <span className="text-sm font-bold" style={{ color: getScoreColor(item.value) }}>
                            {Math.round(item.value * 100)}%
                        </span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{
                                width: `${item.value * 100}%`,
                                background: `linear-gradient(90deg, ${getScoreColor(item.value)}, ${getScoreColor(item.value)}dd)`,
                            }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
}

export default function Analytics() {
    const { user } = useAuth();
    const navigate = useNavigate();

    const [status, setStatus] = useState<EvaluationMetrics | null>(null);
    const [performance, setPerformance] = useState<AIPerformanceSummary | null>(null);
    const [metrics, setMetrics] = useState<CoachingMetrics | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }

        async function fetchData() {
            try {
                setLoading(true);
                const [statusData, performanceData, metricsData] = await Promise.all([
                    getAnalyticsStatus(),
                    getAIPerformanceSummary(),
                    getCoachingMetrics(),
                ]);
                setStatus(statusData);
                setPerformance(performanceData);
                setMetrics(metricsData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load analytics');
            } finally {
                setLoading(false);
            }
        }

        fetchData();
    }, [user, navigate]);

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-900 flex items-center justify-center">
                <div className="text-center">
                    <p className="text-red-400 mb-4">{error}</p>
                    <button
                        onClick={() => window.location.reload()}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950">
            {/* Header */}
            <header className="bg-gray-900/80 backdrop-blur-md border-b border-gray-800 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">

                            <div>
                                <h1 className="text-2xl font-bold bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
                                    AI Performance Analytics
                                </h1>
                                <p className="text-gray-400 text-sm">Powered by Opik Observability</p>
                            </div>
                        </div>

                        {/* Opik Status Badge */}
                        <div className={`flex items-center space-x-2 px-4 py-2 rounded-full ${status?.opik_enabled
                            ? 'bg-green-500/10 border border-green-500/30'
                            : 'bg-yellow-500/10 border border-yellow-500/30'
                            }`}>
                            <div className={`w-2 h-2 rounded-full ${status?.opik_enabled ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
                                }`} />
                            <span className={`text-sm ${status?.opik_enabled ? 'text-green-400' : 'text-yellow-400'
                                }`}>
                                {status?.opik_enabled ? 'Opik Connected' : 'Opik Not Configured'}
                            </span>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Key Metrics Grid */}
                <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <StatCard
                        title="Total Conversations"
                        value={performance?.total_conversations || 0}
                        subtitle="AI coaching sessions"
                        icon="💬"
                    />
                    <StatCard
                        title="Goals Created"
                        value={performance?.total_goals_created || 0}
                        subtitle="From AI extraction"
                        icon="🎯"
                    />
                    <StatCard
                        title="Coaching Quality"
                        value={`${Math.round((performance?.avg_coaching_quality || 0) * 100)}%`}
                        subtitle="Average score"
                        icon="⭐"
                    />
                    <StatCard
                        title="User Satisfaction"
                        value={`${Math.round((1 - (performance?.avg_frustration_level || 0)) * 100)}%`}
                        subtitle="Low frustration"
                        icon="😊"
                    />
                </section>

                {/* Main Analytics Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* SMART Goal Alignment */}
                    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 rounded-2xl p-6 border border-gray-700/50 backdrop-blur-sm">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="p-2 bg-orange-500/20 rounded-lg">
                                <span className="text-2xl">📊</span>
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">SMART Goal Alignment</h2>
                                <p className="text-gray-400 text-sm">How well AI helps create SMART goals</p>
                            </div>
                        </div>

                        {metrics && (
                            <SMARTBreakdown scores={metrics.metrics.smart_alignment} />
                        )}
                    </div>

                    {/* Coaching Effectiveness */}
                    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 rounded-2xl p-6 border border-gray-700/50 backdrop-blur-sm">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="p-2 bg-primary-500/20 rounded-lg">
                                <span className="text-2xl">🎓</span>
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">Coaching Effectiveness</h2>
                                <p className="text-gray-400 text-sm">AI coaching quality metrics</p>
                            </div>
                        </div>

                        {metrics && (
                            <div className="space-y-4">
                                <ProgressBar
                                    label="Motivational Quality"
                                    value={metrics.metrics.coaching_effectiveness.motivational_quality}
                                />
                                <ProgressBar
                                    label="Actionability"
                                    value={metrics.metrics.coaching_effectiveness.actionability}
                                />
                                <ProgressBar
                                    label="Clarity"
                                    value={metrics.metrics.coaching_effectiveness.clarity}
                                />
                                <ProgressBar
                                    label="Empathy"
                                    value={metrics.metrics.coaching_effectiveness.empathy}
                                />
                            </div>
                        )}
                    </div>

                    {/* User Engagement */}
                    <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 rounded-2xl p-6 border border-gray-700/50 backdrop-blur-sm">
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="p-2 bg-yellow-500/20 rounded-lg">
                                <span className="text-2xl">📈</span>
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-white">User Engagement</h2>
                                <p className="text-gray-400 text-sm">Interaction and success metrics</p>
                            </div>
                        </div>

                        {metrics && (
                            <div className="space-y-6">
                                <div className="text-center p-4 bg-gray-800/50 rounded-xl">
                                    <p className="text-3xl font-bold text-white">
                                        {metrics.metrics.user_engagement.avg_session_length.toFixed(1)}
                                    </p>
                                    <p className="text-gray-400 text-sm">Avg. messages per session</p>
                                </div>

                                <ProgressBar
                                    label="Goal Completion Rate"
                                    value={metrics.metrics.user_engagement.goal_completion_rate}
                                />
                                <ProgressBar
                                    label="Return User Rate"
                                    value={metrics.metrics.user_engagement.return_user_rate}
                                />
                            </div>
                        )}
                    </div>
                </div>

                {/* Overall Quality Scores */}
                <section className="mt-8 bg-gradient-to-br from-gray-800/50 to-gray-900/50 rounded-2xl p-8 border border-gray-700/50">
                    <h2 className="text-xl font-bold text-white mb-8 text-center">Overall AI Performance Scores</h2>

                    <div className="flex flex-wrap justify-center gap-12">
                        <div className="relative">
                            <CircularProgress
                                score={performance?.avg_coaching_quality || 0}
                                label="Coaching Quality"
                                size={140}
                            />
                        </div>
                        <div className="relative">
                            <CircularProgress
                                score={performance?.avg_goal_extraction_quality || 0}
                                label="Goal Extraction"
                                size={140}
                            />
                        </div>
                        <div className="relative">
                            <CircularProgress
                                score={1 - (performance?.avg_frustration_level || 0)}
                                label="User Satisfaction"
                                size={140}
                            />
                        </div>
                    </div>

                    <div className="mt-8 text-center">
                        <p className="text-gray-400 text-sm">
                            Model: <span className="text-orange-400 font-mono">{performance?.model_version}</span>
                            {' • '}
                            Period: <span className="text-orange-400">{performance?.evaluation_period}</span>
                        </p>
                    </div>
                </section>

                {/* Opik Configuration Info */}
                {!status?.opik_enabled && (
                    <section className="mt-8 bg-gradient-to-r from-yellow-500/10 to-orange-500/10 rounded-2xl p-6 border border-yellow-500/30">
                        <div className="flex items-start space-x-4">
                            <span className="text-3xl">⚙️</span>
                            <div>
                                <h3 className="text-lg font-bold text-yellow-400">Enable Full Observability</h3>
                                <p className="text-gray-300 mt-1">
                                    To enable comprehensive LLM tracing and evaluation with Opik:
                                </p>
                                <ol className="mt-4 space-y-2 text-gray-400 text-sm list-decimal list-inside">
                                    <li>Sign up for free at <a href="https://www.comet.com/opik" target="_blank" rel="noopener noreferrer" className="text-orange-400 hover:text-orange-300 underline">comet.com/opik</a></li>
                                    <li>Create a new project and get your API key</li>
                                    <li>Add <code className="bg-gray-800 px-2 py-1 rounded">OPIK_API_KEY</code> to your <code className="bg-gray-800 px-2 py-1 rounded">.env</code> file</li>
                                    <li>Restart the backend server</li>
                                </ol>
                            </div>
                        </div>
                    </section>
                )}

                {/* Project Info */}
                {status?.opik_enabled && (
                    <section className="mt-8 bg-gradient-to-r from-green-500/10 to-emerald-500/10 rounded-2xl p-6 border border-green-500/30">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                                <span className="text-3xl">✅</span>
                                <div>
                                    <h3 className="text-lg font-bold text-green-400">Opik Connected</h3>
                                    <p className="text-gray-400 text-sm">
                                        Project: <span className="text-green-300">{status.project_name}</span>
                                        {status.workspace && (
                                            <> • Workspace: <span className="text-green-300">{status.workspace}</span></>
                                        )}
                                    </p>
                                </div>
                            </div>
                            <a
                                href="https://www.comet.com/opik"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center space-x-2"
                            >
                                <span>Open Dashboard</span>
                                <span>→</span>
                            </a>
                        </div>
                    </section>
                )}
            </main>
        </div>
    );
}

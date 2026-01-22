import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import * as agentsApi from '../api/agents';
import * as goalsApi from '../api/goals';

interface GoalItem {
    id: number;
    title: string;
}

export default function Insights() {
    const [goals, setGoals] = useState<GoalItem[]>([]);
    const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null);
    const [insights, setInsights] = useState<any>(null);
    const [resources, setResources] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadGoals();
    }, []);

    useEffect(() => {
        if (selectedGoalId) {
            loadInsights(selectedGoalId);
            loadResources(selectedGoalId);
        }
    }, [selectedGoalId]);

    async function loadGoals() {
        setIsLoading(true);
        try {
            const data = await goalsApi.listGoals();
            setGoals(data);
            if (data.length > 0) {
                setSelectedGoalId(data[0].id);
            }
        } catch (err) {
            console.error('Failed to load goals:', err);
        } finally {
            setIsLoading(false);
        }
    }

    async function loadInsights(goalId: number) {
        try {
            const data = await agentsApi.getInsights(goalId);
            setInsights(data);
        } catch (err) {
            console.error('Failed to load insights:', err);
        }
    }

    async function loadResources(goalId: number) {
        try {
            const data = await agentsApi.getResources(goalId);
            setResources(data);
        } catch (err) {
            console.error('Failed to load resources:', err);
        }
    }

    if (isLoading) {
        return (
            <div className="max-w-6xl mx-auto px-4 py-8">
                <div className="flex items-center justify-center py-16">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Insights & Resources</h1>
                <p className="mt-2 text-gray-600">
                    AI-powered analysis of your habits and patterns
                </p>
            </div>

            {goals.length === 0 ? (
                <div className="bg-white rounded-xl shadow-sm p-8 text-center">
                    <div className="text-6xl mb-4">📊</div>
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">No Goals Yet</h2>
                    <p className="text-gray-600 mb-4">Start tracking goals to see your insights!</p>
                    <Link
                        to="/chat"
                        className="inline-flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                    >
                        Create Goal
                    </Link>
                </div>
            ) : (
                <>
                    {/* Goal Selector */}
                    <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
                        <select
                            value={selectedGoalId || ''}
                            onChange={(e) => setSelectedGoalId(Number(e.target.value))}
                            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                        >
                            {goals.map((goal) => (
                                <option key={goal.id} value={goal.id}>{goal.title}</option>
                            ))}
                        </select>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Sustainability Score Card */}
                        {insights && (
                            <div className="bg-gradient-to-br from-yellow-500 to-orange-600 rounded-xl shadow-sm p-6 text-white">
                                <h2 className="text-lg font-semibold mb-4 flex items-center">
                                    <span className="mr-2">🌱</span>
                                    Sustainability Score
                                </h2>
                                <div className="flex items-center justify-center py-4">
                                    <div className="relative">
                                        <svg className="w-32 h-32 transform -rotate-90">
                                            <circle cx="64" cy="64" r="56" stroke="rgba(255,255,255,0.3)" strokeWidth="12" fill="none" />
                                            <circle
                                                cx="64" cy="64" r="56"
                                                stroke="white" strokeWidth="12" fill="none"
                                                strokeDasharray={`${(insights.sustainability_score / 100) * 352} 352`}
                                                strokeLinecap="round"
                                            />
                                        </svg>
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <span className="text-4xl font-bold">{insights.sustainability_score || 0}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex justify-center mt-2">
                                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${insights.burnout_risk === 'LOW' ? 'bg-green-400' :
                                        insights.burnout_risk === 'MEDIUM' ? 'bg-yellow-400 text-yellow-900' : 'bg-red-400'
                                        }`}>
                                        {insights.burnout_risk} Burnout Risk
                                    </span>
                                </div>
                            </div>
                        )}

                        {/* Habit Analysis */}
                        {insights?.habit_analysis && (
                            <div className="bg-white rounded-xl shadow-sm p-6">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                    <span className="mr-2">🔄</span>
                                    Habit Analysis
                                </h2>
                                <div className="grid grid-cols-2 gap-4 mb-4">
                                    <div className="bg-primary-50 rounded-lg p-4 text-center">
                                        <div className="text-3xl font-bold text-primary-600">
                                            {insights.habit_analysis.habit_score || 0}
                                        </div>
                                        <div className="text-sm text-gray-600">Habit Score</div>
                                    </div>
                                    <div className="bg-orange-50 rounded-lg p-4 text-center">
                                        <div className="text-3xl font-bold text-orange-600">
                                            {insights.habit_analysis.days_consistent || 0}
                                        </div>
                                        <div className="text-sm text-gray-600">Days Consistent</div>
                                    </div>
                                </div>
                                {insights.habit_analysis.habit_loops?.length > 0 && (
                                    <div>
                                        <h3 className="font-medium text-gray-700 mb-2">Your Habit Loops</h3>
                                        <div className="space-y-2">
                                            {insights.habit_analysis.habit_loops.map((loop: any, i: number) => (
                                                <div key={i} className="bg-gray-50 rounded-lg p-3">
                                                    <div className="text-sm">
                                                        <span className="font-medium">Routine:</span> {loop.routine}
                                                    </div>
                                                    <div className="text-xs text-gray-500 mt-1">
                                                        Cue: {loop.cue} → Reward: {loop.reward}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Pattern Insights */}
                        {insights?.pattern_insights && (
                            <div className="bg-white rounded-xl shadow-sm p-6">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                    <span className="mr-2">📈</span>
                                    Pattern Insights
                                </h2>
                                <div className="space-y-4">
                                    {insights.pattern_insights.best_days?.length > 0 && (
                                        <div>
                                            <h3 className="text-sm font-medium text-gray-700">Best Days</h3>
                                            <div className="flex flex-wrap gap-2 mt-1">
                                                {insights.pattern_insights.best_days.map((day: string, i: number) => (
                                                    <span key={i} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                                                        {day}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {insights.pattern_insights.best_times?.length > 0 && (
                                        <div>
                                            <h3 className="text-sm font-medium text-gray-700">Best Times</h3>
                                            <div className="flex flex-wrap gap-2 mt-1">
                                                {insights.pattern_insights.best_times.map((time: string, i: number) => (
                                                    <span key={i} className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm">
                                                        {time}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    {insights.pattern_insights.failure_patterns?.length > 0 && (
                                        <div>
                                            <h3 className="text-sm font-medium text-gray-700">Areas to Improve</h3>
                                            <ul className="mt-1 space-y-1">
                                                {insights.pattern_insights.failure_patterns.map((pattern: string, i: number) => (
                                                    <li key={i} className="text-sm text-gray-600 flex items-start">
                                                        <span className="text-yellow-500 mr-2">⚠️</span>
                                                        {pattern}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Recommendations */}
                        {insights?.recommendations?.length > 0 && (
                            <div className="bg-white rounded-xl shadow-sm p-6">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                    <span className="mr-2">💡</span>
                                    AI Recommendations
                                </h2>
                                <div className="space-y-3">
                                    {insights.recommendations.map((rec: string, i: number) => (
                                        <div key={i} className="flex items-start p-3 bg-orange-50 rounded-lg">
                                            <span className="text-orange-500 mr-3 mt-0.5">{i + 1}.</span>
                                            <span className="text-sm text-gray-700">{rec}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Resources */}
                        {resources?.recommended_resources?.length > 0 && (
                            <div className="bg-white rounded-xl shadow-sm p-6 lg:col-span-2">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                                    <span className="mr-2">📚</span>
                                    Recommended Resources
                                </h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {resources.recommended_resources.map((resource: any, i: number) => (
                                        <div key={i} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <span className="text-xs font-medium px-2 py-1 bg-gray-100 rounded text-gray-600">
                                                        {resource.type}
                                                    </span>
                                                    <h3 className="font-medium text-gray-900 mt-2">{resource.name}</h3>
                                                </div>
                                                <span className="text-sm text-gray-500">{resource.cost}</span>
                                            </div>
                                            {resource.time_commitment && (
                                                <p className="text-xs text-gray-500 mt-2">
                                                    ⏱️ {resource.time_commitment}
                                                </p>
                                            )}
                                            {resource.url && (
                                                <a
                                                    href={resource.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="mt-3 inline-block text-sm text-primary-600 hover:text-primary-700"
                                                >
                                                    Learn more →
                                                </a>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </>
            )}
        </div>
    );
}

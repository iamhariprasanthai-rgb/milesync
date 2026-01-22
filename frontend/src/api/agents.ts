/**
 * Agent API client for MileSync multi-agent system.
 */

import { api } from './client';

// Types

export interface AgentInfo {
    type: string;
    name: string;
    description: string;
}

export interface SMARTGoal {
    specific: string;
    measurable: string;
    achievable: string;
    relevant: string;
    time_bound: string;
}

export interface TaskScheduleItem {
    title: string;
    description?: string;
    frequency: 'daily' | 'weekly' | 'monthly' | 'one_time';
    estimated_minutes: number;
    priority: 'low' | 'medium' | 'high';
}

export interface MilestoneOutput {
    id: string;
    title: string;
    description?: string;
    deadline?: string;
    success_criteria: string[];
    tasks: TaskScheduleItem[];
}

export interface DailySummary {
    tasks_completed: number;
    tasks_pending: number;
    streak_count: number;
    completion_rate: number;
}

export interface HabitLoop {
    cue: string;
    routine: string;
    reward: string;
}

export interface HabitAnalysis {
    habit_score: number;
    days_consistent: number;
    habit_loops: HabitLoop[];
}

export interface PatternInsights {
    best_days: string[];
    best_times: string[];
    failure_patterns: string[];
}

export interface EmotionalAssessment {
    motivation_level: number;
    stress_level: number;
    confidence_level: number;
    detected_patterns: string[];
}

export interface Intervention {
    type: string;
    technique: string;
    message: string;
    exercises: string[];
}

export interface Resource {
    type: string;
    name: string;
    url?: string;
    relevance_score: number;
    time_commitment?: string;
    cost: string;
}

// API Functions

export async function getAgentsInfo(): Promise<{ agents: AgentInfo[]; total_agents: number }> {
    const response = await api.get('/api/agents/info');
    return response.data;
}

export async function routeToAgent(
    messages: { role: string; content: string }[],
    goalId?: number,
    sessionId?: number
): Promise<{
    agent_type: string;
    success: boolean;
    message: string;
    data: Record<string, unknown>;
    requires_user_input: boolean;
}> {
    const response = await api.post('/api/agents/route', {
        messages,
        goal_id: goalId,
        session_id: sessionId,
    });
    return response.data;
}

export async function startIntake(
    initialMessage: string,
    sessionId?: number
): Promise<{
    agent_type: string;
    message: string;
    data: Record<string, unknown>;
    requires_user_input: boolean;
}> {
    const response = await api.post('/api/agents/intake', {
        initial_message: initialMessage,
        session_id: sessionId,
    });
    return response.data;
}

export async function generatePlan(
    goalSummary: string,
    goalType: string = 'long_term',
    motivationScore: number = 7,
    feasibilityScore: number = 7,
    obstacles: string[] = []
): Promise<{
    agent_type: string;
    message: string;
    smart_goal: SMARTGoal;
    milestones: MilestoneOutput[];
    task_schedule: {
        daily: TaskScheduleItem[];
        weekly: TaskScheduleItem[];
        monthly: TaskScheduleItem[];
    };
}> {
    const response = await api.post('/api/agents/plan', {
        goal_summary: goalSummary,
        goal_type: goalType,
        motivation_score: motivationScore,
        feasibility_score: feasibilityScore,
        obstacles,
    });
    return response.data;
}

export async function getDailyTasks(goalId?: number): Promise<{
    agent_type: string;
    daily_summary: DailySummary;
    next_actions: string[];
    motivational_message: string;
}> {
    const response = await api.get('/api/agents/daily', {
        params: goalId ? { goal_id: goalId } : {},
    });
    return response.data;
}

export interface ExecutionSummary {
    motivational_message: string;
    next_actions: string[];
}

export interface SustainabilityInsights {
    sustainability_score: number;
    burnout_risk: string;
    recommendations: string[];
}

export interface PsychologicalSupport {
    intervention?: Intervention;
    affirmations: string[];
}

export async function dailyCheckin(
    goalId: number,
    completedTaskIds: number[] = [],
    notes?: string
): Promise<{
    execution: ExecutionSummary;
    sustainability: SustainabilityInsights;
    psychological?: PsychologicalSupport;
}> {
    const response = await api.post('/api/agents/checkin', {
        goal_id: goalId,
        completed_task_ids: completedTaskIds,
        notes,
    });
    return response.data;
}

export async function getInsights(goalId?: number): Promise<{
    agent_type: string;
    habit_analysis: HabitAnalysis;
    pattern_insights: PatternInsights;
    sustainability_score: number;
    burnout_risk: 'LOW' | 'MEDIUM' | 'HIGH';
    recommendations: string[];
}> {
    const response = await api.get('/api/agents/insights', {
        params: goalId ? { goal_id: goalId } : {},
    });
    return response.data;
}

export async function getResources(goalId?: number): Promise<{
    agent_type: string;
    recommended_resources: Resource[];
    integration_suggestions: string[];
    community_matches: string[];
}> {
    const response = await api.get('/api/agents/resources', {
        params: goalId ? { goal_id: goalId } : {},
    });
    return response.data;
}

export async function getMotivationSupport(
    message: string,
    goalId?: number
): Promise<{
    agent_type: string;
    emotional_assessment: EmotionalAssessment;
    intervention?: Intervention;
    affirmations: string[];
    progress_celebration: string;
}> {
    const response = await api.post('/api/agents/motivation', {
        message,
        goal_id: goalId,
    });
    return response.data;
}

export async function runIntakePipeline(initialMessage: string): Promise<{
    foundation: Record<string, unknown>;
    planning: Record<string, unknown>;
}> {
    const response = await api.post('/api/agents/pipeline/intake', {
        initial_message: initialMessage,
    });
    return response.data;
}

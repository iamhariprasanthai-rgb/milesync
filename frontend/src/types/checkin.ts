export interface ExecutionSummary {
    motivational_message: string;
    next_actions: string[];
}

export interface SustainabilityInsights {
    sustainability_score: number;
    burnout_risk: 'LOW' | 'MEDIUM' | 'HIGH';
    recommendations: string[];
}

export interface PsychologicalIntervention {
    technique: string;
    message: string;
    exercises: string[];
}

export interface PsychologicalSupport {
    intervention?: PsychologicalIntervention;
    affirmations: string[];
}

export interface CheckinResponse {
    execution?: ExecutionSummary;
    sustainability?: SustainabilityInsights;
    psychological?: PsychologicalSupport;
}

export interface DailySummaryStats {
    tasks_completed: number;
    tasks_pending: number;
    streak_count: number;
    completion_rate: number;
}

export interface DailySummaryResponse {
    daily_summary: DailySummaryStats;
    motivational_message: string;
}

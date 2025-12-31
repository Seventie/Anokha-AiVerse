// frontend/src/services/roadmapService.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface GenerateRoadmapRequest {
  target_role: string;
  timeline_weeks: number;
  preferences?: Record<string, any>;
}

export interface RoadmapResponse {
  success: boolean;
  roadmap_id: string;
  target_role: string;
  timeline_weeks: number;
  diagram: {
    svg_url: string;
    png_url: string;
  };
  phases: any[];
  learning_path: any[];
  skill_gaps: {
    current: string[];
    missing: string[];
    total_to_learn: number;
  };
  total_tasks: number;
  message?: string;
}

export interface CurrentRoadmapResponse {
  success: boolean;
  has_roadmap: boolean;
  roadmap?: {
    id: string;
    target_role: string;
    timeline_weeks: number;
    current_phase: string;
    overall_progress: number;
    created_at: string;
    diagram: {
      svg_url: string;
      png_url: string;
    };
  };
  statistics?: {
    total_tasks: number;
    completed: number;
    in_progress: number;
    not_started: number;
  };
  tasks_by_phase?: Record<string, any[]>;
  roadmap_data?: any;
  message?: string;
}

export interface UpdateTaskRequest {
  status?: 'not_started' | 'in_progress' | 'completed' | 'skipped';
  progress_percent?: number;
  notes?: string;
}

export interface ScheduleResponse {
  success: boolean;
  scheduled_days: number;
  tasks_scheduled: number;
  calendar_events_created: number;
  notifications: string[];
  weekly_email_scheduled: boolean;
  message: string;
  schedule: any[];
}

interface ApiResponse<T> {
  data?: T;
  error?: string;
}

class RoadmapService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  private getToken(): string | null {
    return localStorage.getItem('access_token') || localStorage.getItem('auth_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const token = this.getToken();

      console.log(`🔵 ${options.method || 'GET'} ${url}`);

      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          ...options.headers,
        },
      });

      console.log(`📊 Response status: ${response.status}`);

      if (!response.ok) {
        let errorMessage = 'Request failed';
        try {
          const errorData = await response.json();
          console.error('❌ Error response:', errorData);
          
          if (response.status === 422 && errorData.detail) {
            if (Array.isArray(errorData.detail)) {
              errorMessage = errorData.detail
                .map((err: any) => `${err.loc.join('.')}: ${err.msg}`)
                .join(', ');
            } else {
              errorMessage = errorData.detail;
            }
          } else {
            errorMessage = errorData.detail || errorData.message || errorMessage;
          }
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        return { error: errorMessage };
      }

      const data = await response.json();
      console.log('✅ Success response:', data);
      return { data };
    } catch (error: any) {
      console.error('❌ Network error:', error);
      return { error: error.message || 'Network error occurred' };
    }
  }

  async generateRoadmap(request: GenerateRoadmapRequest): Promise<ApiResponse<RoadmapResponse>> {
    console.log('🎯 Generating roadmap for:', request.target_role);
    return this.request<RoadmapResponse>('/api/roadmap/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getCurrentRoadmap(): Promise<ApiResponse<CurrentRoadmapResponse>> {
    console.log('📋 Fetching current roadmap...');
    return this.request<CurrentRoadmapResponse>('/api/roadmap/current', {
      method: 'GET',
    });
  }

  async scheduleNext7Days(googleCalendarToken?: string): Promise<ApiResponse<ScheduleResponse>> {
    console.log('📅 Scheduling next 7 days...');
    return this.request<ScheduleResponse>('/api/roadmap/schedule-next-7-days', {
      method: 'POST',
      body: JSON.stringify({
        google_calendar_token: googleCalendarToken || null,
      }),
    });
  }

  async checkDailyProgress(): Promise<ApiResponse<any>> {
    console.log('✅ Checking daily progress...');
    return this.request<any>('/api/roadmap/check-daily-progress', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async checkStreak(): Promise<ApiResponse<any>> {
    console.log('🔥 Checking streak...');
    return this.request<any>('/api/roadmap/check-streak', {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async updateTask(taskId: string, updates: UpdateTaskRequest): Promise<ApiResponse<{ message: string }>> {
    console.log(`✏️ Updating task ${taskId}:`, updates);
    return this.request<{ message: string }>(`/api/roadmap/tasks/${taskId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  }

  async deleteRoadmap(roadmapId: string): Promise<ApiResponse<{ message: string }>> {
    console.log(`🗑️ Deleting roadmap ${roadmapId}`);
    return this.request<{ message: string }>(`/api/roadmap/${roadmapId}`, {
      method: 'DELETE',
    });
  }
}

// Helper functions
export const formatTimelineText = (weeks: number): string => {
  if (weeks < 4) return `${weeks} weeks`;
  const months = Math.floor(weeks / 4);
  const remainingWeeks = weeks % 4;
  if (remainingWeeks === 0) {
    return `${months} ${months === 1 ? 'month' : 'months'}`;
  }
  return `${months} ${months === 1 ? 'month' : 'months'} ${remainingWeeks} ${remainingWeeks === 1 ? 'week' : 'weeks'}`;
};

export const calculateDaysRemaining = (timelineWeeks: number, createdAt: string): number => {
  try {
    const created = new Date(createdAt);
    const endDate = new Date(created.getTime() + timelineWeeks * 7 * 24 * 60 * 60 * 1000);
    const now = new Date();
    const diff = endDate.getTime() - now.getTime();
    return Math.max(0, Math.ceil(diff / (24 * 60 * 60 * 1000)));
  } catch (error) {
    console.error('Error calculating days remaining:', error);
    return 0;
  }
};

// Export singleton instance
export const roadmapService = new RoadmapService();

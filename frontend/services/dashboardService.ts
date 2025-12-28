// frontend/services/dashboardService.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface DashboardData {
  success: boolean;
  user: {
    name: string;
    target_role: string;
    location: string;
  };
  daily_quote: string;
  industry_news: {
    headline: string;
    summary: string;
    takeaway: string;
    relevance: string;
  };
  stats: {
    journal_entries_week: number;
    journal_entries_month: number;
    interviews_completed: number;
    interviews_this_week: number;
    skills_count: number;
    projects_count: number;
    avg_sentiment: number;
    mood_trend: string;
    streak_days: number;
  };
  progress: {
    completed: number;
    total: number;
    percentage: number;
    daily_entries: number[];
  };
  today_actions: Array<{
    type: string;
    title: string;
    description: string;
    priority: string;
    time: string;
    icon: string;
  }>;
  recent_activity: Array<{
    type: string;
    title: string;
    time: string;
    mood?: string;
  }>;
  quick_stats: {
    resume_uploaded: boolean;
    profile_completeness: number;
  };
}

class DashboardService {
  private getAuthHeader(): HeadersInit {
    const token = localStorage.getItem('authtoken') || 
                  localStorage.getItem('accesstoken') || 
                  localStorage.getItem('access_token');
    
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    return {
      'Authorization': `Bearer ${token}`
    };
  }

  async getDashboardHome(): Promise<DashboardData> {
    const response = await fetch(`${API_BASE_URL}/api/dashboard/home`, {
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('Failed to fetch dashboard data');
    }

    return response.json();
  }
}

export const dashboardService = new DashboardService();

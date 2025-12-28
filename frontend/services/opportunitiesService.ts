// frontend/services/opportunitiesService.ts - UPDATED

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface JobOpportunity {
  id: string;
  match_id: number;
  title: string;
  company: string;
  location: string;
  url: string;
  job_type: string;
  match_score: number;
  matching_skills: string[];
  missing_skills: string[];
  status: string;
}

interface Hackathon {
  id: string;
  title: string;
  organizer: string;
  platform: string;
  prize_pool: string;
  url: string;
  match_score: number;
}

interface ScanResult {
  jobs_found: number;
  jobs_stored: number;
  job_matches: number;
  hackathon_matches: number;
  top_jobs: JobOpportunity[];
  top_hackathons: Hackathon[];
}

class OpportunitiesService {
  private getAuthHeader(): HeadersInit {
    const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found');
    }
    return { 
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async scanOpportunities(): Promise<{ success: boolean; message: string; data: ScanResult }> {
    console.log('🔍 Starting scan...');
    const response = await fetch(`${API_BASE_URL}/api/opportunities/scan`, {
      method: 'POST',
      headers: this.getAuthHeader()
    });

    const result = await response.json();
    console.log('📊 Scan response:', result);

    if (!response.ok) {
      throw new Error(result.detail || result.message || 'Failed to scan opportunities');
    }

    return result;
  }

  async getMatches(limit: number = 20): Promise<{ 
    success: boolean; 
    data: { jobs: JobOpportunity[]; hackathons: Hackathon[] } 
  }> {
    console.log('📋 Fetching matches...');
    const response = await fetch(`${API_BASE_URL}/api/opportunities/matches?limit=${limit}`, {
      headers: this.getAuthHeader()
    });

    const result = await response.json();
    console.log('📊 Matches response:', result);

    if (!response.ok) {
      throw new Error('Failed to fetch matches');
    }

    return result;
  }

  async updateJobStatus(
    jobMatchId: number, 
    status: 'saved' | 'applied' | 'rejected' | 'interviewing',
    notes?: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/opportunities/job/${jobMatchId}/status`, {
      method: 'PATCH',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ status, notes })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update status');
    }

    return response.json();
  }

  async getStats(): Promise<{
    success: boolean;
    stats: {
      total_matches: number;
      applied: number;
      saved: number;
      interviewing: number;
    }
  }> {
    const response = await fetch(`${API_BASE_URL}/api/opportunities/stats`, {
      headers: this.getAuthHeader()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }

    return response.json();
  }
}

export const opportunitiesService = new OpportunitiesService();

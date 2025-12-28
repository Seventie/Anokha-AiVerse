// frontend/src/services/agentService.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class AgentService {
  private getAuthHeader() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found. Please login again.');
    }
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  // Dashboard Home
  async getDashboardData(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/dashboard/${userId}`, {
      headers: this.getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to load dashboard');
    return response.json();
  }

  // Roadmap Agent
  async getRoadmap(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/roadmap/${userId}`, {
      headers: this.getAuthHeader()
    });
    if (!response.ok) return null;
    return response.json();
  }

  async generateRoadmap(userId: string, params: any) {
    const response = await fetch(`${API_BASE_URL}/api/agents/roadmap/generate`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId, ...params })
    });
    if (!response.ok) throw new Error('Failed to generate roadmap');
    return response.json();
  }

  async syncRoadmapToCalendar(userId: string, roadmap: any) {
    const response = await fetch(`${API_BASE_URL}/api/agents/roadmap/sync-calendar`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId, roadmap })
    });
    if (!response.ok) throw new Error('Failed to sync to calendar');
    return response.json();
  }

  // Opportunities Agent
  async getOpportunities(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/opportunities/${userId}`, {
      headers: this.getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to load opportunities');
    return response.json();
  }

  async scanOpportunities(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/opportunities/scan`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId })
    });
    if (!response.ok) throw new Error('Failed to scan opportunities');
    return response.json();
  }

  async saveJob(userId: string, jobId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/opportunities/save`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId, job_id: jobId })
    });
    return response.json();
  }

  // Resume Agent
  async analyzeResume(userId: string, resumeText: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/resume/analyze`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId, resume_text: resumeText })
    });
    if (!response.ok) throw new Error('Failed to analyze resume');
    return response.json();
  }

  async optimizeResume(userId: string, jobDescription: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/resume/optimize`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId, job_description: jobDescription })
    });
    if (!response.ok) throw new Error('Failed to optimize resume');
    return response.json();
  }

  // Journal Agent
  async getJournalEntries(userId: string, limit: number = 10) {
    const response = await fetch(`${API_BASE_URL}/api/agents/journal/${userId}?limit=${limit}`, {
      headers: this.getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to load journal');
    return response.json();
  }

  async addJournalEntry(userId: string, entry: string, mood: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/journal/add`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId, message: entry, mood })
    });
    if (!response.ok) throw new Error('Failed to add entry');
    return response.json();
  }

  async getMotivation(userId: string, context: any) {
    const response = await fetch(`${API_BASE_URL}/api/agents/journal/motivation`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId, context })
    });
    if (!response.ok) throw new Error('Failed to get motivation');
    return response.json();
  }

  // Interview Agent
  async startInterview(userId: string, jobTitle: string, difficulty: string = 'medium') {
    const response = await fetch(`${API_BASE_URL}/api/agents/interview/start`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId, job_title: jobTitle, difficulty })
    });
    if (!response.ok) throw new Error('Failed to start interview');
    return response.json();
  }

  async submitAnswer(sessionId: string, questionIndex: number, answer: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/interview/answer`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ session_id: sessionId, question_index: questionIndex, answer })
    });
    if (!response.ok) throw new Error('Failed to submit answer');
    return response.json();
  }

  async getInterviewFeedback(sessionId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/interview/feedback/${sessionId}`, {
      headers: this.getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to get feedback');
    return response.json();
  }

  // Summary Agent
  async getWeeklySummary(userId: string, weekOffset: number = 0) {
    const response = await fetch(`${API_BASE_URL}/api/agents/summary/${userId}?week_offset=${weekOffset}`, {
      headers: this.getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to load summary');
    return response.json();
  }

  async generateSummary(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/summary/generate`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId })
    });
    if (!response.ok) throw new Error('Failed to generate summary');
    return response.json();
  }

  // Supervisor Agent
  async getSupervisorStatus() {
    const response = await fetch(`${API_BASE_URL}/api/agents/supervisor/status`, {
      headers: this.getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to get status');
    return response.json();
  }

  async triggerSupervisor(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/supervisor/trigger`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId })
    });
    if (!response.ok) throw new Error('Failed to trigger supervisor');
    return response.json();
  }

  // Profile Agent
  async getProfileAnalysis(userId: string) {
    const response = await fetch(`${API_BASE_URL}/api/agents/profile/${userId}`, {
      headers: this.getAuthHeader()
    });
    if (!response.ok) throw new Error('Failed to load profile');
    return response.json();
  }

  async updateProfile(userId: string, updateData: any) {
    const response = await fetch(`${API_BASE_URL}/api/agents/profile/update`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ user_id: userId, update_data: updateData })
    });
    if (!response.ok) throw new Error('Failed to update profile');
    return response.json();
  }

  // WebSocket connection for real-time updates
  connectWebSocket(userId: string, onMessage: (data: any) => void) {
    const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Attempt reconnection after 5 seconds
      setTimeout(() => this.connectWebSocket(userId, onMessage), 5000);
    };

    return ws;
  }
}

export const agentService = new AgentService();
// frontend/services/journalService.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface JournalEntry {
  id: string;
  title: string;
  content: string;
  mood?: string;
  tags: string[];
  ai_summary?: string;
  key_insights: string[];
  sentiment_score?: number;
  topics_detected: string[];
  word_count: number;
  created_at: string;
  updated_at: string;
}

export interface JournalAnalysis {
  summary: string;
  insights: string[];
  suggestions: string[];
  mood: string;
  sentiment: number;
}

class JournalService {
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

  async createEntry(
    content: string,
    title?: string,
    mood?: string,
    tags?: string[]
  ): Promise<{ success: boolean; entry_id: string; analysis: JournalAnalysis }> {
    const response = await fetch(`${API_BASE_URL}/api/journal/entries`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({ title, content, mood, tags })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create entry');
    }

    return response.json();
  }

  async getEntries(
    limit: number = 20,
    offset: number = 0
  ): Promise<{
    success: boolean;
    entries: JournalEntry[];
    total: number;
    page: number;
    pages: number;
  }> {
    const response = await fetch(
      `${API_BASE_URL}/api/journal/entries?limit=${limit}&offset=${offset}`,
      { headers: this.getAuthHeader() }
    );

    if (!response.ok) {
      throw new Error('Failed to fetch entries');
    }

    return response.json();
  }

  async getPrompts(category?: string): Promise<{ success: boolean; prompts: string[] }> {
    const url = category
      ? `${API_BASE_URL}/api/journal/prompts?category=${category}`
      : `${API_BASE_URL}/api/journal/prompts`;

    const response = await fetch(url, {
      headers: this.getAuthHeader()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch prompts');
    }

    return response.json();
  }

  async getStats(): Promise<{
    success: boolean;
    stats: {
      total_entries: number;
      this_week: number;
      this_month: number;
      current_streak: number;
    };
  }> {
    const response = await fetch(`${API_BASE_URL}/api/journal/stats`, {
      headers: this.getAuthHeader()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }

    return response.json();
  }

  async deleteEntry(entryId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/journal/entries/${entryId}`, {
      method: 'DELETE',
      headers: this.getAuthHeader()
    });

    if (!response.ok) {
      throw new Error('Failed to delete entry');
    }

    return response.json();
  }
  async getComprehensiveSummary(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/journal/summary/comprehensive`, {
    headers: this.getAuthHeader()
  });

  if (!response.ok) {
    throw new Error('Failed to fetch comprehensive summary');
  }

  return response.json();
}
}



export const journalService = new JournalService();

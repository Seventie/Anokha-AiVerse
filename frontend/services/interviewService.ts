// frontend/src/services/interviewService.ts

import { apiService } from './apiService';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface InterviewCreate {
  interview_type: 'company_specific' | 'custom_topic';
  company_name?: string;
  job_description?: string;
  custom_topics?: string[];
  total_rounds: number;
  round_configs: Array<{
    type: 'technical' | 'hr' | 'communication';
    difficulty: 'easy' | 'medium' | 'hard';
  }>;
}

export interface Interview {
  id: string;
  interview_type: string;
  company_name?: string;
  total_rounds: number;
  current_round: number;
  status: string;
  created_at: string;
}

export interface Round {
  id: string;
  round_number: number;
  round_type: string;
  difficulty: string;
  status: string;
  score?: number;
  pass_status?: boolean;
}

export interface Question {
  question_id: number;
  question_text: string;
  category: string;
  what_to_look_for: string[];
  audio_url?: string;
}

export interface AnswerFeedback {
  score: number;
  feedback: string;
  strengths: string[];
  improvements: string[];
  next_question?: Question;
}

export interface Evaluation {
  overall_score: number;
  technical_score: number;
  communication_score: number;
  problem_solving_score: number;
  confidence_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

class InterviewService {
  private getAuthHeader() {
    const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found');
    }
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  // ========== INTERVIEW LIFECYCLE ==========

  async createInterview(data: InterviewCreate): Promise<Interview> {
    const response = await fetch(`${API_BASE_URL}/api/interview/create`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify(data)
    });
    
    if (!response.ok) throw new Error('Failed to create interview');
    return response.json();
  }

  async startInterview(interviewId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/start`, {
      method: 'POST',
      headers: this.getAuthHeader()
    });
    
    if (!response.ok) throw new Error('Failed to start interview');
    return response.json();
  }

  async pauseInterview(interviewId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/pause`, {
      method: 'POST',
      headers: this.getAuthHeader()
    });
    
    if (!response.ok) throw new Error('Failed to pause interview');
    return response.json();
  }

  async completeInterview(interviewId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/complete`, {
      method: 'POST',
      headers: this.getAuthHeader()
    });
    
    if (!response.ok) throw new Error('Failed to complete interview');
    return response.json();
  }

  // ========== ROUND MANAGEMENT ==========

  async getRounds(interviewId: string): Promise<Round[]> {
    const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/rounds`, {
      headers: this.getAuthHeader()
    });
    
    if (!response.ok) throw new Error('Failed to get rounds');
    return response.json();
  }

  // frontend/src/services/interviewService.ts

async startRound(interviewId: string, roundId: string): Promise<Question> {
  try {
    console.log('🚀 Starting round:', { interviewId, roundId });
    
    const response = await fetch(
      `${API_BASE_URL}/api/interview/${interviewId}/round/${roundId}/start`,
      {
        method: 'POST',
        headers: this.getAuthHeader()
      }
    );
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('❌ Backend error:', errorData);
      throw new Error(errorData.detail || `Failed to start round: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ Round started:', data);
    return data;
  } catch (error) {
    console.error('❌ Failed to start round:', error);
    throw error;
  }
}


  // ========== QUESTION & ANSWER ==========

  async submitTextAnswer(
    interviewId: string,
    roundId: string,
    questionId: number,
    answerText: string
  ): Promise<AnswerFeedback> {
    const response = await fetch(`${API_BASE_URL}/api/interview/answer`, {
      method: 'POST',
      headers: this.getAuthHeader(),
      body: JSON.stringify({
        interview_id: interviewId,
        round_id: roundId,
        question_id: questionId,
        answer_text: answerText
      })
    });
    
    if (!response.ok) throw new Error('Failed to submit answer');
    return response.json();
  }

  async submitAudioAnswer(
    interviewId: string,
    roundId: string,
    questionId: number,
    audioBlob: Blob
  ): Promise<AnswerFeedback> {
    const formData = new FormData();
    formData.append('interview_id', interviewId);
    formData.append('round_id', roundId);
    formData.append('question_id', questionId.toString());
    formData.append('audio', audioBlob, 'answer.wav');

    const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
    
    const response = await fetch(`${API_BASE_URL}/api/interview/answer/audio`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
        // Don't set Content-Type for FormData - browser will set it with boundary
      },
      body: formData
    });
    
    if (!response.ok) throw new Error('Failed to submit audio answer');
    return response.json();
  }

  // ========== RESULTS & ANALYTICS ==========

  async getEvaluation(interviewId: string): Promise<Evaluation> {
    const response = await fetch(
      `${API_BASE_URL}/api/interview/${interviewId}/evaluation`,
      {
        headers: this.getAuthHeader()
      }
    );
    
    if (!response.ok) throw new Error('Failed to get evaluation');
    return response.json();
  }

  async getHistory(limit: number = 10): Promise<any[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/interview/history?limit=${limit}`,
      {
        headers: this.getAuthHeader()
      }
    );
    
    if (!response.ok) throw new Error('Failed to get history');
    return response.json();
  }

  async getAnalytics(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/interview/analytics`, {
      headers: this.getAuthHeader()
    });
    
    if (!response.ok) throw new Error('Failed to get analytics');
    return response.json();
  }

  async getConversation(interviewId: string, roundId?: string): Promise<any[]> {
    let url = `${API_BASE_URL}/api/interview/${interviewId}/conversation`;
    if (roundId) url += `?round_id=${roundId}`;
    
    const response = await fetch(url, {
      headers: this.getAuthHeader()
    });
    
    if (!response.ok) throw new Error('Failed to get conversation');
    return response.json();
  }

  // ========== RECORDING ==========

  async uploadRecording(interviewId: string, videoBlob: Blob): Promise<any> {
    const formData = new FormData();
    formData.append('video', videoBlob, 'interview.webm');

    const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
    
    const response = await fetch(
      `${API_BASE_URL}/api/interview/${interviewId}/recording/upload`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      }
    );
    
    if (!response.ok) throw new Error('Failed to upload recording');
    return response.json();
  }

  // ========== HELPERS ==========

  playAudio(audioUrl: string): HTMLAudioElement {
    const audio = new Audio(`${API_BASE_URL}${audioUrl}`);
    audio.play();
    return audio;
  }
}

export const interviewService = new InterviewService();

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
  current_round_data?: Round;
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
  question?: string;
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
  is_complete?: boolean;
  next_round?: Round;
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
    try {
      console.log('📤 Creating interview:', data);
      const response = await fetch(`${API_BASE_URL}/api/interview/create`, {
        method: 'POST',
        headers: this.getAuthHeader(),
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to create interview');
      }
      
      const result = await response.json();
      console.log('✅ Interview created:', result);
      return result;
    } catch (error) {
      console.error('❌ Create interview error:', error);
      throw error;
    }
  }

  // 🔥 FIX: Added missing getInterview method
  async getInterview(interviewId: string): Promise<Interview> {
    try {
      console.log('📥 Fetching interview:', interviewId);
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}`, {
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to get interview');
      }
      
      const result = await response.json();
      console.log('✅ Interview fetched:', result);
      return result;
    } catch (error) {
      console.error('❌ Get interview error:', error);
      throw error;
    }
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
    try {
      console.log('📥 Fetching rounds for:', interviewId);
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/rounds`, {
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to get rounds');
      }
      
      const rounds = await response.json();
      console.log('✅ Rounds fetched:', rounds);
      return rounds;
    } catch (error) {
      console.error('❌ Get rounds error:', error);
      throw error;
    }
  }

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
    try {
      console.log('📤 Submitting text answer:', { interviewId, roundId, questionId });
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
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to submit answer');
      }
      
      const result = await response.json();
      console.log('✅ Answer submitted:', result);
      return result;
    } catch (error) {
      console.error('❌ Submit answer error:', error);
      throw error;
    }
  }

  async submitAudioAnswer(
    interviewId: string,
    roundId: string,
    questionId: number,
    audioBlob: Blob
  ): Promise<AnswerFeedback> {
    try {
      console.log('📤 Submitting audio answer:', { interviewId, roundId, questionId });
      const formData = new FormData();
      formData.append('interview_id', interviewId);
      formData.append('round_id', roundId);
      formData.append('question_id', questionId.toString());

      const mime = (audioBlob.type || '').toLowerCase();
      const filename = mime.includes('webm')
        ? 'answer.webm'
        : mime.includes('mpeg') || mime.includes('mp3')
        ? 'answer.mp3'
        : mime.includes('mp4') || mime.includes('m4a')
        ? 'answer.m4a'
        : 'answer.wav';

      formData.append('audio', audioBlob, filename);

      const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
      
      const response = await fetch(`${API_BASE_URL}/api/interview/answer/audio`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
          // Don't set Content-Type for FormData - browser will set it with boundary
        },
        body: formData
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to submit audio answer');
      }
      
      const result = await response.json();
      console.log('✅ Audio answer submitted:', result);
      return result;
    } catch (error) {
      console.error('❌ Submit audio error:', error);
      throw error;
    }
  }

  // 🔥 FIX: Added submitAnswer method (used by InterviewRoom)
  async submitAnswer(
    interviewId: string,
    data: { answer: string; is_voice: boolean }
  ): Promise<any> {
    try {
      console.log('📤 Submitting answer:', { interviewId, data });
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/submit-answer`, {
        method: 'POST',
        headers: this.getAuthHeader(),
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to submit answer');
      }
      
      const result = await response.json();
      console.log('✅ Answer submitted:', result);
      return result;
    } catch (error) {
      console.error('❌ Submit answer error:', error);
      throw error;
    }
  }

  // ========== RESULTS & ANALYTICS ==========

  async getEvaluation(interviewId: string): Promise<Evaluation> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/interview/${interviewId}/evaluation`,
        {
          headers: this.getAuthHeader()
        }
      );
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to get evaluation');
      }
      
      return response.json();
    } catch (error) {
      console.error('❌ Get evaluation error:', error);
      throw error;
    }
  }

  // 🔥 FIX: Added getResults method
  async getResults(interviewId: string): Promise<any> {
    try {
      console.log('📥 Fetching results for:', interviewId);
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/results`, {
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to get results');
      }
      
      const results = await response.json();
      console.log('✅ Results fetched:', results);
      return results;
    } catch (error) {
      console.error('❌ Get results error:', error);
      throw error;
    }
  }

  // 🔥 FIX: Added getAnalytics method with interviewId parameter
  async getAnalytics(interviewId?: string): Promise<any> {
    try {
      const url = interviewId 
        ? `${API_BASE_URL}/api/interview/${interviewId}/analytics`
        : `${API_BASE_URL}/api/interview/analytics`;
      
      const response = await fetch(url, {
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to get analytics');
      }
      
      return response.json();
    } catch (error) {
      console.error('❌ Get analytics error:', error);
      throw error;
    }
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

  async getConversation(interviewId: string, roundId?: string): Promise<any[]> {
    try {
      let url = `${API_BASE_URL}/api/interview/${interviewId}/conversation`;
      if (roundId) url += `?round_id=${roundId}`;
      
      const response = await fetch(url, {
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to get conversation');
      }
      
      return response.json();
    } catch (error) {
      console.error('❌ Get conversation error:', error);
      throw error;
    }
  }

  // ========== RECORDING ==========

  async uploadRecording(interviewId: string, videoBlob: Blob): Promise<any> {
    try {
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
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Failed to upload recording');
      }
      
      return response.json();
    } catch (error) {
      console.error('❌ Upload recording error:', error);
      throw error;
    }
  }

  // 🔥 FIX: Added downloadReport method
  async downloadReport(interviewId: string): Promise<void> {
    try {
      const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/report`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to download report');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `interview-report-${interviewId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('❌ Download report error:', error);
      throw error;
    }
  }

  // ========== HELPERS ==========

  playAudio(audioUrl: string): HTMLAudioElement {
    const audio = new Audio(`${API_BASE_URL}${audioUrl}`);
    audio.play();
    return audio;
  }
}

export const interviewService = new InterviewService();

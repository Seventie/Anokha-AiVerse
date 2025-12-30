// frontend/src/services/interviewService.ts

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
    pass_threshold?: number;
  }>;
}

export interface Interview {
  id: string;
  interview_type: string;
  company_name?: string;
  job_description?: string;
  total_rounds: number;
  current_round: number;
  current_round_data?: Round;
  status: string;
  created_at: string;
  overall_score?: number;
  verdict?: string;
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
}

export interface FinalEvaluation {
  technical_score: number;
  communication_score: number;
  problem_solving_score: number;
  confidence_score: number;
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  suggested_topics: string[];
  verdict: 'selected' | 'positive' | 'considerate' | 'not_selected';
}

export interface InterviewHistoryItem {
  id: string;
  interview_type: string;
  company_name?: string;
  status: string;
  overall_score?: number;
  verdict?: 'selected' | 'positive' | 'considerate' | 'not_selected';
  completed_at?: string;
  created_at?: string;
  duration_seconds?: number;
  completed_rounds?: number;
  total_rounds?: number;
}

export interface DetailedResults {
  interview: {
    id: string;
    company_name: string;
    duration_seconds: number;
    verdict: {
      label: string;
      color: string;
      icon: string;
      message: string;
    };
  };
  scores: {
    overall: number;
    technical: number;
    communication: number;
    problem_solving: number;
    confidence: number;
  };
  qa_breakdown: Array<{
    question_id: number;
    question: string;
    category: string;
    answer: string;
    score: number;
    confidence: string;
    feedback: string;
    strengths: string[];
    improvements: string[];
    audio_url?: string;
    answer_audio_url?: string;
  }>;
  skill_gaps: Array<{
    skill: string;
    severity: string;
    recommended_action: string;
  }>;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  recording: {
    video_url?: string;
    duration?: number;
  };
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
        const error = await response.json().catch(() => ({ detail: 'Failed to create interview' }));
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

  async getInterview(interviewId: string): Promise<Interview> {
    try {
      console.log('📥 Fetching interview:', interviewId);
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}`, {
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to get interview' }));
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

  async startInterview(interviewId: string): Promise<{ message: string; interview_id: string }> {
    try {
      console.log('🚀 Starting interview:', interviewId);
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/start`, {
        method: 'POST',
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to start interview' }));
        throw new Error(error.detail || 'Failed to start interview');
      }
      
      const result = await response.json();
      console.log('✅ Interview started:', result);
      return result;
    } catch (error) {
      console.error('❌ Start interview error:', error);
      throw error;
    }
  }

  async pauseInterview(interviewId: string): Promise<{ message: string; interview_id: string }> {
    try {
      console.log('⏸️ Pausing interview:', interviewId);
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/pause`, {
        method: 'POST',
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to pause interview' }));
        throw new Error(error.detail || 'Failed to pause interview');
      }
      
      return response.json();
    } catch (error) {
      console.error('❌ Pause interview error:', error);
      throw error;
    }
  }

  async completeInterview(interviewId: string): Promise<{
    message: string;
    overall_score: number;
    verdict: 'selected' | 'positive' | 'considerate' | 'not_selected';
    evaluation_id: string;
  }> {
    try {
      console.log('🏁 Completing interview:', interviewId);
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/complete`, {
        method: 'POST',
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to complete interview' }));
        throw new Error(error.detail || 'Failed to complete interview');
      }
      
      const result = await response.json();
      console.log('✅ Interview completed:', result);
      return result;
    } catch (error) {
      console.error('❌ Complete interview error:', error);
      throw error;
    }
  }

  async deleteInterview(interviewId: string): Promise<{ message: string }> {
    try {
      console.log('🗑️ Deleting interview:', interviewId);
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}`, {
        method: 'DELETE',
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to delete interview' }));
        throw new Error(error.detail || 'Failed to delete interview');
      }
      
      return response.json();
    } catch (error) {
      console.error('❌ Delete interview error:', error);
      throw error;
    }
  }

  // ========== ROUND MANAGEMENT ==========

  async getRounds(interviewId: string): Promise<Round[]> {
    try {
      console.log('📥 Fetching rounds for:', interviewId);
      const response = await fetch(`${API_BASE_URL}/api/interview/${interviewId}/rounds`, {
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to get rounds' }));
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
        const errorData = await response.json().catch(() => ({ detail: 'Failed to start round' }));
        console.error('❌ Backend error:', errorData);
        throw new Error(errorData.detail || `Failed to start round: ${response.status}`);
      }

      const data = await response.json();
      console.log('✅ Round started with question:', data);
      return data;
    } catch (error) {
      console.error('❌ Failed to start round:', error);
      throw error;
    }
  }

  // ========== QUESTION & ANSWER ==========

  async submitAnswer(
    interviewId: string,
    roundId: string,
    questionId: number | string,
    answerText: string,
    audioUrl?: string
  ): Promise<AnswerFeedback> {
    try {
      console.log('📤 Submitting answer:', { interviewId, roundId, questionId });
      const response = await fetch(`${API_BASE_URL}/api/interview/answer`, {
        method: 'POST',
        headers: this.getAuthHeader(),
        body: JSON.stringify({
          interview_id: interviewId,
          round_id: roundId,
          question_id: Number(questionId),
          answer_text: answerText,
          audio_url: audioUrl
        })
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to submit answer' }));
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

  async submitTextAnswer(
    interviewId: string,
    roundId: string,
    questionId: number | string,
    answerText: string
  ): Promise<AnswerFeedback> {
    return this.submitAnswer(interviewId, roundId, questionId, answerText);
  }

  async submitAudioAnswer(
    interviewId: string,
    roundId: string,
    questionId: number | string,
    audioBlob: Blob
  ): Promise<AnswerFeedback> {
    try {
      console.log('📤 Submitting audio answer:', { interviewId, roundId, questionId });
      const formData = new FormData();
      formData.append('interview_id', interviewId);
      formData.append('round_id', roundId);
      formData.append('question_id', String(questionId));

      // Determine filename based on mime type
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
        },
        body: formData
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to submit audio answer' }));
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

  // ========== RESULTS & ANALYTICS ==========

  async getEvaluation(interviewId: string): Promise<FinalEvaluation> {
    try {
      console.log('📊 Fetching evaluation:', interviewId);
      const response = await fetch(
        `${API_BASE_URL}/api/interview/${interviewId}/evaluation`,
        {
          headers: this.getAuthHeader()
        }
      );
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to get evaluation' }));
        throw new Error(error.detail || 'Failed to get evaluation');
      }
      
      const result = await response.json();
      console.log('✅ Evaluation fetched:', result);
      return result;
    } catch (error) {
      console.error('❌ Get evaluation error:', error);
      throw error;
    }
  }

  async getDetailedResults(interviewId: string): Promise<DetailedResults> {
    try {
      console.log('📊 Fetching detailed results:', interviewId);
      const response = await fetch(
        `${API_BASE_URL}/api/interview/${interviewId}/detailed-results`,
        {
          headers: this.getAuthHeader()
        }
      );
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to get detailed results' }));
        throw new Error(error.detail || 'Failed to get detailed results');
      }
      
      const result = await response.json();
      console.log('✅ Detailed results fetched:', result);
      return result;
    } catch (error) {
      console.error('❌ Get detailed results error:', error);
      throw error;
    }
  }

  async getConversation(interviewId: string, roundId?: string): Promise<Array<{
    id: number;
    speaker: 'ai' | 'user';
    message: string;
    audio_url?: string;
    timestamp: string;
    score?: number;
  }>> {
    try {
      console.log('📥 Fetching conversation:', { interviewId, roundId });
      let url = `${API_BASE_URL}/api/interview/${interviewId}/conversation`;
      if (roundId) url += `?round_id=${roundId}`;
      
      const response = await fetch(url, {
        headers: this.getAuthHeader()
      });
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to get conversation' }));
        throw new Error(error.detail || 'Failed to get conversation');
      }
      
      const result = await response.json();
      console.log('✅ Conversation fetched:', result);
      return result;
    } catch (error) {
      console.error('❌ Get conversation error:', error);
      throw error;
    }
  }

  async getInterviewHistory(limit: number = 10): Promise<InterviewHistoryItem[]> {
    try {
      console.log('📥 Fetching interview history');
      const response = await fetch(
        `${API_BASE_URL}/api/interview/history?limit=${limit}`,
        {
          headers: this.getAuthHeader()
        }
      );
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to get interview history' }));
        throw new Error(error.detail || 'Failed to get interview history');
      }
      
      const result = await response.json();
      console.log('✅ Interview history fetched:', result);
      return result;
    } catch (error) {
      console.error('❌ Get interview history error:', error);
      throw error;
    }
  }

  // ========== RECORDING ==========

  async uploadRecording(interviewId: string, videoBlob: Blob): Promise<{
    message: string;
    video_url: string;
    file_size_mb: number;
  }> {
    try {
      console.log('📤 Uploading session recording:', interviewId);
      const formData = new FormData();
      
      const filename = `session_${interviewId}_${Date.now()}.webm`;
      formData.append('video', videoBlob, filename);

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
        const error = await response.json().catch(() => ({ detail: 'Failed to upload recording' }));
        throw new Error(error.detail || 'Failed to upload recording');
      }
      
      const result = await response.json();
      console.log('✅ Session recording uploaded:', result);
      return result;
    } catch (error) {
      console.error('❌ Upload recording error:', error);
      throw error;
    }
  }

  async getRecording(interviewId: string): Promise<{
    video_url: string;
    transcript_text?: string;
    duration_seconds?: number;
    file_size_mb: number;
  }> {
    try {
      console.log('📥 Fetching recording:', interviewId);
      const response = await fetch(
        `${API_BASE_URL}/api/interview/${interviewId}/recording`,
        {
          headers: this.getAuthHeader()
        }
      );
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to get recording' }));
        throw new Error(error.detail || 'Failed to get recording');
      }
      
      const result = await response.json();
      console.log('✅ Recording fetched:', result);
      return result;
    } catch (error) {
      console.error('❌ Get recording error:', error);
      throw error;
    }
  }

  // ========== UTILITIES ==========

  playAudio(audioUrl: string): HTMLAudioElement {
    const fullUrl = audioUrl.startsWith('http') 
      ? audioUrl 
      : `${API_BASE_URL}${audioUrl}`;
    const audio = new Audio(fullUrl);
    audio.play().catch(err => console.error('Audio playback error:', err));
    return audio;
  }

  getFullAudioUrl(audioUrl?: string): string | undefined {
    if (!audioUrl) return undefined;
    return audioUrl.startsWith('http') 
      ? audioUrl 
      : `${API_BASE_URL}${audioUrl}`;
  }
}

export const interviewService = new InterviewService();

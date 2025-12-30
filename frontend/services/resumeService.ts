// frontend/src/services/resumeService.ts - COMPLETE FIXED VERSION

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ==================== INTERFACES ====================

export interface ParsedResume {
  personal_info: {
    fullName: string | null;
    email: string | null;
    phone: string | null;
    location: string | null;
    linkedin: string | null;
    github: string | null;
    portfolio: string | null;
    summary: string | null;
  };
  education: Array<{
    degree: string;
    institution: string;
    year: string;
    gpa?: string;
  }>;
  experience: Array<{
    title: string;
    company: string;
    duration: string;
    responsibilities: string[];
  }>;
  projects: Array<{
    name: string;
    description: string;
    technologies: string[];
    link?: string;
  }>;
  skills: {
    technical: string[];
    non_technical: string[];
  };
  certifications: any[];
  achievements: string[];
  languages: Array<{
    language: string;
    proficiency: string;
  }>;
  metadata: {
    parsed_at: string;
    confidence_score: number;
    source_file: string;
  };
}

export interface ResumeData {
  id?: string;
  resume_id: string;
  filename: string;
  parsed_data: ParsedResume;
  uploaded_at: string;
  is_active?: boolean;
  match_score?: number;
}

export interface ResumeHistoryItem {
  id: string;
  filename: string;
  full_name: string | null;
  is_active: boolean;
  uploaded_at: string;
  match_score: number | null;
}

// ==================== ANALYSIS INTERFACES ====================

export interface ATSScore {
  overall_score: number;
  breakdown: {
    contact_info: number;
    skills: number;
    experience: number;
    education: number;
    projects: number;
    formatting: number;
  };
  grade: string;
  message: string;
}

export interface ResumeSuggestions {
  strengths: string[];
  weaknesses: string[];
  improvements: string[];
}

export interface ProjectSuggestion {
  name: string;
  description: string;
  technologies: string[];
  value: string;
}

export interface JDAnalysis {
  match_score: number;
  matching_keywords: string[];
  missing_keywords: string[];
  recommended_changes: string[];
  ats_keywords: string[];
}

export interface ResumeAnalysis {
  ats_score: ATSScore;
  suggestions: ResumeSuggestions;
  project_suggestions: ProjectSuggestion[];
  jd_analysis?: JDAnalysis;
}

// ==================== SERVICE CLASS ====================

class ResumeService {
  private getAuthHeader(): HeadersInit {
    const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found');
    }
    return { 'Authorization': `Bearer ${token}` };
  }

  // ==================== UNAUTHENTICATED PARSING (FOR SIGNUP) ====================

  /**
   * 🔥 Parse resume WITHOUT authentication (for signup flow)
   * This endpoint doesn't require auth token
   */
  async parseResumeUnauthenticated(file: File): Promise<{ message: string; data: ParsedResume }> {
    try {
      console.log('📄 Parsing resume (unauthenticated):', file.name);
      
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE_URL}/api/resume/parse`, {
        method: 'POST',
        body: formData // No auth header!
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to parse resume' }));
        throw new Error(error.detail || 'Failed to parse resume');
      }

      const result = await response.json();
      console.log('✅ Resume parsed successfully:', result);
      return result;
    } catch (error) {
      console.error('❌ Resume parsing error:', error);
      throw error;
    }
  }

  // ==================== AUTHENTICATED UPLOAD & PARSE ====================

  /**
   * Upload resume WITH authentication (after login)
   * This saves the resume to the user's account
   */
  async uploadResume(
    file: File, 
    jobDescription?: string
  ): Promise<{ message: string; resume_id: string; data: ParsedResume }> {
    try {
      console.log('📤 Uploading resume (authenticated):', file.name);
      
      const formData = new FormData();
      formData.append('file', file);
      if (jobDescription) {
        formData.append('jd_text', jobDescription);
      }

      const response = await fetch(`${API_BASE_URL}/api/resume/upload`, {
        method: 'POST',
        headers: this.getAuthHeader(),
        body: formData
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to upload resume' }));
        throw new Error(error.detail || 'Failed to upload resume');
      }

      const result = await response.json();
      console.log('✅ Resume uploaded successfully:', result);
      return result;
    } catch (error) {
      console.error('❌ Resume upload error:', error);
      throw error;
    }
  }

  /**
   * @deprecated Use parseResumeUnauthenticated for signup or uploadResume for authenticated users
   */
  async parseResume(
    file: File, 
    jobDescription?: string
  ): Promise<{ message: string; data: ParsedResume }> {
    return this.parseResumeUnauthenticated(file);
  }

  // ==================== ANALYSIS ====================

  async analyzeCurrentResume(
    jdText?: string
  ): Promise<{ success: boolean; data: ResumeAnalysis }> {
    try {
      const headers: HeadersInit = {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      };

      const response = await fetch(`${API_BASE_URL}/api/resume/analyze`, {
        method: 'POST',
        headers,
        body: jdText ? JSON.stringify({ jd_text: jdText }) : undefined
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to analyze resume' }));
        throw new Error(error.detail || 'Failed to analyze resume');
      }

      return response.json();
    } catch (error) {
      console.error('❌ Resume analysis error:', error);
      throw error;
    }
  }

  async analyzeResume(
    resumeId: string, 
    jdText?: string
  ): Promise<{ success: boolean; data: ResumeAnalysis }> {
    try {
      const headers: HeadersInit = {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      };

      const response = await fetch(`${API_BASE_URL}/api/resume/${resumeId}/analyze`, {
        method: 'POST',
        headers,
        body: jdText ? JSON.stringify({ jd_text: jdText }) : undefined
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to analyze resume' }));
        throw new Error(error.detail || 'Failed to analyze resume');
      }

      return response.json();
    } catch (error) {
      console.error('❌ Resume analysis error:', error);
      throw error;
    }
  }

  async analyzeUploadedResume(
    file: File, 
    jdText?: string
  ): Promise<{ 
    success: boolean; 
    parsed_data: ParsedResume; 
    analysis: ResumeAnalysis 
  }> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (jdText) {
        formData.append('jd_text', jdText);
      }

      const response = await fetch(`${API_BASE_URL}/api/resume/analyze-uploaded`, {
        method: 'POST',
        headers: this.getAuthHeader(),
        body: formData
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to analyze resume' }));
        throw new Error(error.detail || 'Failed to analyze resume');
      }

      return response.json();
    } catch (error) {
      console.error('❌ Resume analysis error:', error);
      throw error;
    }
  }

  // ==================== RETRIEVAL ====================

  async getCurrentResume(): Promise<ResumeData | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/resume/current`, {
        headers: {
          ...this.getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });

      if (response.status === 404) {
        return null;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch resume');
      }

      return response.json();
    } catch (error) {
      console.error('❌ Get current resume error:', error);
      throw error;
    }
  }

  async getResumeHistory(): Promise<ResumeHistoryItem[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/resume/history`, {
        headers: {
          ...this.getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch history');
      }

      return response.json();
    } catch (error) {
      console.error('❌ Get resume history error:', error);
      throw error;
    }
  }

  async getAllResumes(): Promise<ResumeData[]> {
    try {
      const history = await this.getResumeHistory();
      return history.map(item => ({
        id: item.id,
        resume_id: item.id,
        filename: item.filename,
        uploaded_at: item.uploaded_at,
        is_active: item.is_active,
        match_score: item.match_score || 0,
        parsed_data: {} as ParsedResume // Will be loaded on demand
      }));
    } catch (error) {
      console.error('❌ Get all resumes error:', error);
      throw error;
    }
  }

  // ==================== MANAGEMENT ====================

  async setActiveResume(resumeId: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/resume/${resumeId}/set-active`, {
        method: 'PATCH',
        headers: {
          ...this.getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to set active resume' }));
        throw new Error(error.detail || 'Failed to set active resume');
      }

      return response.json();
    } catch (error) {
      console.error('❌ Set active resume error:', error);
      throw error;
    }
  }

  async deleteResume(resumeId: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/resume/${resumeId}`, {
        method: 'DELETE',
        headers: {
          ...this.getAuthHeader(),
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Failed to delete resume' }));
        throw new Error(error.detail || 'Failed to delete resume');
      }

      return response.json();
    } catch (error) {
      console.error('❌ Delete resume error:', error);
      throw error;
    }
  }
}

// ==================== SINGLETON EXPORT ====================

export const resumeService = new ResumeService();

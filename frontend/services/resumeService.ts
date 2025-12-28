// frontend/services/resumeService.ts - COMPLETE VERSION

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

  // ==================== UPLOAD & PARSE ====================

  async uploadResume(
    file: File, 
    jobDescription?: string
  ): Promise<{ message: string; resume_id: string; data: ParsedResume }> {
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
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload resume');
    }

    return response.json();
  }

  async parseResume(
    file: File, 
    jobDescription?: string
  ): Promise<{ message: string; data: ParsedResume }> {
    const formData = new FormData();
    formData.append('file', file);
    if (jobDescription) {
      formData.append('jd_text', jobDescription);
    }

    const response = await fetch(`${API_BASE_URL}/api/resume/parse`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to parse resume');
    }

    return response.json();
  }

  // ==================== ANALYSIS ====================

  async analyzeCurrentResume(
    jdText?: string
  ): Promise<{ success: boolean; data: ResumeAnalysis }> {
    const headers = {
      ...this.getAuthHeader(),
      'Content-Type': 'application/json'
    };

    const body = jdText ? JSON.stringify({ jd_text: jdText }) : undefined;

    const response = await fetch(`${API_BASE_URL}/api/resume/analyze`, {
      method: 'POST',
      headers,
      body
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to analyze resume');
    }

    return response.json();
  }

  async analyzeResume(
    resumeId: string, 
    jdText?: string
  ): Promise<{ success: boolean; data: ResumeAnalysis }> {
    const headers = {
      ...this.getAuthHeader(),
      'Content-Type': 'application/json'
    };

    const body = jdText ? JSON.stringify({ jd_text: jdText }) : undefined;

    const response = await fetch(`${API_BASE_URL}/api/resume/${resumeId}/analyze`, {
      method: 'POST',
      headers,
      body
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to analyze resume');
    }

    return response.json();
  }

  async analyzeUploadedResume(
    file: File, 
    jdText?: string
  ): Promise<{ 
    success: boolean; 
    parsed_data: ParsedResume; 
    analysis: ResumeAnalysis 
  }> {
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
      const error = await response.json();
      throw new Error(error.detail || 'Failed to analyze resume');
    }

    return response.json();
  }

  // ==================== RETRIEVAL ====================

  async getCurrentResume(): Promise<ResumeData | null> {
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
  }

  async getResumeHistory(): Promise<ResumeHistoryItem[]> {
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
  }

  async getAllResumes(): Promise<ResumeData[]> {
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
  }

  // ==================== MANAGEMENT ====================

  async setActiveResume(resumeId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/resume/${resumeId}/set-active`, {
      method: 'PATCH',
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to set active resume');
    }

    return response.json();
  }

  async deleteResume(resumeId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/resume/${resumeId}`, {
      method: 'DELETE',
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete resume');
    }

    return response.json();
  }
}

// ==================== SINGLETON EXPORT ====================

export const resumeService = new ResumeService();

// frontend/services/resumeService.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
  resume_id: string;
  filename: string;
  parsed_data: ParsedResume;
  uploaded_at: string;
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

class ResumeService {
  private getAuthHeader(): HeadersInit {
    const token = localStorage.getItem('access_token') || localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('No authentication token found');
    }
    return { 'Authorization': `Bearer ${token}` };
  }

  async uploadResume(file: File, jobDescription?: string): Promise<{ message: string; resume_id: string; data: ParsedResume }> {
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

  async parseResume(file: File, jobDescription?: string): Promise<{ message: string; data: ParsedResume }> {
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

  async deleteResume(resumeId: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/resume/${resumeId}`, {
      method: 'DELETE',
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error('Failed to delete resume');
    }

    return response.json();
  }
}

export const resumeService = new ResumeService();

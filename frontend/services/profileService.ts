// frontend/services/profileService.ts

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface CompleteProfile {
  profile: {
    id: string;
    email: string;
    full_name: string;
    location: string;
    readiness_level: string;
    created_at: string;
  };
  career_goals: {
    target_roles: string[];
    timeline: string;
    vision_statement: string;
  };
  education: Array<{
    id: number;
    institution: string;
    degree: string;
    major?: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    grade?: string;
  }>;
  experience: Array<{
    id: number;
    role: string;
    company: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    description?: string;
  }>;
  projects: Array<{
    id: number;
    title: string;
    description?: string;
    tech_stack?: string;
    link?: string;
  }>;
  skills: Array<{
    id: number;
    skill: string;
    category: string;
    level: string;
  }>;
  links: Array<{
    id: number;
    type: string;
    url: string;
  }>;
  availability: {
    free_time: string;
    study_days: string[];
  } | null;
  preferred_locations: string[];
  resume: {
    id: string;
    filename: string;
    uploaded_at: string;
  } | null;
  completeness_score: number;
  missing_sections: string[];
}

class ProfileService {
  private getAuthHeader(): HeadersInit {
    // ✅ FIX: Try multiple possible token keys
    const token = localStorage.getItem('authtoken') || 
                  localStorage.getItem('accesstoken') || 
                  localStorage.getItem('access_token');
    
    console.log('🔑 Token check:', token ? 'Found' : 'Not found'); // Debug log
    
    if (!token) {
      console.error('❌ No auth token found in localStorage');
      console.log('Available keys:', Object.keys(localStorage));
      throw new Error('No authentication token found');
    }
    
    return {
      'Authorization': `Bearer ${token}`
    };
  }

  async getCompleteProfile(): Promise<CompleteProfile> {
    const response = await fetch(`${API_BASE_URL}/api/profile/complete`, {
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Profile fetch failed:', error);
      throw new Error('Failed to fetch profile');
    }

    return response.json();
  }

  async updateBasicProfile(updates: {
    full_name?: string;
    location?: string;
    target_role?: string;
    timeline?: string;
    vision_statement?: string;
  }): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/profile/basic`, {
      method: 'PATCH',
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });

    if (!response.ok) {
      throw new Error('Failed to update profile');
    }

    return response.json();
  }

  // Education
  async addEducation(data: {
    institution: string;
    degree: string;
    major?: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    grade?: string;
  }): Promise<{ success: boolean; id: number }> {
    const response = await fetch(`${API_BASE_URL}/api/profile/education`, {
      method: 'POST',
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error('Failed to add education');
    }

    return response.json();
  }

  async deleteEducation(id: number): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/profile/education/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeader()
    });

    if (!response.ok) {
      throw new Error('Failed to delete education');
    }

    return response.json();
  }

  // Experience
  async addExperience(data: {
    role: string;
    company: string;
    location?: string;
    start_date?: string;
    end_date?: string;
    description?: string;
  }): Promise<{ success: boolean; id: number }> {
    const response = await fetch(`${API_BASE_URL}/api/profile/experience`, {
      method: 'POST',
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error('Failed to add experience');
    }

    return response.json();
  }

  async deleteExperience(id: number): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/profile/experience/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeader()
    });

    if (!response.ok) {
      throw new Error('Failed to delete experience');
    }

    return response.json();
  }

  // Projects
  async addProject(data: {
    title: string;
    description?: string;
    tech_stack?: string;
    link?: string;
  }): Promise<{ success: boolean; id: number }> {
    const response = await fetch(`${API_BASE_URL}/api/profile/project`, {
      method: 'POST',
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error('Failed to add project');
    }

    return response.json();
  }

  async deleteProject(id: number): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/profile/project/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeader()
    });

    if (!response.ok) {
      throw new Error('Failed to delete project');
    }

    return response.json();
  }

  // Skills
  async addSkill(data: {
    skill: string;
    category?: string;
    level?: string;
  }): Promise<{ success: boolean; id: number }> {
    const response = await fetch(`${API_BASE_URL}/api/profile/skill`, {
      method: 'POST',
      headers: {
        ...this.getAuthHeader(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error('Failed to add skill');
    }

    return response.json();
  }

  async deleteSkill(id: number): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/profile/skill/${id}`, {
      method: 'DELETE',
      headers: this.getAuthHeader()
    });

    if (!response.ok) {
      throw new Error('Failed to delete skill');
    }

    return response.json();
  }
}

export const profileService = new ProfileService();

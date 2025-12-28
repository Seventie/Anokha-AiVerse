// frontend/services/authService.ts (UPDATED)

import { apiService } from './apiService';

export interface EducationEntry {
  institution: string;
  degree: string;
  major: string;
  location: string;
  duration: string;
}

export interface ExperienceEntry {
  role: string;
  company: string;
  location: string;
  duration: string;
  description: string;
}

export interface ProjectEntry {
  title: string;
  description: string;
  techStack: string;
}

export interface User {
  id: string;
  fullName?: string;
  email: string;
  username?: string;
  password?: string;
  location?: string;
  preferredLocations?: string[];
  currentStatus?: string;
  fieldOfInterest?: string;
  education?: EducationEntry[];
  experience?: ExperienceEntry[];
  projects?: ProjectEntry[];
  skills?: { technical?: string[]; soft?: string[] };
  availability?: { freeTime?: string; studyDays?: string[] };
  targetRole?: string;
  timeline?: string;
  visionStatement?: string;
  createdAt?: string;
  isDemo?: boolean;
}

export const authService = {
  register: async (user: Omit<User, 'id' | 'createdAt'>): Promise<User | null> => {
    const response = await apiService.register(user);
    if (response.error) {
      console.error('Registration failed:', response.error);
      return null;
    }
    // New response format includes { user, access_token, token_type }
    return (response.data as any)?.user as User || response.data as User;
  },

  login: async (email: string, password?: string): Promise<User | null> => {
    const response = await apiService.login(email, password || '');
    if (response.error) {
      console.error('Login failed:', response.error);
      return null;
    }

    // Get user profile after login
    const userResponse = await apiService.getCurrentUser();
    if (userResponse.error) {
      console.error('Failed to get user profile:', userResponse.error);
      return null;
    }

    return userResponse.data as User;
  },

  getSession: async (): Promise<User | null> => {
    const response = await apiService.getCurrentUser();
    if (response.error) {
      return null;
    }
    return response.data as User;
  },

  logout: () => {
    apiService.logout();
  },

  // Legacy methods for backward compatibility
  setSession: (user: User) => {
    // Token is already stored in apiService
    console.log('Session set for user:', user.email);
  },
};
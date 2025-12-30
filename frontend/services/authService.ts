// frontend/src/services/authService.ts

import { apiService } from './apiService';

export interface User {
  id: string;
  email: string;
  username: string;
  fullName: string;
  location?: string;
  preferredLocations?: string[];
  currentStatus?: string;
  fieldOfInterest?: string;
  targetRole?: string;
  timeline?: string;
  visionStatement?: string;
  readiness_level?: string;
  is_demo?: boolean;
  created_at?: string;
  education?: any[];
  skills?: any[];
  projects?: any[];
  experience?: any[];
  availability?: any;
}

interface AuthResponse {
  user?: User;
  error?: string;
}

class AuthService {
  async login(email: string, password: string): Promise<AuthResponse> {
    try {
      console.log('🔐 AuthService: Logging in with', email);
      
      const response = await apiService.login(email, password);
      
      if (response.error) {
        console.error('❌ AuthService: Login failed:', response.error);
        return { error: response.error };
      }
      
      if (response.data?.access_token) {
        console.log('✅ AuthService: Token received, fetching user profile...');
        
        // Fetch user profile
        const userResponse = await apiService.getCurrentUser();
        
        if (userResponse.error) {
          console.error('❌ AuthService: Failed to fetch user:', userResponse.error);
          return { error: userResponse.error };
        }
        
        if (userResponse.data) {
          console.log('✅ AuthService: User profile loaded:', userResponse.data);
          return { user: userResponse.data as User };
        }
      }
      
      return { error: 'Login failed. Please try again.' };
    } catch (error: any) {
      console.error('❌ AuthService: Login exception:', error);
      return { error: error.message || 'Login failed. Please try again.' };
    }
  }

  async getCurrentUser(): Promise<AuthResponse> {
    try {
      const response = await apiService.getCurrentUser();
      
      if (response.error) {
        return { error: response.error };
      }
      
      if (response.data) {
        return { user: response.data as User };
      }
      
      return { error: 'Failed to fetch user profile' };
    } catch (error: any) {
      return { error: error.message || 'Failed to fetch user profile' };
    }
  }

  logout(): void {
    apiService.logout();
  }

  isAuthenticated(): boolean {
    return !!apiService.getToken();
  }
}

export const authService = new AuthService();

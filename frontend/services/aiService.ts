
import { GoogleGenAI, Type } from "@google/genai";

export const aiService = {
  suggestLocations: async (query: string, lat?: number, lng?: number) => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    try {
      const response = await ai.models.generateContent({
        model: 'gemini-2.5-flash',
        contents: `Provide a list of 5 real city/region names matching this search query: "${query}". Return as a JSON array of strings.`,
        config: {
          tools: [{ googleMaps: {} }],
          toolConfig: {
            retrievalConfig: {
              latLng: lat && lng ? { latitude: lat, longitude: lng } : undefined
            }
          },
        },
      });
      const text = response.text || "";
      const cities = text.match(/["']([^"']+)["']/g)?.map(c => c.replace(/["']/g, '')) || [];
      return cities.length > 0 ? cities.slice(0, 5) : [query];
    } catch (error) {
      return [query];
    }
  },

  parseResume: async (text: string) => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    try {
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `Analyze this resume and return structured JSON for: fullName, location, education (institution, degree, major, duration), experience (role, company, duration, description), projects (title, techStack, description), skills (technical, soft). Text: ${text}`,
        config: {
          responseMimeType: "application/json",
          responseSchema: {
            type: Type.OBJECT,
            properties: {
              fullName: { type: Type.STRING },
              location: { type: Type.STRING },
              education: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { institution: { type: Type.STRING }, degree: { type: Type.STRING }, major: { type: Type.STRING }, duration: { type: Type.STRING } } } },
              experience: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { role: { type: Type.STRING }, company: { type: Type.STRING }, duration: { type: Type.STRING }, description: { type: Type.STRING } } } },
              projects: { type: Type.ARRAY, items: { type: Type.OBJECT, properties: { title: { type: Type.STRING }, techStack: { type: Type.STRING }, description: { type: Type.STRING } } } },
              skills: { type: Type.OBJECT, properties: { technical: { type: Type.ARRAY, items: { type: Type.STRING } }, soft: { type: Type.ARRAY, items: { type: Type.STRING } } } }
            }
          }
        }
      });
      return JSON.parse(response.text || '{}');
    } catch (error) {
      return null;
    }
  },

  getAgentReasoning: async (userProfile: any) => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    try {
      const response = await ai.models.generateContent({
        model: 'gemini-3-pro-preview',
        contents: `You are a career mentor. Based on this profile: ${JSON.stringify(userProfile)}, provide a 3-paragraph strategic monologue. Identify the biggest skill gap and one high-leverage move for this week.`,
        config: { 
          systemInstruction: "Tonal Directive: Insightful, slightly futuristic, professional. Max 150 words." 
        }
      });
      return response.text;
    } catch (error) {
      return "Strategic analysis recalibrating. Based on your current profile, focus on consolidating your technical stack into high-impact projects.";
    }
  },

  generateRoadmap: async (userProfile: any) => {
    const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
    try {
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `Generate a 4-phase career roadmap to transition from ${userProfile.currentStatus} to ${userProfile.targetRole}. User skills: ${userProfile.skills.technical.join(', ')}. Profile: ${userProfile.visionStatement}`,
        config: {
          responseMimeType: "application/json",
          responseSchema: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                phase: { type: Type.STRING },
                title: { type: Type.STRING },
                tasks: { type: Type.ARRAY, items: { type: Type.STRING } },
                status: { type: Type.STRING }
              }
            }
          }
        }
      });
      return JSON.parse(response.text || '[]');
    } catch (error) {
      return null;
    }
  }
};

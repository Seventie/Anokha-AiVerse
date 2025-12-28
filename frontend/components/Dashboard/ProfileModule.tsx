// frontend/components/Dashboard/ProfileModule.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { agentService } from '../../services/agentService';
import { 
  UserCircle, Edit3, Save, CheckCircle, 
  AlertCircle, TrendingUp, Loader2, 
  Target, MapPin, Calendar, Award, Sparkles
} from 'lucide-react';

interface ProfileModuleProps {
  user: User;
}

const ProfileModule: React.FC<ProfileModuleProps> = ({ user }) => {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<any>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await agentService.getProfileAnalysis(user.id);
      setProfile(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load profile:', error);
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await agentService.updateProfile(user.id, editData);
      setEditing(false);
      loadProfile();
      alert('Profile updated successfully!');
    } catch (error) {
      console.error('Failed to update:', error);
      alert('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const startEditing = () => {
    setEditData({
      targetRole: user.targetRole || '',
      timeline: user.timeline || '',
      visionStatement: user.visionStatement || '',
      location: user.location || ''
    });
    setEditing(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Profile Management</h2>
          <p className="text-white/60">Manage your career profile and goals</p>
        </div>
        {!editing && (
          <button
            onClick={startEditing}
            className="px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary rounded-2xl flex items-center gap-3 transition-all border border-primary/30"
          >
            <Edit3 size={20} />
            Edit Profile
          </button>
        )}
      </div>

      {/* Completeness Score */}
      {profile?.completeness_score !== undefined && (
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium flex items-center gap-3">
              <TrendingUp size={20} className="text-primary" />
              Profile Completeness
            </h3>
            <span className="text-2xl font-bold text-primary">
              {profile.completeness_score}%
            </span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-3">
            <div
              className="bg-primary h-3 rounded-full transition-all"
              style={{ width: `${profile.completeness_score}%` }}
            />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Profile Information */}
        <div className="space-y-6">
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
              <UserCircle size={20} className="text-primary" />
              Personal Information
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/60 mb-2">Full Name</label>
                <input
                  type="text"
                  value={user.fullName}
                  disabled
                  className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Email</label>
                <input
                  type="email"
                  value={user.email}
                  disabled
                  className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white disabled:opacity-50"
                />
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Location</label>
                {editing ? (
                  <input
                    type="text"
                    value={editData.location || ''}
                    onChange={(e) => setEditData({ ...editData, location: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                  />
                ) : (
                  <div className="flex items-center gap-2 text-white/80">
                    <MapPin size={16} />
                    <span>{user.location || 'Not set'}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Career Goals */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
              <Target size={20} className="text-primary" />
              Career Goals
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/60 mb-2">Target Role</label>
                {editing ? (
                  <input
                    type="text"
                    value={editData.targetRole || ''}
                    onChange={(e) => setEditData({ ...editData, targetRole: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                  />
                ) : (
                  <p className="text-white/80">{user.targetRole || 'Not set'}</p>
                )}
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Timeline</label>
                {editing ? (
                  <input
                    type="text"
                    value={editData.timeline || ''}
                    onChange={(e) => setEditData({ ...editData, timeline: e.target.value })}
                    placeholder="e.g., 6 Months"
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                  />
                ) : (
                  <div className="flex items-center gap-2 text-white/80">
                    <Calendar size={16} />
                    <span>{user.timeline}</span>
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Vision Statement</label>
                {editing ? (
                  <textarea
                    value={editData.visionStatement || ''}
                    onChange={(e) => setEditData({ ...editData, visionStatement: e.target.value })}
                    rows={4}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50 resize-none"
                  />
                ) : (
                  <p className="text-white/80">{user.visionStatement || 'Not set'}</p>
                )}
              </div>
            </div>
          </div>

          {editing && (
            <div className="flex gap-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex-1 px-6 py-4 bg-primary text-bg-deep rounded-2xl font-bold flex items-center justify-center gap-3 hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
              >
                {saving ? (
                  <>
                    <Loader2 size={20} className="animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save size={20} />
                    Save Changes
                  </>
                )}
              </button>
              <button
                onClick={() => setEditing(false)}
                className="px-6 py-4 bg-white/10 hover:bg-white/20 rounded-2xl transition-all"
              >
                Cancel
              </button>
            </div>
          )}
        </div>

        {/* Analysis & Recommendations */}
        <div className="space-y-6">
          {/* Missing Sections */}
          {profile?.missing_sections && profile.missing_sections.length > 0 && (
            <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                <AlertCircle size={20} className="text-yellow-400" />
                Missing Information
              </h3>
              <ul className="space-y-2">
                {profile.missing_sections.map((section: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-3 text-white/80">
                    <AlertCircle size={16} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                    <span>{section}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Recommendations */}
          {profile?.recommendations && profile.recommendations.length > 0 && (
            <div className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 rounded-[2rem] p-6">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                <Sparkles size={20} className="text-primary" />
                Recommendations
              </h3>
              <div className="space-y-3">
                {profile.recommendations.map((rec: any, idx: number) => (
                  <div key={idx} className="p-4 bg-white/5 rounded-xl">
                    <div className="flex items-start gap-3">
                      <CheckCircle size={18} className="text-primary mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <p className="text-white/90 font-medium">{rec.suggestion || rec}</p>
                        {rec.section && (
                          <p className="text-xs text-white/40 mt-1">Section: {rec.section}</p>
                        )}
                        {rec.impact && (
                          <p className="text-xs text-white/60 mt-1">{rec.impact}</p>
                        )}
                      </div>
                      {rec.priority && (
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          rec.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                          rec.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                          'bg-green-500/20 text-green-400'
                        }`}>
                          {rec.priority}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skills Summary */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
              <Award size={20} className="text-primary" />
              Skills Summary
            </h3>
            <div className="space-y-3">
              <div>
                <p className="text-sm text-white/60 mb-2">Technical Skills</p>
                <div className="flex flex-wrap gap-2">
                  {user.skills?.technical?.slice(0, 8).map((skill: string, idx: number) => (
                    <span key={idx} className="px-3 py-1 bg-primary/10 text-primary rounded-full text-xs">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
              {user.skills?.soft && user.skills.soft.length > 0 && (
                <div>
                  <p className="text-sm text-white/60 mb-2">Soft Skills</p>
                  <div className="flex flex-wrap gap-2">
                    {user.skills.soft.slice(0, 6).map((skill: string, idx: number) => (
                      <span key={idx} className="px-3 py-1 bg-blue-500/10 text-blue-400 rounded-full text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Education & Experience Summary */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <h3 className="text-lg font-medium mb-4">Quick Stats</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-white/60">Education</span>
                <span className="text-white/80 font-medium">{user.education?.length || 0} entries</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/60">Experience</span>
                <span className="text-white/80 font-medium">{user.experience?.length || 0} positions</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-white/60">Projects</span>
                <span className="text-white/80 font-medium">{user.projects?.length || 0} projects</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfileModule;


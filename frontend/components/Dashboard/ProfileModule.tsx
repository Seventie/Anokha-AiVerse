// frontend/components/Dashboard/ProfileModule.tsx - FIXED VERSION

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { profileService, CompleteProfile } from '../../services/profileService';
import { resumeService } from '../../services/resumeService';
import { 
  UserCircle, Edit3, Save, CheckCircle, 
  AlertCircle, TrendingUp, Loader2, 
  Target, MapPin, Calendar, Award, Sparkles,
  Plus, Trash2, Briefcase, GraduationCap,
  Code, Upload, File, X
} from 'lucide-react';

interface ProfileModuleProps {
  user: User;
}

const ProfileModule: React.FC<ProfileModuleProps> = ({ user }) => {
  const [profile, setProfile] = useState<CompleteProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState<any>({});
  const [saving, setSaving] = useState(false);
  
  // Modal states
  const [showAddEducation, setShowAddEducation] = useState(false);
  const [showAddExperience, setShowAddExperience] = useState(false);
  const [showAddProject, setShowAddProject] = useState(false);
  const [showAddSkill, setShowAddSkill] = useState(false);
  const [showResumeUpload, setShowResumeUpload] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await profileService.getCompleteProfile();
      setProfile(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load profile:', error);
      setLoading(false);
    }
  };

  const handleSaveBasic = async () => {
    setSaving(true);
    try {
      await profileService.updateBasicProfile(editData);
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
    if (!profile) return;
    
    // FIX: Safe null/undefined handling
    const targetRole = profile.career_goals?.target_roles?.[0] || '';
    const timeline = profile.career_goals?.timeline || '';
    const visionStatement = profile.career_goals?.vision_statement || '';
    
    setEditData({
      full_name: profile.profile?.full_name || '',
      location: profile.profile?.location || '',
      target_role: targetRole,
      timeline: timeline,
      vision_statement: visionStatement
    });
    setEditing(true);
  };

  const handleDeleteItem = async (type: string, id: number) => {
    if (!confirm('Are you sure you want to delete this?')) return;
    
    try {
      switch (type) {
        case 'education':
          await profileService.deleteEducation(id);
          break;
        case 'experience':
          await profileService.deleteExperience(id);
          break;
        case 'project':
          await profileService.deleteProject(id);
          break;
        case 'skill':
          await profileService.deleteSkill(id);
          break;
      }
      loadProfile();
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Failed to delete item');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  if (!profile) {
    return <div className="text-center py-20 text-white/60">Failed to load profile</div>;
  }

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Profile Management</h2>
          <p className="text-white/60">Manage your complete career profile</p>
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
      <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium flex items-center gap-3">
            <TrendingUp size={20} className="text-primary" />
            Profile Completeness
          </h3>
          <span className="text-2xl font-bold text-primary">
            {profile.completeness_score || 0}%
          </span>
        </div>
        <div className="w-full bg-white/10 rounded-full h-3">
          <div
            className="bg-primary h-3 rounded-full transition-all"
            style={{ width: `${profile.completeness_score || 0}%` }}
          />
        </div>
        
        {/* Missing Sections */}
        {profile.missing_sections && profile.missing_sections.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-sm text-white/60">To improve your profile:</p>
            {profile.missing_sections.map((section, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm text-white/80">
                <AlertCircle size={16} className="text-yellow-400 mt-0.5 flex-shrink-0" />
                <span>{section}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* LEFT COLUMN */}
        <div className="space-y-6">
          
          {/* Basic Info */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
              <UserCircle size={20} className="text-primary" />
              Personal Information
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-white/60 mb-2">Full Name</label>
                {editing ? (
                  <input
                    type="text"
                    value={editData.full_name || ''}
                    onChange={(e) => setEditData({ ...editData, full_name: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                  />
                ) : (
                  <p className="text-white/80">{profile.profile?.full_name || 'Not set'}</p>
                )}
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Email</label>
                <p className="text-white/80">{profile.profile?.email || 'Not set'}</p>
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
                    <span>{profile.profile?.location || 'Not set'}</span>
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
                    value={editData.target_role || ''}
                    onChange={(e) => setEditData({ ...editData, target_role: e.target.value })}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                  />
                ) : (
                  <p className="text-white/80">
                    {profile.career_goals?.target_roles?.[0] || 'Not set'}
                  </p>
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
                    <span>{profile.career_goals?.timeline || 'Not set'}</span>
                  </div>
                )}
              </div>
              <div>
                <label className="block text-sm text-white/60 mb-2">Vision Statement</label>
                {editing ? (
                  <textarea
                    value={editData.vision_statement || ''}
                    onChange={(e) => setEditData({ ...editData, vision_statement: e.target.value })}
                    rows={4}
                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50 resize-none"
                  />
                ) : (
                  <p className="text-white/80">{profile.career_goals?.vision_statement || 'Not set'}</p>
                )}
              </div>
            </div>
          </div>

          {editing && (
            <div className="flex gap-3">
              <button
                onClick={handleSaveBasic}
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

          {/* Resume */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium flex items-center gap-3">
                <File size={20} className="text-primary" />
                Resume
              </h3>
              <button
                onClick={() => setShowResumeUpload(true)}
                className="px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl flex items-center gap-2 transition-all text-sm"
              >
                <Upload size={16} />
                Upload New
              </button>
            </div>
            {profile.resume ? (
              <div className="p-4 bg-white/5 rounded-xl">
                <p className="text-white/90 font-medium">{profile.resume.filename || 'Resume'}</p>
                <p className="text-xs text-white/40 mt-1">
                  Uploaded {new Date(profile.resume.uploaded_at).toLocaleDateString()}
                </p>
              </div>
            ) : (
              <p className="text-white/60 text-sm">No resume uploaded yet</p>
            )}
          </div>
        </div>

        {/* RIGHT COLUMN */}
        <div className="space-y-6">
          
          {/* Education */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium flex items-center gap-3">
                <GraduationCap size={20} className="text-primary" />
                Education
              </h3>
              <button
                onClick={() => setShowAddEducation(true)}
                className="p-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl transition-all"
              >
                <Plus size={20} />
              </button>
            </div>
            {profile.education && profile.education.length > 0 ? (
              <div className="space-y-3">
                {profile.education.map((edu) => (
                  <div key={edu.id} className="p-4 bg-white/5 rounded-xl group">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-white/90">{edu.degree || 'Degree'}</h4>
                        <p className="text-sm text-white/70">{edu.institution}</p>
                        {edu.major && <p className="text-xs text-white/50">{edu.major}</p>}
                        <p className="text-xs text-white/40 mt-1">
                          {edu.start_date} - {edu.end_date || 'Present'}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteItem('education', edu.id)}
                        className="opacity-0 group-hover:opacity-100 p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-all"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/60 text-sm">No education added yet</p>
            )}
          </div>

          {/* Experience */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium flex items-center gap-3">
                <Briefcase size={20} className="text-primary" />
                Experience
              </h3>
              <button
                onClick={() => setShowAddExperience(true)}
                className="p-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl transition-all"
              >
                <Plus size={20} />
              </button>
            </div>
            {profile.experience && profile.experience.length > 0 ? (
              <div className="space-y-3">
                {profile.experience.map((exp) => (
                  <div key={exp.id} className="p-4 bg-white/5 rounded-xl group">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-white/90">{exp.role}</h4>
                        <p className="text-sm text-white/70">{exp.company}</p>
                        <p className="text-xs text-white/40 mt-1">
                          {exp.start_date} - {exp.end_date || 'Present'}
                        </p>
                        {exp.description && (
                          <p className="text-xs text-white/60 mt-2 line-clamp-2">{exp.description}</p>
                        )}
                      </div>
                      <button
                        onClick={() => handleDeleteItem('experience', exp.id)}
                        className="opacity-0 group-hover:opacity-100 p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-all"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/60 text-sm">No experience added yet</p>
            )}
          </div>

          {/* Projects */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium flex items-center gap-3">
                <Code size={20} className="text-primary" />
                Projects
              </h3>
              <button
                onClick={() => setShowAddProject(true)}
                className="p-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl transition-all"
              >
                <Plus size={20} />
              </button>
            </div>
            {profile.projects && profile.projects.length > 0 ? (
              <div className="space-y-3">
                {profile.projects.map((proj) => (
                  <div key={proj.id} className="p-4 bg-white/5 rounded-xl group">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-white/90">{proj.title}</h4>
                        {proj.description && (
                          <p className="text-sm text-white/70 mt-1 line-clamp-2">{proj.description}</p>
                        )}
                        {proj.tech_stack && (
                          <p className="text-xs text-primary mt-2">{proj.tech_stack}</p>
                        )}
                      </div>
                      <button
                        onClick={() => handleDeleteItem('project', proj.id)}
                        className="opacity-0 group-hover:opacity-100 p-2 hover:bg-red-500/20 text-red-400 rounded-lg transition-all"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/60 text-sm">No projects added yet</p>
            )}
          </div>

          {/* Skills */}
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium flex items-center gap-3">
                <Award size={20} className="text-primary" />
                Skills ({profile.skills?.length || 0})
              </h3>
              <button
                onClick={() => setShowAddSkill(true)}
                className="p-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl transition-all"
              >
                <Plus size={20} />
              </button>
            </div>
            {profile.skills && profile.skills.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((skill) => (
                  <div
                    key={skill.id}
                    className="group px-3 py-2 bg-primary/10 text-primary rounded-xl text-sm flex items-center gap-2 hover:bg-primary/20 transition-all"
                  >
                    <span>{skill.skill || 'Skill'}</span>
                    <button
                      onClick={() => handleDeleteItem('skill', skill.id)}
                      className="opacity-0 group-hover:opacity-100"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-white/60 text-sm">No skills added yet</p>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {showAddEducation && <AddEducationModal onClose={() => { setShowAddEducation(false); loadProfile(); }} />}
      {showAddExperience && <AddExperienceModal onClose={() => { setShowAddExperience(false); loadProfile(); }} />}
      {showAddProject && <AddProjectModal onClose={() => { setShowAddProject(false); loadProfile(); }} />}
      {showAddSkill && <AddSkillModal onClose={() => { setShowAddSkill(false); loadProfile(); }} />}
      {showResumeUpload && <ResumeUploadModal onClose={() => { setShowResumeUpload(false); loadProfile(); }} />}
    </div>
  );
};

// ==================== MODALS ====================
const AddEducationModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [formData, setFormData] = useState({
    institution: '',
    degree: '',
    major: '',
    location: '',
    start_date: '',
    end_date: '',
    grade: ''
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await profileService.addEducation(formData);
      onClose();
    } catch (error) {
      console.error('Failed to add education:', error);
      alert('Failed to add education');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-bg-deep border border-white/10 rounded-[2rem] p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-light">Add Education</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-all">
            <X size={24} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-white/60 mb-2">Institution *</label>
            <input
              type="text"
              required
              value={formData.institution}
              onChange={(e) => setFormData({ ...formData, institution: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="e.g., Stanford University"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-white/60 mb-2">Degree *</label>
              <input
                type="text"
                required
                value={formData.degree}
                onChange={(e) => setFormData({ ...formData, degree: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                placeholder="e.g., B.Tech"
              />
            </div>
            <div>
              <label className="block text-sm text-white/60 mb-2">Major</label>
              <input
                type="text"
                value={formData.major}
                onChange={(e) => setFormData({ ...formData, major: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                placeholder="e.g., Computer Science"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="e.g., Bangalore, India"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-white/60 mb-2">Start Date</label>
              <input
                type="text"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                placeholder="e.g., Aug 2020"
              />
            </div>
            <div>
              <label className="block text-sm text-white/60 mb-2">End Date</label>
              <input
                type="text"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                placeholder="e.g., May 2024 or Present"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">GPA/Grade</label>
            <input
              type="text"
              value={formData.grade}
              onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="e.g., 3.8/4.0"
            />
          </div>
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-6 py-3 bg-primary text-bg-deep rounded-xl font-bold hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
            >
              {saving ? 'Adding...' : 'Add Education'}
            </button>
            <button type="button" onClick={onClose} className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const AddExperienceModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [formData, setFormData] = useState({
    role: '',
    company: '',
    location: '',
    start_date: '',
    end_date: '',
    description: ''
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await profileService.addExperience(formData);
      onClose();
    } catch (error) {
      console.error('Failed to add experience:', error);
      alert('Failed to add experience');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-bg-deep border border-white/10 rounded-[2rem] p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-light">Add Experience</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-all">
            <X size={24} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-white/60 mb-2">Role/Position *</label>
            <input
              type="text"
              required
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="e.g., Software Engineer"
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">Company *</label>
            <input
              type="text"
              required
              value={formData.company}
              onChange={(e) => setFormData({ ...formData, company: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="e.g., Google"
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">Location</label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="e.g., Remote / San Francisco, CA"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-white/60 mb-2">Start Date</label>
              <input
                type="text"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                placeholder="e.g., Jan 2023"
              />
            </div>
            <div>
              <label className="block text-sm text-white/60 mb-2">End Date</label>
              <input
                type="text"
                value={formData.end_date}
                onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
                placeholder="e.g., Present"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50 resize-none"
              placeholder="Describe your responsibilities and achievements..."
            />
          </div>
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-6 py-3 bg-primary text-bg-deep rounded-xl font-bold hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
            >
              {saving ? 'Adding...' : 'Add Experience'}
            </button>
            <button type="button" onClick={onClose} className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const AddProjectModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    tech_stack: '',
    link: ''
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await profileService.addProject(formData);
      onClose();
    } catch (error) {
      console.error('Failed to add project:', error);
      alert('Failed to add project');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-bg-deep border border-white/10 rounded-[2rem] p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-light">Add Project</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-all">
            <X size={24} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-white/60 mb-2">Project Title *</label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="e.g., E-commerce Platform"
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50 resize-none"
              placeholder="Describe what the project does and your role..."
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">Tech Stack</label>
            <input
              type="text"
              value={formData.tech_stack}
              onChange={(e) => setFormData({ ...formData, tech_stack: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="e.g., React, Node.js, MongoDB"
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">Project Link</label>
            <input
              type="url"
              value={formData.link}
              onChange={(e) => setFormData({ ...formData, link: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="https://github.com/username/project"
            />
          </div>
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-6 py-3 bg-primary text-bg-deep rounded-xl font-bold hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
            >
              {saving ? 'Adding...' : 'Add Project'}
            </button>
            <button type="button" onClick={onClose} className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const AddSkillModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [formData, setFormData] = useState({
    skill: '',
    category: 'technical',
    level: 'intermediate'
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await profileService.addSkill(formData);
      onClose();
    } catch (error) {
      console.error('Failed to add skill:', error);
      alert('Failed to add skill');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-bg-deep border border-white/10 rounded-[2rem] p-6 max-w-lg w-full">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-light">Add Skill</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-all">
            <X size={24} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-white/60 mb-2">Skill Name *</label>
            <input
              type="text"
              required
              value={formData.skill}
              onChange={(e) => setFormData({ ...formData, skill: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
              placeholder="e.g., React, Python, Leadership"
            />
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">Category</label>
            <select
              value={formData.category}
              onChange={(e) => setFormData({ ...formData, category: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
            >
              <option value="technical">Technical</option>
              <option value="soft">Soft Skill</option>
              <option value="domain">Domain Knowledge</option>
              <option value="tool">Tool/Software</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-white/60 mb-2">Proficiency Level</label>
            <select
              value={formData.level}
              onChange={(e) => setFormData({ ...formData, level: e.target.value })}
              className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-primary/50"
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="expert">Expert</option>
            </select>
          </div>
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-6 py-3 bg-primary text-bg-deep rounded-xl font-bold hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
            >
              {saving ? 'Adding...' : 'Add Skill'}
            </button>
            <button type="button" onClick={onClose} className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const ResumeUploadModal: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setUploading(true);
    try {
      await resumeService.uploadResume(file);
      alert('Resume uploaded successfully!');
      onClose();
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Failed to upload resume');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-bg-deep border border-white/10 rounded-[2rem] p-6 max-w-lg w-full">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-light">Upload Resume</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-all">
            <X size={24} />
          </button>
        </div>
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-8 text-center transition-all ${
            dragActive ? 'border-primary bg-primary/10' : 'border-white/20 hover:border-white/40'
          }`}
        >
          <Upload size={48} className="mx-auto mb-4 text-white/40" />
          
          {file ? (
            <div className="space-y-2">
              <p className="text-white/90 font-medium">{file.name}</p>
              <p className="text-sm text-white/60">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
              <button
                onClick={() => setFile(null)}
                className="text-sm text-red-400 hover:text-red-300 transition-all"
              >
                Remove
              </button>
            </div>
          ) : (
            <div>
              <p className="text-white/80 mb-2">
                Drag & drop your resume here
              </p>
              <p className="text-sm text-white/40 mb-4">or</p>
              <label className="px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl inline-flex items-center gap-2 cursor-pointer transition-all">
                <File size={20} />
                Browse Files
                <input
                  type="file"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileChange}
                  className="hidden"
                />
              </label>
              <p className="text-xs text-white/40 mt-4">
                Supported: PDF, DOC, DOCX (Max 10MB)
              </p>
            </div>
          )}
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="flex-1 px-6 py-3 bg-primary text-bg-deep rounded-xl font-bold hover:shadow-[0_0_40px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? (
              <>
                <Loader2 size={20} className="inline animate-spin mr-2" />
                Uploading...
              </>
            ) : (
              'Upload Resume'
            )}
          </button>
          <button
            onClick={onClose}
            className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfileModule;
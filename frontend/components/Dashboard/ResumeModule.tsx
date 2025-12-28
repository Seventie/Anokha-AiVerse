// frontend/src/components/Dashboard/ResumeModule.tsx

import React, { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, CheckCircle, AlertCircle, Download } from 'lucide-react';
import { resumeService, ParsedResume, ResumeHistoryItem } from '../../services/resumeService';

const ResumeModule: React.FC = () => {
  const [currentResume, setCurrentResume] = useState<ParsedResume | null>(null);
  const [history, setHistory] = useState<ResumeHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    loadResume();
    loadHistory();
  }, []);

  const loadResume = async () => {
    try {
      const data = await resumeService.getCurrentResume();
      if (data) {
        setCurrentResume(data.parsed_data);
      }
    } catch (error) {
      console.error('Failed to load resume:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await resumeService.getResumeHistory();
      setHistory(data);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const result = await resumeService.uploadResume(selectedFile);
      setCurrentResume(result.data);
      setSelectedFile(null);
      loadHistory();
      alert('✅ Resume uploaded and parsed successfully!');
    } catch (error: any) {
      alert(`Failed to upload: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
    } else {
      alert('Please select a PDF file');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8">
      {/* Upload Section */}
      <div className="bg-white rounded-2xl border border-gray-200 p-6">
        <h2 className="text-2xl font-bold mb-4">Upload Resume</h2>
        
        <div className="flex items-center gap-4">
          <label className="flex-1 cursor-pointer">
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 hover:border-primary transition-colors">
              <div className="text-center">
                <Upload className="mx-auto mb-2 text-gray-400" size={40} />
                <p className="text-sm text-gray-600">
                  {selectedFile ? selectedFile.name : 'Click to upload PDF resume'}
                </p>
              </div>
            </div>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>

          {selectedFile && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary/90 disabled:opacity-50"
            >
              {uploading ? 'Parsing...' : 'Upload & Parse'}
            </button>
          )}
        </div>
      </div>

      {/* Current Resume */}
      {currentResume && (
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">Current Resume</h2>
            <CheckCircle className="text-green-500" />
          </div>

          <div className="space-y-6">
            {/* Personal Info */}
            <div>
              <h3 className="font-semibold text-lg mb-2">Personal Information</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div><span className="text-gray-500">Name:</span> {currentResume.personal_info.fullName || 'N/A'}</div>
                <div><span className="text-gray-500">Email:</span> {currentResume.personal_info.email || 'N/A'}</div>
                <div><span className="text-gray-500">Phone:</span> {currentResume.personal_info.phone || 'N/A'}</div>
                <div><span className="text-gray-500">Location:</span> {currentResume.personal_info.location || 'N/A'}</div>
              </div>
            </div>

            {/* Skills */}
            <div>
              <h3 className="font-semibold text-lg mb-2">Skills</h3>
              <div className="flex flex-wrap gap-2">
                {currentResume.skills.technical.map((skill, idx) => (
                  <span key={idx} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            {/* Education */}
            {currentResume.education.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-2">Education</h3>
                {currentResume.education.map((edu, idx) => (
                  <div key={idx} className="mb-2">
                    <p className="font-medium">{edu.degree}</p>
                    <p className="text-sm text-gray-600">{edu.institution} • {edu.year}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Experience */}
            {currentResume.experience.length > 0 && (
              <div>
                <h3 className="font-semibold text-lg mb-2">Experience</h3>
                {currentResume.experience.map((exp, idx) => (
                  <div key={idx} className="mb-4">
                    <p className="font-medium">{exp.title} at {exp.company}</p>
                    <p className="text-sm text-gray-600">{exp.duration}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          <h2 className="text-2xl font-bold mb-4">Upload History</h2>
          <div className="space-y-2">
            {history.map(item => (
              <div key={item.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                <div className="flex items-center gap-3">
                  <FileText className="text-gray-400" size={20} />
                  <div>
                    <p className="font-medium text-sm">{item.filename}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(item.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                {item.is_active && (
                  <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                    Active
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResumeModule;

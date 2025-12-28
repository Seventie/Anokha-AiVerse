// frontend/src/components/Interview/InterviewSetup.tsx

import React, { useState } from 'react';
import { interviewService } from '../../services/interviewService';

interface Props {
  onInterviewCreated: (interviewId: string) => void;
  onCancel: () => void;
}

const InterviewSetup: React.FC<Props> = ({ onInterviewCreated, onCancel }) => {
  const [interviewType, setInterviewType] = useState<'company_specific' | 'custom_topic'>('company_specific');
  const [companyName, setCompanyName] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [customTopics, setCustomTopics] = useState<string[]>([]);
  const [topicInput, setTopicInput] = useState('');
  const [totalRounds, setTotalRounds] = useState(1);
  const [roundConfigs, setRoundConfigs] = useState([
    { type: 'technical' as const, difficulty: 'medium' as const }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const addTopic = () => {
    if (topicInput.trim()) {
      setCustomTopics([...customTopics, topicInput.trim()]);
      setTopicInput('');
    }
  };

  const removeTopic = (index: number) => {
    setCustomTopics(customTopics.filter((_, i) => i !== index));
  };

  const updateRound = (index: number, field: 'type' | 'difficulty', value: string) => {
    const updated = [...roundConfigs];
    updated[index] = { ...updated[index], [field]: value };
    setRoundConfigs(updated);
  };

  const addRound = () => {
    if (roundConfigs.length < 3) {
      setRoundConfigs([...roundConfigs, { type: 'technical', difficulty: 'medium' }]);
      setTotalRounds(totalRounds + 1);
    }
  };

  const removeRound = (index: number) => {
    if (roundConfigs.length > 1) {
      setRoundConfigs(roundConfigs.filter((_, i) => i !== index));
      setTotalRounds(totalRounds - 1);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (interviewType === 'company_specific' && !companyName.trim()) {
        setError('Company name is required');
        setLoading(false);
        return;
      }

      const data = {
        interview_type: interviewType,
        company_name: interviewType === 'company_specific' ? companyName : undefined,
        job_description: interviewType === 'company_specific' ? jobDescription : undefined,
        custom_topics: interviewType === 'custom_topic' ? customTopics : undefined,
        total_rounds: totalRounds,
        round_configs: roundConfigs
      };

      console.log('📤 Creating interview with data:', data);
      const interview = await interviewService.createInterview(data);
      console.log('✅ Interview created:', interview);
      onInterviewCreated(interview.id);
    } catch (err: any) {
      console.error('❌ Failed to create interview:', err);
      setError(err.message || 'Failed to create interview');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#1a3a35] text-white py-12 px-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-5xl font-light mb-12">
          Setup <span className="font-serif italic text-primary">Mock Interview</span>
        </h1>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Interview Type */}
          <div>
            <h2 className="text-xl font-medium mb-4 tracking-wide">Interview Type</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setInterviewType('company_specific')}
                className={`flex-1 py-4 rounded-2xl border-2 transition-all ${
                  interviewType === 'company_specific'
                    ? 'border-primary bg-primary/20 text-white'
                    : 'border-white/20 bg-white/5 text-white/60 hover:bg-white/10'
                }`}
              >
                <div className="font-medium text-lg">Company-Specific</div>
                <div className="text-sm mt-1">Simulate real interview</div>
              </button>

              <button
                type="button"
                onClick={() => setInterviewType('custom_topic')}
                className={`flex-1 py-4 rounded-2xl border-2 transition-all ${
                  interviewType === 'custom_topic'
                    ? 'border-primary bg-primary/20 text-white'
                    : 'border-white/20 bg-white/5 text-white/60 hover:bg-white/10'
                }`}
              >
                <div className="font-medium text-lg">Custom Topics</div>
                <div className="text-sm mt-1">Practice specific skills</div>
              </button>
            </div>
          </div>

          {/* Company-Specific Fields */}
          {interviewType === 'company_specific' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-2">Company Name *</label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="e.g., Google, Amazon, Microsoft"
                  required
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:ring-2 focus:ring-primary text-white placeholder-white/40"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Job Description (Optional)</label>
                <textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description here..."
                  rows={6}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl focus:ring-2 focus:ring-primary text-white placeholder-white/40"
                />
              </div>
            </>
          )}

          {/* Custom Topics */}
          {interviewType === 'custom_topic' && (
            <div>
              <label className="block text-sm font-medium mb-2">Topics to Practice</label>
              <div className="flex gap-2 mb-3">
                <input
                  type="text"
                  value={topicInput}
                  onChange={(e) => setTopicInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTopic())}
                  placeholder="e.g., React, System Design"
                  className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40"
                />
                <button
                  type="button"
                  onClick={addTopic}
                  className="px-6 py-3 rounded-xl bg-primary text-white font-medium hover:bg-primary/90"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {customTopics.map((topic, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 border border-white/20 text-sm"
                  >
                    {topic}
                    <button
                      type="button"
                      onClick={() => removeTopic(index)}
                      className="text-primary hover:text-primary/80 font-bold"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Rounds Configuration */}
          <div>
            <h3 className="text-xl font-medium mb-4">Interview Rounds</h3>
            <div className="space-y-3">
              {roundConfigs.map((round, index) => (
                <div key={index} className="flex gap-3 items-center bg-white/5 p-4 rounded-xl">
                  <div className="text-sm text-white/70">Round {index + 1}:</div>
                  <select
                    value={round.type}
                    onChange={(e) => updateRound(index, 'type', e.target.value)}
                    className="flex-1 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white"
                  >
                    <option value="technical">Technical</option>
                    <option value="behavioral">HR/Behavioral</option>
                    <option value="communication">Communication</option>
                  </select>
                  <select
                    value={round.difficulty}
                    onChange={(e) => updateRound(index, 'difficulty', e.target.value)}
                    className="flex-1 px-3 py-2 bg-white/10 border border-white/20 rounded-lg text-white"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                  {roundConfigs.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeRound(index)}
                      className="text-red-400 hover:text-red-300 font-medium"
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}
            </div>
            {roundConfigs.length < 3 && (
              <button
                type="button"
                onClick={addRound}
                className="mt-3 text-primary hover:text-primary/80 font-medium"
              >
                + Add Round
              </button>
            )}
          </div>

          {/* Error */}
          {error && (
            <div className="p-4 rounded-xl bg-red-500/20 border border-red-500/50 text-red-200">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-3 rounded-xl border border-white/20 text-white hover:bg-white/5"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-3 rounded-xl bg-primary text-white font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Start Interview'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InterviewSetup;

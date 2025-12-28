// frontend/components/Dashboard/JournalModule.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { agentService } from '../../services/agentService';
import { 
  BookOpen, Heart, Send, Sparkles, 
  Calendar, TrendingUp, Loader2, Smile,
  Frown, Meh, Zap
} from 'lucide-react';

interface JournalModuleProps {
  user: User;
}

const JournalModule: React.FC<JournalModuleProps> = ({ user }) => {
  const [entries, setEntries] = useState<any[]>([]);
  const [currentEntry, setCurrentEntry] = useState('');
  const [mood, setMood] = useState<'happy' | 'neutral' | 'sad'>('neutral');
  const [reflection, setReflection] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingEntries, setLoadingEntries] = useState(true);

  useEffect(() => {
    loadEntries();
  }, []);

  const loadEntries = async () => {
    try {
      const data = await agentService.getJournalEntries(user.id);
      setEntries(data.entries || []);
      setLoadingEntries(false);
    } catch (error) {
      console.error('Failed to load entries:', error);
      setLoadingEntries(false);
    }
  };

  const handleSubmit = async () => {
    if (!currentEntry.trim()) return;

    setLoading(true);
    try {
      const result = await agentService.addJournalEntry(user.id, currentEntry, mood);
      setReflection(result);
      setCurrentEntry('');
      loadEntries();
    } catch (error) {
      console.error('Failed to submit:', error);
    } finally {
      setLoading(false);
    }
  };

  const getMotivation = async () => {
    setLoading(true);
    try {
      const result = await agentService.getMotivation(user.id, {
        progress: 'Making steady progress',
        mood: mood
      });
      setReflection({ motivation: result.motivation || 'Keep going! You\'re doing great!' });
    } catch (error) {
      console.error('Failed to get motivation:', error);
    } finally {
      setLoading(false);
    }
  };

  const moodIcons = {
    happy: <Smile size={24} className="text-yellow-400" />,
    neutral: <Meh size={24} className="text-blue-400" />,
    sad: <Frown size={24} className="text-purple-400" />
  };

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Career Journal</h2>
          <p className="text-white/60">Reflect on your journey and get AI insights</p>
        </div>
        <button
          onClick={getMotivation}
          disabled={loading}
          className="px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary rounded-2xl flex items-center gap-3 transition-all border border-primary/30"
        >
          <Zap size={20} />
          Get Motivation
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Entry Form */}
        <div className="space-y-6">
          <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
            <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
              <BookOpen size={20} className="text-primary" />
              New Entry
            </h3>
            
            {/* Mood Selector */}
            <div className="mb-4">
              <p className="text-sm text-white/60 mb-3">How are you feeling today?</p>
              <div className="flex gap-3">
                {(['happy', 'neutral', 'sad'] as const).map((m) => (
                  <button
                    key={m}
                    onClick={() => setMood(m)}
                    className={`flex-1 p-4 rounded-2xl border transition-all ${
                      mood === m
                        ? 'bg-primary/20 border-primary/30 text-primary'
                        : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/10'
                    }`}
                  >
                    <div className="flex flex-col items-center gap-2">
                      {moodIcons[m]}
                      <span className="text-sm font-medium capitalize">{m}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Entry Text */}
            <textarea
              value={currentEntry}
              onChange={(e) => setCurrentEntry(e.target.value)}
              placeholder="Share your thoughts, progress, challenges, or anything on your mind..."
              className="w-full h-48 bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder-white/30 resize-none focus:outline-none focus:border-primary/50"
            />

            <button
              onClick={handleSubmit}
              disabled={loading || !currentEntry.trim()}
              className="w-full mt-4 px-6 py-4 bg-primary text-bg-deep rounded-2xl font-bold flex items-center justify-center gap-3 hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send size={20} />
                  Submit Entry
                </>
              )}
            </button>
          </div>

          {/* AI Reflection */}
          {reflection && (
            <div className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 rounded-[2rem] p-6">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                <Sparkles size={20} className="text-primary" />
                AI Reflection
              </h3>
              {reflection.reflection && (
                <p className="text-white/90 mb-4 leading-relaxed">{reflection.reflection}</p>
              )}
              {reflection.motivation && (
                <div className="p-4 bg-white/5 rounded-xl">
                  <div className="flex items-start gap-3">
                    <Heart size={20} className="text-primary mt-0.5 flex-shrink-0" />
                    <p className="text-white/90 italic">{reflection.motivation}</p>
                  </div>
                </div>
              )}
              {reflection.insights && reflection.insights.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm text-white/60 mb-2">Key Insights:</p>
                  <ul className="space-y-2">
                    {reflection.insights.map((insight: string, idx: number) => (
                      <li key={idx} className="text-sm text-white/80 flex items-start gap-2">
                        <TrendingUp size={14} className="text-primary mt-1 flex-shrink-0" />
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {reflection.suggested_actions && reflection.suggested_actions.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm text-white/60 mb-2">Suggested Actions:</p>
                  <ul className="space-y-2">
                    {reflection.suggested_actions.map((action: any, idx: number) => (
                      <li key={idx} className="text-sm text-white/80 flex items-start gap-2">
                        <Zap size={14} className="text-primary mt-1 flex-shrink-0" />
                        <span>{action.action || action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Past Entries */}
        <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
          <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
            <Calendar size={20} className="text-primary" />
            Recent Entries
          </h3>
          
          {loadingEntries ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 size={32} className="animate-spin text-primary" />
            </div>
          ) : entries.length > 0 ? (
            <div className="space-y-4 max-h-[600px] overflow-y-auto">
              {entries.map((entry, idx) => (
                <div key={idx} className="p-4 bg-white/5 rounded-2xl">
                  <div className="flex items-center gap-3 mb-2">
                    {moodIcons[entry.mood as keyof typeof moodIcons] || moodIcons.neutral}
                    <span className="text-xs text-white/40">
                      {entry.timestamp ? new Date(entry.timestamp).toLocaleDateString() : 'Recent'}
                    </span>
                  </div>
                  <p className="text-white/80 text-sm">{entry.message || entry.entry}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <BookOpen size={48} className="mx-auto mb-4 text-white/20" />
              <p className="text-white/60">No entries yet. Start journaling to track your journey!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default JournalModule;


// frontend/components/Dashboard/JournalModule.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { journalService, JournalEntry, JournalAnalysis } from '../../services/journalService';
import { 
  BookOpen, Heart, Send, Sparkles, 
  Calendar, TrendingUp, Loader2, Smile,
  Frown, Meh, Zap, Trash2, Lightbulb,
  MessageSquare, Target, Brain
} from 'lucide-react';

interface JournalModuleProps {
  user: User;
}

const JournalModule: React.FC<JournalModuleProps> = ({ user }) => {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [currentEntry, setCurrentEntry] = useState('');
  const [mood, setMood] = useState<'happy' | 'motivated' | 'frustrated' | 'confused' | 'accomplished'>('motivated');
  const [aiResponse, setAiResponse] = useState<JournalAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingEntries, setLoadingEntries] = useState(true);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('reflection');

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    await Promise.all([
      loadEntries(),
      loadPrompts(),
      loadStats()
    ]);
  };

  const loadEntries = async () => {
    try {
      const data = await journalService.getEntries(10, 0);
      setEntries(data.entries || []);
      setLoadingEntries(false);
    } catch (error) {
      console.error('Failed to load entries:', error);
      setLoadingEntries(false);
    }
  };

  const loadPrompts = async () => {
    try {
      const data = await journalService.getPrompts(selectedCategory);
      setPrompts(data.prompts || []);
    } catch (error) {
      console.error('Failed to load prompts:', error);
    }
  };

  const loadStats = async () => {
    try {
      const data = await journalService.getStats();
      setStats(data.stats);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const handleSubmit = async () => {
    if (!currentEntry.trim()) return;

    setLoading(true);
    setAiResponse(null);
    
    try {
      const result = await journalService.createEntry(
        currentEntry,
        undefined, // auto-generate title
        mood
      );
      
      setAiResponse(result.analysis);
      setCurrentEntry('');
      
      // Reload entries and stats
      await Promise.all([loadEntries(), loadStats()]);
      
    } catch (error) {
      console.error('Failed to submit:', error);
      alert('Failed to save entry. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const usePrompt = (prompt: string) => {
    setCurrentEntry(prompt + '\n\n');
  };

  const handleDelete = async (entryId: string) => {
    if (!confirm('Delete this entry? This cannot be undone.')) return;
    
    try {
      await journalService.deleteEntry(entryId);
      await loadEntries();
      await loadStats();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  const moodConfig = {
    happy: { icon: Smile, color: 'text-yellow-400', bg: 'bg-yellow-400/20', border: 'border-yellow-400/30' },
    motivated: { icon: Zap, color: 'text-primary', bg: 'bg-primary/20', border: 'border-primary/30' },
    frustrated: { icon: Frown, color: 'text-red-400', bg: 'bg-red-400/20', border: 'border-red-400/30' },
    confused: { icon: Meh, color: 'text-blue-400', bg: 'bg-blue-400/20', border: 'border-blue-400/30' },
    accomplished: { icon: Target, color: 'text-green-400', bg: 'bg-green-400/20', border: 'border-green-400/30' }
  };

  const categories = [
    { id: 'reflection', label: 'Reflection', icon: Brain },
    { id: 'learning', label: 'Learning', icon: Lightbulb },
    { id: 'career', label: 'Career', icon: Target },
    { id: 'project', label: 'Projects', icon: BookOpen }
  ];

  const MoodIcon = moodConfig[mood].icon;

  return (
    <div className="space-y-8">
      
      {/* Header with Stats */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Career Journal</h2>
          <p className="text-white/60">Reflect on your journey and get AI insights</p>
        </div>
        
        {stats && (
          <div className="flex gap-4">
            <div className="px-4 py-2 bg-white/5 rounded-2xl border border-white/10">
              <div className="text-2xl font-bold text-primary">{stats.current_streak}</div>
              <div className="text-xs text-white/60">Day Streak</div>
            </div>
            <div className="px-4 py-2 bg-white/5 rounded-2xl border border-white/10">
              <div className="text-2xl font-bold text-primary">{stats.this_week}</div>
              <div className="text-xs text-white/60">This Week</div>
            </div>
            <div className="px-4 py-2 bg-white/5 rounded-2xl border border-white/10">
              <div className="text-2xl font-bold text-primary">{stats.total_entries}</div>
              <div className="text-xs text-white/60">Total</div>
            </div>
          </div>
        )}
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
              <p className="text-sm text-white/60 mb-3">How are you feeling?</p>
              <div className="grid grid-cols-5 gap-2">
                {(Object.keys(moodConfig) as Array<keyof typeof moodConfig>).map((m) => {
                  const config = moodConfig[m];
                  const Icon = config.icon;
                  return (
                    <button
                      key={m}
                      onClick={() => setMood(m)}
                      className={`p-3 rounded-xl border transition-all ${
                        mood === m
                          ? `${config.bg} ${config.border} ${config.color}`
                          : 'bg-white/5 border-white/10 text-white/60 hover:bg-white/10'
                      }`}
                    >
                      <div className="flex flex-col items-center gap-1">
                        <Icon size={20} />
                        <span className="text-xs font-medium capitalize">{m}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Category Selector for Prompts */}
            <div className="mb-4">
              <p className="text-sm text-white/60 mb-3">Need inspiration?</p>
              <div className="flex gap-2 mb-3">
                {categories.map((cat) => {
                  const Icon = cat.icon;
                  return (
                    <button
                      key={cat.id}
                      onClick={() => {
                        setSelectedCategory(cat.id);
                        journalService.getPrompts(cat.id).then(data => setPrompts(data.prompts));
                      }}
                      className={`flex-1 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                        selectedCategory === cat.id
                          ? 'bg-primary/20 text-primary border border-primary/30'
                          : 'bg-white/5 text-white/60 border border-white/10 hover:bg-white/10'
                      }`}
                    >
                      <Icon size={14} className="inline mr-1" />
                      {cat.label}
                    </button>
                  );
                })}
              </div>
              
              {/* Prompt Suggestions */}
              {prompts.length > 0 && (
                <div className="space-y-2">
                  {prompts.slice(0, 3).map((prompt, idx) => (
                    <button
                      key={idx}
                      onClick={() => usePrompt(prompt)}
                      className="w-full text-left p-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-sm text-white/70 transition-all"
                    >
                      <Lightbulb size={14} className="inline text-primary mr-2" />
                      {prompt}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Entry Text */}
            <textarea
              value={currentEntry}
              onChange={(e) => setCurrentEntry(e.target.value)}
              placeholder="Share your thoughts, progress, challenges, or anything on your mind..."
              className="w-full h-48 bg-white/5 border border-white/10 rounded-2xl p-4 text-white placeholder-white/30 resize-none focus:outline-none focus:border-primary/50"
            />

            <div className="flex items-center justify-between mt-4">
              <div className="text-xs text-white/40">
                {currentEntry.trim().split(/\s+/).filter(Boolean).length} words
              </div>
              <button
                onClick={handleSubmit}
                disabled={loading || !currentEntry.trim()}
                className="px-6 py-3 bg-primary text-bg-deep rounded-2xl font-bold flex items-center gap-3 hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 size={20} className="animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Send size={20} />
                    Submit & Analyze
                  </>
                )}
              </button>
            </div>
          </div>

          {/* AI Response - Conversational */}
          {aiResponse && (
            <div className="bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/30 rounded-[2rem] p-6 animate-fadeIn">
              <h3 className="text-lg font-medium mb-4 flex items-center gap-3">
                <Sparkles size={20} className="text-primary" />
                AI Reflection
              </h3>
              
              {/* Main Summary/Response */}
              <div className="mb-4 p-4 bg-white/5 rounded-2xl">
                <div className="flex items-start gap-3">
                  <MessageSquare size={20} className="text-primary mt-1 flex-shrink-0" />
                  <p className="text-white/90 leading-relaxed">{aiResponse.summary}</p>
                </div>
              </div>

              {/* Key Insights */}
              {aiResponse.insights && aiResponse.insights.length > 0 && (
                <div className="mb-4">
                  <p className="text-sm text-white/60 mb-3 flex items-center gap-2">
                    <Brain size={16} />
                    Key Insights
                  </p>
                  <ul className="space-y-2">
                    {aiResponse.insights.map((insight: string, idx: number) => (
                      <li key={idx} className="text-sm text-white/80 flex items-start gap-2 p-3 bg-white/5 rounded-xl">
                        <TrendingUp size={14} className="text-primary mt-0.5 flex-shrink-0" />
                        <span>{insight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Suggestions */}
              {aiResponse.suggestions && aiResponse.suggestions.length > 0 && (
                <div>
                  <p className="text-sm text-white/60 mb-3 flex items-center gap-2">
                    <Zap size={16} />
                    Suggested Actions
                  </p>
                  <ul className="space-y-2">
                    {aiResponse.suggestions.map((suggestion: string, idx: number) => (
                      <li key={idx} className="text-sm text-white/80 flex items-start gap-2 p-3 bg-white/5 rounded-xl">
                        <Target size={14} className="text-primary mt-0.5 flex-shrink-0" />
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Mood & Sentiment */}
              <div className="mt-4 pt-4 border-t border-white/10 flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-white/60">
                  <Heart size={16} className="text-primary" />
                  Detected Mood: <span className="text-primary font-medium capitalize">{aiResponse.mood}</span>
                </div>
                <div className="text-sm text-white/60">
                  Sentiment: <span className={`font-medium ${
                    aiResponse.sentiment > 0.3 ? 'text-green-400' : 
                    aiResponse.sentiment < -0.3 ? 'text-red-400' : 'text-yellow-400'
                  }`}>
                    {aiResponse.sentiment > 0.3 ? 'Positive' : 
                     aiResponse.sentiment < -0.3 ? 'Needs Support' : 'Neutral'}
                  </span>
                </div>
              </div>
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
            <div className="space-y-4 max-h-[700px] overflow-y-auto pr-2 custom-scrollbar">
              {entries.map((entry) => {
                const entryMood = (entry.mood || 'motivated') as keyof typeof moodConfig;
                const config = moodConfig[entryMood] || moodConfig.motivated;
                const Icon = config.icon;
                
                return (
                  <div key={entry.id} className="p-4 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition-all group">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Icon size={18} className={config.color} />
                        <span className="text-xs text-white/40">
                          {new Date(entry.created_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </span>
                      </div>
                      <button
                        onClick={() => handleDelete(entry.id)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity text-white/40 hover:text-red-400"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                    
                    {entry.title && entry.title !== 'Untitled' && (
                      <h4 className="text-sm font-medium text-white/90 mb-2">{entry.title}</h4>
                    )}
                    
                    <p className="text-white/70 text-sm mb-3 line-clamp-3">{entry.content}</p>
                    
                    {entry.ai_summary && (
                      <div className="p-3 bg-primary/10 rounded-xl border border-primary/20">
                        <p className="text-xs text-primary/90 italic">"{entry.ai_summary}"</p>
                      </div>
                    )}
                    
                    {entry.topics_detected && entry.topics_detected.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {entry.topics_detected.map((topic, idx) => (
                          <span key={idx} className="px-2 py-1 bg-white/5 border border-white/10 rounded-lg text-xs text-white/60">
                            {topic}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12">
              <BookOpen size={48} className="mx-auto mb-4 text-white/20" />
              <p className="text-white/60 mb-2">No entries yet</p>
              <p className="text-white/40 text-sm">Start journaling to track your journey!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default JournalModule;

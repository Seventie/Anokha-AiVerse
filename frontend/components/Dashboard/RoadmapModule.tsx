// frontend/src/components/Dashboard/RoadmapModule.tsx

import React, { useState, useEffect } from 'react';
import { User } from '../../services/authService';
import { agentService } from '../../services/agentService';
import { 
  Map, Plus, CheckCircle, Clock, Target, 
  TrendingUp, Loader2, Edit3, Download,
  Calendar as CalendarIcon, Zap
} from 'lucide-react';

interface RoadmapModuleProps {
  user: User;
}

const RoadmapModule: React.FC<RoadmapModuleProps> = ({ user }) => {
  const [roadmap, setRoadmap] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedMilestone, setSelectedMilestone] = useState<any>(null);

  useEffect(() => {
    loadRoadmap();
  }, []);

  const loadRoadmap = async () => {
    try {
      const data = await agentService.getRoadmap(user.id);
      setRoadmap(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load roadmap:', error);
      setLoading(false);
    }
  };

  const generateNewRoadmap = async () => {
    setGenerating(true);
    try {
      const newRoadmap = await agentService.generateRoadmap(user.id, {
        targetRole: user.targetRole || 'Software Engineer',
        timeline: user.timeline || '6 Months',
        currentSkills: user.skills?.technical || [],
        preferredLocations: user.preferredLocations || []
      });
      setRoadmap(newRoadmap);
    } catch (error) {
      console.error('Failed to generate roadmap:', error);
    } finally {
      setGenerating(false);
    }
  };

  const syncToCalendar = async () => {
    try {
      await agentService.syncRoadmapToCalendar(user.id, roadmap);
      alert('Roadmap synced to your calendar!');
    } catch (error) {
      console.error('Failed to sync:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 size={48} className="animate-spin text-primary" />
      </div>
    );
  }

  if (!roadmap) {
    return (
      <div className="text-center py-20">
        <Map size={80} className="mx-auto mb-8 text-white/20" />
        <h2 className="text-3xl font-light mb-4">No Roadmap Yet</h2>
        <p className="text-white/60 mb-8 max-w-md mx-auto">
          Let our AI agent generate a personalized career roadmap based on your goals and current skills.
        </p>
        <button
          onClick={generateNewRoadmap}
          disabled={generating}
          className="px-12 py-6 bg-primary text-bg-deep rounded-[2rem] font-bold flex items-center gap-4 mx-auto hover:shadow-[0_0_60px_rgba(212,212,170,0.4)] transition-all disabled:opacity-50"
        >
          {generating ? (
            <>
              <Loader2 size={24} className="animate-spin" />
              Generating Your Roadmap...
            </>
          ) : (
            <>
              <Zap size={24} />
              Generate My Roadmap
            </>
          )}
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-light mb-2">Career Roadmap</h2>
          <p className="text-white/60">Your personalized path to {user.targetRole || 'your dream role'}</p>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={syncToCalendar}
            className="px-6 py-3 bg-white/10 hover:bg-white/20 rounded-2xl flex items-center gap-3 transition-all border border-white/10"
          >
            <CalendarIcon size={20} />
            Sync to Calendar
          </button>
          <button
            onClick={generateNewRoadmap}
            disabled={generating}
            className="px-6 py-3 bg-primary/20 hover:bg-primary/30 text-primary rounded-2xl flex items-center gap-3 transition-all border border-primary/30"
          >
            <Zap size={20} />
            Regenerate
          </button>
        </div>
      </div>

      {/* Timeline Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <TimelineCard
          icon={<Target size={24} className="text-blue-400" />}
          label="Target Role"
          value={roadmap.target_role}
        />
        <TimelineCard
          icon={<Clock size={24} className="text-green-400" />}
          label="Timeline"
          value={roadmap.timeline}
        />
        <TimelineCard
          icon={<TrendingUp size={24} className="text-purple-400" />}
          label="Milestones"
          value={`${roadmap.milestones?.length || 0} Phases`}
        />
        <TimelineCard
          icon={<CheckCircle size={24} className="text-yellow-400" />}
          label="Progress"
          value="12% Complete"
        />
      </div>

      {/* Visual Roadmap */}
      <div className="bg-white/5 border border-white/10 rounded-[3rem] p-8">
        <h3 className="text-xl font-medium mb-6 flex items-center gap-3">
          <Map size={24} className="text-primary" />
          Monthly Milestones
        </h3>
        
        <div className="relative">
          {/* Timeline Line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-primary via-primary/50 to-transparent"></div>
          
          {/* Milestones */}
          <div className="space-y-8 relative">
            {roadmap.milestones?.map((milestone: any, idx: number) => (
              <div 
                key={idx}
                className="relative pl-20 cursor-pointer group"
                onClick={() => setSelectedMilestone(milestone)}
              >
                {/* Timeline Dot */}
                <div className="absolute left-6 top-4 w-4 h-4 rounded-full bg-primary border-4 border-bg-deep group-hover:scale-150 transition-all"></div>
                
                {/* Milestone Card */}
                <div className="bg-white/5 hover:bg-white/10 border border-white/10 hover:border-primary/30 rounded-[2rem] p-6 transition-all">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="text-xs text-primary font-bold uppercase tracking-widest mb-2">
                        Month {milestone.month}
                      </div>
                      <h4 className="text-xl font-medium mb-2">{milestone.title}</h4>
                      <p className="text-sm text-white/60">{milestone.focus}</p>
                    </div>
                    <div className="px-4 py-2 bg-primary/10 text-primary rounded-full text-xs font-bold">
                      {milestone.status || 'Not Started'}
                    </div>
                  </div>
                  
                  {/* Goals */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                    <div>
                      <p className="text-xs text-white/40 uppercase tracking-wider mb-2">Goals</p>
                      <ul className="space-y-1">
                        {milestone.goals?.slice(0, 3).map((goal: string, i: number) => (
                          <li key={i} className="text-sm text-white/80 flex items-start gap-2">
                            <CheckCircle size={14} className="text-primary mt-0.5 flex-shrink-0" />
                            {goal}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <p className="text-xs text-white/40 uppercase tracking-wider mb-2">Skills to Master</p>
                      <div className="flex flex-wrap gap-2">
                        {milestone.skills?.slice(0, 4).map((skill: string, i: number) => (
                          <span key={i} className="px-3 py-1 bg-white/5 border border-white/10 rounded-full text-xs">
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Learning Paths */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Skills to Learn */}
        <div className="bg-white/5 border border-white/10 rounded-[3rem] p-8">
          <h3 className="text-xl font-medium mb-6 flex items-center gap-3">
            <Target size={24} className="text-primary" />
            Priority Skills
          </h3>
          
          <div className="space-y-4">
            {roadmap.learning_paths?.slice(0, 5).map((path: any, idx: number) => (
              <div key={idx} className="p-4 bg-white/5 rounded-2xl">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium">{path.skill}</h4>
                  <span className={`px-3 py-1 rounded-full text-xs ${
                    path.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                    path.priority === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-green-500/20 text-green-400'
                  }`}>
                    {path.priority}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm text-white/60">
                  <span>{path.estimated_hours}h estimated</span>
                  <button className="text-primary hover:underline text-xs">
                    View Resources →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Suggested Projects */}
        <div className="bg-white/5 border border-white/10 rounded-[3rem] p-8">
          <h3 className="text-xl font-medium mb-6 flex items-center gap-3">
            <Plus size={24} className="text-primary" />
            Portfolio Projects
          </h3>
          
          <div className="space-y-4">
            {roadmap.projects?.slice(0, 3).map((project: any, idx: number) => (
              <div key={idx} className="p-4 bg-white/5 rounded-2xl hover:bg-white/10 transition-all cursor-pointer group">
                <h4 className="font-medium mb-2 group-hover:text-primary transition-colors">
                  {project.title}
                </h4>
                <p className="text-sm text-white/60 mb-3">{project.description}</p>
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-2">
                    {project.skills_used?.slice(0, 3).map((skill: string, i: number) => (
                      <span key={i} className="px-2 py-1 bg-primary/10 text-primary rounded-full text-xs">
                        {skill}
                      </span>
                    ))}
                  </div>
                  <span className="text-xs text-white/40">{project.timeline}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Milestone Detail Modal */}
      {selectedMilestone && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6" onClick={() => setSelectedMilestone(null)}>
          <div className="bg-bg-deep border border-white/20 rounded-[3rem] p-12 max-w-3xl w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-8">
              <div>
                <div className="text-xs text-primary font-bold uppercase tracking-widest mb-2">
                  Month {selectedMilestone.month}
                </div>
                <h2 className="text-3xl font-light mb-2">{selectedMilestone.title}</h2>
                <p className="text-white/60">{selectedMilestone.focus}</p>
              </div>
              <button onClick={() => setSelectedMilestone(null)} className="text-white/60 hover:text-white">
                ✕
              </button>
            </div>
            
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-medium mb-4">Goals</h3>
                <ul className="space-y-3">
                  {selectedMilestone.goals?.map((goal: string, i: number) => (
                    <li key={i} className="flex items-start gap-3 text-white/80">
                      <CheckCircle size={20} className="text-primary mt-0.5 flex-shrink-0" />
                      {goal}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h3 className="text-lg font-medium mb-4">Deliverables</h3>
                <div className="grid gap-3">
                  {selectedMilestone.deliverables?.map((item: string, i: number) => (
                    <div key={i} className="p-4 bg-white/5 rounded-2xl">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-lg font-medium mb-4">Skills to Master</h3>
                <div className="flex flex-wrap gap-3">
                  {selectedMilestone.skills?.map((skill: string, i: number) => (
                    <span key={i} className="px-4 py-2 bg-primary/10 text-primary border border-primary/30 rounded-2xl">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const TimelineCard = ({ icon, label, value }: any) => (
  <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
    <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-4">
      {icon}
    </div>
    <p className="text-2xl font-light mb-1">{value}</p>
    <p className="text-sm text-white/40">{label}</p>
  </div>
);

export default RoadmapModule;
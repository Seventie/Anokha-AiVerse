// frontend/src/components/roadmap/SkillGapAnalysis.tsx

import React from 'react';
import { AlertCircle, TrendingUp, CheckCircle } from 'lucide-react';

interface SkillGapAnalysisProps {
  roadmapData: any;
}

const SkillGapAnalysis: React.FC<SkillGapAnalysisProps> = ({ roadmapData }) => {
  if (!roadmapData) {
    return null;
  }

  const learningPath = roadmapData.learning_path || [];
  
  // Categorize by priority
  const highPriority = learningPath.filter((s: any) => s.priority === 'high');
  const mediumPriority = learningPath.filter((s: any) => s.priority === 'medium');
  const lowPriority = learningPath.filter((s: any) => s.priority === 'low');

  return (
    <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
      <h3 className="text-xl font-light mb-6 flex items-center gap-3">
        <TrendingUp size={24} className="text-primary" />
        Skill Gap Analysis
      </h3>

      <div className="space-y-4 mb-6">
        {/* High Priority */}
        <PrioritySection
          title="High Priority"
          count={highPriority.length}
          color="red"
          icon={<AlertCircle size={16} />}
        />
        
        {/* Medium Priority */}
        <PrioritySection
          title="Medium Priority"
          count={mediumPriority.length}
          color="yellow"
          icon={<AlertCircle size={16} />}
        />
        
        {/* Low Priority */}
        <PrioritySection
          title="Low Priority"
          count={lowPriority.length}
          color="green"
          icon={<CheckCircle size={16} />}
        />
      </div>

      {/* Skills List */}
      <div className="space-y-3">
        {highPriority.map((skill: any, idx: number) => (
          <SkillCard key={`high-${idx}`} skill={skill} priority="high" />
        ))}
        {mediumPriority.slice(0, 3).map((skill: any, idx: number) => (
          <SkillCard key={`med-${idx}`} skill={skill} priority="medium" />
        ))}
        {lowPriority.slice(0, 2).map((skill: any, idx: number) => (
          <SkillCard key={`low-${idx}`} skill={skill} priority="low" />
        ))}
      </div>
    </div>
  );
};

const PrioritySection: React.FC<{
  title: string;
  count: number;
  color: string;
  icon: React.ReactNode;
}> = ({ title, count, color, icon }) => {
  const colorClasses = {
    red: 'bg-red-500/20 border-red-500/30 text-red-400',
    yellow: 'bg-yellow-500/20 border-yellow-500/30 text-yellow-400',
    green: 'bg-green-500/20 border-green-500/30 text-green-400'
  };

  return (
    <div className={`border rounded-xl p-3 flex items-center justify-between ${colorClasses[color as keyof typeof colorClasses]}`}>
      <div className="flex items-center gap-2">
        {icon}
        <span className="font-medium">{title}</span>
      </div>
      <span className="text-2xl font-light">{count}</span>
    </div>
  );
};

const SkillCard: React.FC<{ skill: any; priority: string }> = ({ skill, priority }) => {
  const borderColor = {
    high: 'border-red-500/30',
    medium: 'border-yellow-500/30',
    low: 'border-green-500/30'
  }[priority];

  return (
    <div className={`border ${borderColor} bg-white/5 rounded-xl p-3 flex justify-between items-center`}>
      <span className="text-white/90">{skill.skill}</span>
      <span className="text-xs text-white/60 bg-white/10 px-2 py-1 rounded">
        {skill.estimated_hours || 20}h
      </span>
    </div>
  );
};

export default SkillGapAnalysis;

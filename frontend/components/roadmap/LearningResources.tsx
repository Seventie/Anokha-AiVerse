// frontend/src/components/roadmap/LearningResources.tsx

import React, { useState } from 'react';
import { 
  Calendar, Clock, CheckCircle2, Circle, 
  PlayCircle, ExternalLink, ChevronDown, ChevronUp 
} from 'lucide-react';

interface Task {
  id: string;
  skill_name: string;
  title: string;
  description: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'skipped';
  progress_percent: number;
  estimated_hours: number;
  start_date: string | null;
  due_date: string | null;
  completed_at: string | null;
  resources: string[];
}

interface LearningResourcesProps {
  phase: string;
  tasks: Task[];
  onTaskUpdate: (taskId: string, status: string) => void;
}

const LearningResources: React.FC<LearningResourcesProps> = ({ 
  phase, 
  tasks, 
  onTaskUpdate 
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());

  // Calculate phase progress
  const completedTasks = tasks.filter(t => t.status === 'completed').length;
  const totalTasks = tasks.length;
  const phaseProgress = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const toggleTaskExpansion = (taskId: string) => {
    const newExpanded = new Set(expandedTasks);
    if (newExpanded.has(taskId)) {
      newExpanded.delete(taskId);
    } else {
      newExpanded.add(taskId);
    }
    setExpandedTasks(newExpanded);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-400';
      case 'in_progress':
        return 'text-blue-400';
      case 'skipped':
        return 'text-yellow-400';
      default:
        return 'text-white/40';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="text-green-400" size={20} />;
      case 'in_progress':
        return <PlayCircle className="text-blue-400" size={20} />;
      default:
        return <Circle className="text-white/40" size={20} />;
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Not set';
    return new Date(dateString).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="bg-white/5 border border-white/10 rounded-[2rem] overflow-hidden">
      {/* Phase Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-5 flex items-center justify-between hover:bg-white/5 transition-all"
      >
        <div className="flex items-center gap-4">
          <Calendar size={24} className="text-primary" />
          <div className="text-left">
            <h3 className="text-xl font-light text-white capitalize">
              {phase.replace('_', ' ')} Phase
            </h3>
            <p className="text-sm text-white/60">
              {completedTasks}/{totalTasks} completed
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Progress Circle */}
          <div className="relative w-16 h-16">
            <svg className="w-16 h-16 transform -rotate-90">
              <circle
                cx="32"
                cy="32"
                r="28"
                stroke="rgba(255,255,255,0.1)"
                strokeWidth="4"
                fill="none"
              />
              <circle
                cx="32"
                cy="32"
                r="28"
                stroke="#D4D4AA"
                strokeWidth="4"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 28}`}
                strokeDashoffset={`${2 * Math.PI * 28 * (1 - phaseProgress / 100)}`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-medium text-primary">{phaseProgress}%</span>
            </div>
          </div>
          
          {isExpanded ? (
            <ChevronUp size={24} className="text-white/60" />
          ) : (
            <ChevronDown size={24} className="text-white/60" />
          )}
        </div>
      </button>

      {/* Tasks List */}
      {isExpanded && (
        <div className="px-6 pb-6 space-y-3">
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              isExpanded={expandedTasks.has(task.id)}
              onToggleExpand={() => toggleTaskExpansion(task.id)}
              onStatusChange={(status) => onTaskUpdate(task.id, status)}
              getStatusColor={getStatusColor}
              getStatusIcon={getStatusIcon}
              formatDate={formatDate}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ==================== TASK CARD COMPONENT ====================

const TaskCard: React.FC<{
  task: Task;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onStatusChange: (status: string) => void;
  getStatusColor: (status: string) => string;
  getStatusIcon: (status: string) => React.ReactNode;
  formatDate: (date: string | null) => string;
}> = ({ 
  task, 
  isExpanded, 
  onToggleExpand, 
  onStatusChange, 
  getStatusColor, 
  getStatusIcon, 
  formatDate 
}) => {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
      {/* Task Header */}
      <button
        onClick={onToggleExpand}
        className="w-full px-4 py-4 flex items-center gap-4 hover:bg-white/5 transition-all"
      >
        {/* Status Icon */}
        <div className="flex-shrink-0">
          {getStatusIcon(task.status)}
        </div>

        {/* Task Info */}
        <div className="flex-1 text-left">
          <h4 className="text-white/90 font-medium">{task.skill_name}</h4>
          <p className="text-sm text-white/60">{task.title}</p>
        </div>

        {/* Time Badge */}
        <div className="flex items-center gap-2 px-3 py-1 bg-white/10 rounded-lg">
          <Clock size={14} className="text-primary" />
          <span className="text-sm text-white/80">{task.estimated_hours}h</span>
        </div>

        {/* Expand Icon */}
        {isExpanded ? (
          <ChevronUp size={20} className="text-white/40" />
        ) : (
          <ChevronDown size={20} className="text-white/40" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-white/10 pt-4">
          {/* Description */}
          <p className="text-sm text-white/70">{task.description}</p>

          {/* Dates */}
          <div className="flex gap-4 text-sm">
            <div className="flex items-center gap-2 text-white/60">
              <Calendar size={14} />
              <span>Due: {formatDate(task.due_date)}</span>
            </div>
            {task.completed_at && (
              <div className="flex items-center gap-2 text-green-400">
                <CheckCircle2 size={14} />
                <span>Completed: {formatDate(task.completed_at)}</span>
              </div>
            )}
          </div>

          {/* Resources */}
          {task.resources && task.resources.length > 0 && (
            <div>
              <p className="text-sm font-medium text-white/80 mb-2 flex items-center gap-2">
                <ExternalLink size={14} className="text-primary" />
                Resources
              </p>
              <div className="space-y-2">
                {task.resources.map((resource, idx) => (
                  <a
                    key={idx}
                    href={resource}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm text-white/80 hover:text-primary transition-all border border-white/10"
                  >
                    {resource}
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Status Change Buttons */}
          <div className="flex gap-2 pt-2">
            {task.status !== 'in_progress' && (
              <button
                onClick={() => onStatusChange('in_progress')}
                className="flex-1 px-4 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-xl text-sm font-medium transition-all border border-blue-500/30"
              >
                Start Learning
              </button>
            )}
            {task.status !== 'completed' && (
              <button
                onClick={() => onStatusChange('completed')}
                className="flex-1 px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-xl text-sm font-medium transition-all border border-green-500/30"
              >
                Mark Complete
              </button>
            )}
            {task.status === 'completed' && (
              <button
                onClick={() => onStatusChange('not_started')}
                className="flex-1 px-4 py-2 bg-white/5 hover:bg-white/10 text-white/60 rounded-xl text-sm font-medium transition-all border border-white/10"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LearningResources;

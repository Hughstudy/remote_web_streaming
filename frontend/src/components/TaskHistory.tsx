import React from 'react';
import { Task, TaskStep } from '../types';

interface TaskHistoryProps {
  tasks: Task[];
  currentTask: Task | null;
  className?: string;
}

const TaskHistory: React.FC<TaskHistoryProps> = ({ tasks, currentTask, className = '' }) => {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed': return '✅';
      case 'running': return '⏳';
      case 'failed': return '❌';
      default: return '📋';
    }
  };

  const getStatusColor = (status: Task['status']) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-50';
      case 'running': return 'text-blue-600 bg-blue-50';
      case 'failed': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const StepItem: React.FC<{ step: TaskStep; isLast: boolean }> = ({ step, isLast }) => (
    <div className="flex items-start space-x-3">
      <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs ${
        step.type === 'step_error' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'
      }`}>
        {step.step_number}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <span className="text-xs font-medium text-gray-900 uppercase tracking-wide">
            {step.action}
          </span>
          <span className="text-xs text-gray-500">
            {formatTime(step.timestamp)}
          </span>
        </div>
        <p className="text-sm text-gray-700 mt-1">{step.description}</p>
        {step.type === 'step_error' && (
          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
            Error occurred during this step
          </div>
        )}
      </div>
      {!isLast && <div className="absolute left-3 mt-8 w-px h-8 bg-gray-200"></div>}
    </div>
  );

  const TaskItem: React.FC<{ task: Task; isExpanded?: boolean }> = ({ task, isExpanded = false }) => (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <div className={`px-4 py-3 ${getStatusColor(task.status)}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-lg">{getStatusIcon(task.status)}</span>
            <div>
              <h4 className="font-medium text-gray-900 truncate max-w-md" title={task.instruction}>
                {task.instruction}
              </h4>
              <p className="text-xs opacity-75">
                Started at {formatTime(task.createdAt)}
              </p>
            </div>
          </div>
          <div className="text-right text-xs">
            <div className="font-medium capitalize">{task.status}</div>
            <div className="opacity-75">{task.steps.length} steps</div>
          </div>
        </div>
      </div>

      {/* Task Steps */}
      {(isExpanded || task.status === 'running') && task.steps.length > 0 && (
        <div className="px-4 py-4 bg-white border-t border-gray-200">
          <h5 className="text-sm font-medium text-gray-900 mb-3">Execution Steps:</h5>
          <div className="space-y-4 relative">
            {task.steps.map((step, index) => (
              <StepItem
                key={`${step.task_id}-${step.step_number}`}
                step={step}
                isLast={index === task.steps.length - 1}
              />
            ))}
            {task.status === 'running' && (
              <div className="flex items-center space-x-3 opacity-60">
                <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center">
                  <div className="animate-spin w-3 h-3 border border-gray-400 border-t-transparent rounded-full"></div>
                </div>
                <span className="text-sm text-gray-600">Executing next step...</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Task Result */}
      {task.status === 'completed' && task.result && (
        <div className="px-4 py-3 bg-green-50 border-t border-green-200">
          <h5 className="text-sm font-medium text-green-900 mb-2">Result:</h5>
          <p className="text-sm text-green-800">{task.result}</p>
        </div>
      )}
    </div>
  );

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Task History</h3>
        <p className="text-sm text-gray-600">Monitor your AI agent's progress and past tasks</p>
      </div>

      <div className="p-4">
        {currentTask && (
          <div className="mb-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Current Task:</h4>
            <TaskItem task={currentTask} isExpanded={true} />
          </div>
        )}

        {tasks.length > 0 ? (
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-gray-900">Previous Tasks:</h4>
            {tasks
              .filter(task => task.id !== currentTask?.id)
              .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
              .map(task => (
                <TaskItem key={task.id} task={task} />
              ))
            }
          </div>
        ) : !currentTask && (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-4">🤖</div>
            <div className="font-medium">No tasks yet</div>
            <div className="text-sm">Start by giving your AI agent a task to execute</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TaskHistory;
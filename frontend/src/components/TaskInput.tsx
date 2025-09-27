import React, { useState } from 'react';

interface TaskInputProps {
  onSubmitTask: (instruction: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const TaskInput: React.FC<TaskInputProps> = ({ onSubmitTask, isLoading = false, disabled = false }) => {
  const [instruction, setInstruction] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (instruction.trim() && !isLoading && !disabled) {
      onSubmitTask(instruction.trim());
      setInstruction('');
    }
  };

  const exampleTasks = [
    "Search for flights from New York to Tokyo",
    "Find the latest news about artificial intelligence",
    "Go to GitHub and search for browser automation tools",
    "Navigate to Google and search for 'best pizza recipes'",
    "Check the weather forecast for San Francisco"
  ];

  const handleExampleClick = (example: string) => {
    setInstruction(example);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          Give instructions to your AI agent
        </h2>
        <p className="text-sm text-gray-600">
          Tell the AI what you want it to do on the web. It will control the browser and complete the task for you.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="e.g., Search for the latest iPhone prices and compare them across different websites"
            rows={4}
            disabled={disabled}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
        </div>

        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">
            {instruction.length}/500 characters
          </span>
          <button
            type="submit"
            disabled={!instruction.trim() || isLoading || disabled}
            className="inline-flex items-center px-6 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </>
            ) : (
              'Execute Task'
            )}
          </button>
        </div>
      </form>

      {/* Example Tasks */}
      <div className="mt-6 border-t border-gray-200 pt-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Example tasks to try:</h3>
        <div className="space-y-2">
          {exampleTasks.map((example, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(example)}
              disabled={disabled}
              className="block w-full text-left px-3 py-2 text-sm text-primary-600 hover:bg-primary-50 rounded border border-primary-200 hover:border-primary-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TaskInput;
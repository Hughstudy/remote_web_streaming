import React, { useState, useEffect, useCallback } from 'react';
import BrowserStream from './components/BrowserStream';
import TaskInput from './components/TaskInput';
import TaskHistory from './components/TaskHistory';
import { websocketService } from './services/websocket.service';
import { apiService } from './services/api.service';
import { Task, TaskStep, WebSocketMessage, VNCInfo } from './types';

const App: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [vncInfo, setVncInfo] = useState<VNCInfo | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize WebSocket connection
  useEffect(() => {
    const initializeConnection = async () => {
      try {
        await websocketService.connect();
        setIsConnected(true);
        setError(null);

        // Request VNC info on connection
        websocketService.getVNCInfo();
      } catch (err) {
        console.error('Failed to connect to WebSocket:', err);
        setError('Failed to connect to server');
        setIsConnected(false);
      }
    };

    initializeConnection();

    return () => {
      websocketService.disconnect();
    };
  }, []);

  // Handle WebSocket messages
  useEffect(() => {
    const handleMessage = (message: WebSocketMessage) => {
      console.log('Received message:', message);

      switch (message.type) {
        case 'task_created':
          if (message.task_id && message.instruction) {
            const newTask: Task = {
              id: message.task_id,
              instruction: message.instruction,
              status: 'created',
              steps: [],
              createdAt: new Date()
            };
            setTasks(prev => [...prev, newTask]);
          }
          break;

        case 'task_update':
          if (message.task_id) {
            setTasks(prev =>
              prev.map(task =>
                task.id === message.task_id
                  ? { ...task, status: message.status as Task['status'] || task.status }
                  : task
              )
            );

            if (message.status === 'running') {
              const runningTask = tasks.find(t => t.id === message.task_id);
              if (runningTask) {
                setCurrentTask(runningTask);
              }
            }
          }
          setIsLoading(false);
          break;

        case 'step_update':
          if (message.task_id) {
            const newStep: TaskStep = {
              type: 'step_update',
              task_id: message.task_id,
              step_number: message.step_number || 0,
              action: message.action || 'unknown',
              description: message.description || '',
              timestamp: new Date()
            };

            setTasks(prev =>
              prev.map(task =>
                task.id === message.task_id
                  ? { ...task, steps: [...task.steps, newStep] }
                  : task
              )
            );

            setCurrentTask(prev =>
              prev?.id === message.task_id
                ? { ...prev, steps: [...prev.steps, newStep] }
                : prev
            );
          }
          break;

        case 'task_complete':
          if (message.task_id) {
            setTasks(prev =>
              prev.map(task =>
                task.id === message.task_id
                  ? { ...task, status: 'completed' }
                  : task
              )
            );

            setCurrentTask(prev =>
              prev?.id === message.task_id
                ? { ...prev, status: 'completed' }
                : prev
            );

            setIsLoading(false);
            // Clear current task after completion
            setTimeout(() => setCurrentTask(null), 5000);
          }
          break;

        case 'vnc_info':
          if (message.data) {
            setVncInfo(message.data);
          }
          break;

        case 'error':
          console.error('WebSocket error:', message.message);
          setError(message.message || 'An error occurred');
          setIsLoading(false);
          break;
      }
    };

    websocketService.onMessage('*', handleMessage);

    return () => {
      websocketService.offMessage('*');
    };
  }, [tasks]);

  const handleSubmitTask = useCallback(async (instruction: string) => {
    if (!isConnected) {
      setError('Not connected to server');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      // Create task via API
      const response = await apiService.createTask({ instruction });

      // Execute task via WebSocket
      websocketService.executeTask(response.task_id);

    } catch (err) {
      console.error('Error creating task:', err);
      setError('Failed to create task');
      setIsLoading(false);
    }
  }, [isConnected]);

  const handleRetryConnection = async () => {
    setError(null);
    try {
      await websocketService.connect();
      setIsConnected(true);
      websocketService.getVNCInfo();
    } catch (err) {
      setError('Failed to reconnect to server');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Web Agent</h1>
              <p className="text-sm text-gray-600">Autonomous browser automation with real-time streaming</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="text-red-400">⚠️</div>
              <span className="text-sm text-red-800">{error}</span>
            </div>
            {!isConnected && (
              <button
                onClick={handleRetryConnection}
                className="text-sm text-red-600 hover:text-red-800 font-medium"
              >
                Retry Connection
              </button>
            )}
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - Browser Stream */}
          <div className="space-y-6">
            <BrowserStream vncInfo={vncInfo} className="w-full" />
          </div>

          {/* Right Column - Controls and History */}
          <div className="space-y-6">
            <TaskInput
              onSubmitTask={handleSubmitTask}
              isLoading={isLoading}
              disabled={!isConnected}
            />

            <TaskHistory
              tasks={tasks}
              currentTask={currentTask}
              className="max-h-[600px] overflow-y-auto"
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-gray-500">
            <p>AI Web Agent - Remote Streaming • Built with FastAPI, React, and browser-use</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
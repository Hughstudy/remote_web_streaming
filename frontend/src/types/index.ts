export interface Task {
  id: string;
  instruction: string;
  status: 'created' | 'running' | 'completed' | 'failed';
  steps: TaskStep[];
  result?: string;
  createdAt: Date;
}

export interface TaskStep {
  type: 'step_update' | 'step_error';
  task_id: string;
  step_number: number;
  action: string;
  description: string;
  screenshot?: string;
  timestamp: Date;
}

export interface WebSocketMessage {
  type: 'task_created' | 'task_update' | 'step_update' | 'task_complete' | 'error' | 'vnc_info';
  task_id?: string;
  status?: string;
  message?: string;
  instruction?: string;
  data?: any;
  step_number?: number;
  action?: string;
  description?: string;
}

export interface VNCInfo {
  host: string;
  port: number;
  display: string;
  width: number;
  height: number;
  ws_url: string;
}

export interface CreateTaskRequest {
  instruction: string;
}

export interface CreateTaskResponse {
  task_id: string;
  status: string;
}
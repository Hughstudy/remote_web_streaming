import axios, { AxiosInstance } from 'axios';
import { CreateTaskRequest, CreateTaskResponse } from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.api = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error);
        return Promise.reject(error);
      }
    );
  }

  async healthCheck(): Promise<{ status: string; message: string }> {
    const response = await this.api.get('/');
    return response.data;
  }

  async createTask(request: CreateTaskRequest): Promise<CreateTaskResponse> {
    const response = await this.api.post('/task', request);
    return response.data;
  }
}

export const apiService = new ApiService();
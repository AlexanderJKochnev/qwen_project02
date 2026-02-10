// src/lib/apiClient.ts
import { API_BASE_URL } from '../config/api';

interface ApiOptions {
  method?: string;
  body?: any;
}

// let authToken: string | null = null;
// Инициализируем переменную сразу из localStorage при загрузке скрипта
let authToken: string | null = localStorage.getItem('auth_token');

export const setAuthToken = (token: string) => {
  authToken = token;
  localStorage.setItem('auth_token', token); // Обязательно сохраняем!
};

export const getAuthToken = () => {
  return authToken || localStorage.getItem('auth_token');
};

export const removeAuthToken = () => {
  authToken = null;
  localStorage.removeItem('auth_token'); // Обязательно удаляем!
};

export const getCurrentLanguage = () => {
  // This would typically come from context or localStorage
  // For now returning default language
  return 'ru'; // Default to Russian
};

export const apiClient = async <T,>(endpoint: string, options: ApiOptions = {}, includeLang: boolean = true): Promise<T> => {
  const { method = 'GET', body } = options;
  
  // Get current language if needed
  const language = includeLang ? getCurrentLanguage() : '';
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }
  
  const config: RequestInit = {
    method,
    headers,
  };
  
  if (body) {
    if (body instanceof FormData) {
      config.body = body;
      // Don't set Content-Type header for FormData, let browser set it with boundary
      delete headers['Content-Type'];
    } else {
      config.body = JSON.stringify(body);
    }
  }
  
  const response = await fetch(url, config);
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }
  
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    return await response.json();
  } else {
    return response.text() as unknown as T;
  }
};

export const deleteItem = async (endpoint: string): Promise<boolean> => {
  try {
    const response = await apiClient(endpoint, { method: 'DELETE' });
    return true;
  } catch (error) {
    console.error('Error deleting item:', error);
    return false;
  }
};
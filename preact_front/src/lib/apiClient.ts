// src/lib/apiClient.ts
// src/lib/apiClient.ts
import { API_BASE_URL } from '../config/api';

export const IMAGE_BASE_URL = `${API_BASE_URL}`;

// Function to get the current language from localStorage
export const getCurrentLanguage = () => localStorage.getItem('language') || 'en';

export const getAuthToken = () => localStorage.getItem('auth_token');
export const setAuthToken = (token: string) => localStorage.setItem('auth_token', token);
export const clearAuthToken = () => localStorage.removeItem('auth_token');
export const removeAuthToken = clearAuthToken; // Alias for clearAuthToken

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {},
  includeLang: boolean = false
): Promise<T> {
  // Build URL without language parameter
  const url = `${API_BASE_URL}${endpoint}`;
  
  console.log(`Making API request to: ${url}`, { endpoint, options, includeLang });

  const headers = new Headers(options.headers);
  headers.set('Content-Type', 'application/json');

  // Добавляем токен, если есть
  const token = getAuthToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const config: RequestInit = {
    ...options,
    headers,
    body: options.body && typeof options.body !== 'string'
      ? JSON.stringify(options.body)
      : options.body,
  };

  const response = await fetch(url, config);
  if (!response.ok) {
    if (response.status === 401) {
      clearAuthToken(); // сброс при невалидном токене
    }
    const errorText = await response.text();
    throw new Error(`HTTP ${response.status}: ${errorText}`);
  }

  return response.json() as Promise<T>;
}

export async function deleteItem(endpoint: string): Promise<boolean> {
  try {
    await apiClient(endpoint, { method: 'DELETE' }, false); // Don't include language for delete operations
    return true;
  } catch (err) {
    console.error('Delete error:', err);
    return false;
  }
}
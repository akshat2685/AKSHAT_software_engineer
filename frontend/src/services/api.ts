import { useStore } from '../stores/projectStore';

export const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const token = useStore.getState().token;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return fetch(url, { ...options, headers });
};

// API Configuration for different environments
const getApiUrl = () => {
  // In production (Render), use the environment variable
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // In development, use the proxy
  if (import.meta.env.DEV) {
    return '/api';
  }

  // Fallback (shouldn't happen)
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiUrl();

// Helper to create full API URLs
export const getApiEndpoint = (path) => {
  // Remove leading slash if present
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;

  // If API_BASE_URL already includes /api, don't duplicate it
  if (API_BASE_URL.endsWith('/api')) {
    return `${API_BASE_URL}/${cleanPath}`;
  }

  // If in production with full URL
  if (API_BASE_URL.startsWith('http')) {
    return `${API_BASE_URL}/${cleanPath}`;
  }

  // If using proxy (/api)
  return `${API_BASE_URL}/${cleanPath}`;
};

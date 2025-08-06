import axios from 'axios';
import { getToken } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Set up axios with some sensible defaults
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout - gives the AI time to think about vacation plans
});

// Keep track of requests so we don't send the same one twice
const pendingRequests = new Map();

// Add auth token and prevent duplicate requests
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Create a unique key for this request
    const requestKey = `${config.method}:${config.url}:${JSON.stringify(config.params)}`;
    
    // If we're already waiting for the same request, just wait for that one
    if (pendingRequests.has(requestKey) && config.method === 'get') {
      return pendingRequests.get(requestKey);
    }
    
    // Store this request so we can track it
    if (config.method === 'get') {
      const requestPromise = config;
      pendingRequests.set(requestKey, requestPromise);
      
      // Remember this request key so we can clean it up later
      config.metadata = { requestKey };
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle responses and auth errors
api.interceptors.response.use(
  (response) => {
    // Clean up our request tracking
    if (response.config.metadata?.requestKey) {
      pendingRequests.delete(response.config.metadata.requestKey);
    }
    return response;
  },
  (error) => {
    // Clean up our request tracking even if something went wrong
    if (error.config?.metadata?.requestKey) {
      pendingRequests.delete(error.config.metadata.requestKey);
    }
    
    // Handle auth errors - if they're not logged in, send them to the login page
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Clear their login info since it's not working
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // Only redirect if they're not already on the login page
      if (window.location.pathname !== '/auth' && !error.config?.url?.includes('/auth/')) {
        // Add a small delay so we don't redirect immediately
        setTimeout(() => {
          window.location.href = '/auth';
        }, 100);
      }
    }
    
    return Promise.reject(error);
  }
);

// Helper function to handle API errors
const handleApiError = (error, defaultMessage = 'An error occurred') => {
  // Handle validation errors (Pydantic errors)
  if (error.response?.data?.detail && Array.isArray(error.response.data.detail)) {
    const validationErrors = error.response.data.detail
      .map(err => err.msg || 'Validation error')
      .join(', ');
    return validationErrors;
  }
  
  if (error.response?.data?.detail) {
    return String(error.response.data.detail);
  }
  
  if (error.response?.status === 404) {
    return 'Resource not found';
  }
  if (error.response?.status === 500) {
    return 'Server error. Please try again later.';
  }
  if (error.code === 'ECONNABORTED') {
    return 'Request timeout. Please try again.';
  }
  return defaultMessage;
};

// Chat API functions
export const sendMessage = async (message, conversationId = null, options = {}) => {
  try {
    const response = await api.post('/chat/', {
      message
    }, {
      ...options,
      params: conversationId ? { conversation_id: conversationId } : {},
      timeout: 45000, // 45 second timeout for chat requests (AI processing can take time)
      signal: options.signal // Support for request cancellation
    });
    
    // Ensure response.response is a string
    if (response.data && typeof response.data.response !== 'string') {
      console.error('Invalid response format:', response.data);
      throw new Error('Invalid response format from server');
    }
    
    return response.data;
  } catch (error) {
    // Handle cancellation
    if (error.name === 'AbortError' || error.message.includes('canceled')) {
      throw new Error('Request was cancelled');
    }
    
    // Special handling for chat errors
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      throw new Error('Request timed out. The AI is taking longer than expected to process your request. Please try again.');
    }
    if (error.response?.status === 408) {
      throw new Error('Request timed out. Please try again.');
    }
    if (error.response?.status === 500) {
      throw new Error('Unable to process your message. Please try again.');
    }
    throw new Error(handleApiError(error, 'Failed to send message'));
  }
};

// Conversation API functions
export const getConversations = async (options = {}) => {
  try {
    const response = await api.get('/conversations/', options);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error, 'Failed to load conversations'));
  }
};

export const getConversation = async (conversationId, options = {}) => {
  try {
    const response = await api.get(`/conversations/${conversationId}`, options);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error, 'Failed to load conversation'));
  }
};

export const createConversation = async (title = 'New Conversation', options = {}) => {
  try {
    const response = await api.post('/conversations/', { title }, options);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error, 'Failed to create conversation'));
  }
};

export const updateConversation = async (conversationId, data, options = {}) => {
  try {
    const response = await api.patch(`/conversations/${conversationId}`, data, options);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error, 'Failed to update conversation'));
  }
};

export const deleteConversation = async (conversationId, options = {}) => {
  try {
    const response = await api.delete(`/conversations/${conversationId}`, options);
    return response.data;
  } catch (error) {
    throw new Error(handleApiError(error, 'Failed to delete conversation'));
  }
};

// Batch operations for better performance
export const batchGetConversations = async (conversationIds, options = {}) => {
  try {
    const promises = conversationIds.map(id => 
      getConversation(id, options).catch(error => {
        console.warn(`Failed to load conversation ${id}:`, error);
        return null;
      })
    );
    
    const results = await Promise.allSettled(promises);
    return results
      .filter(result => result.status === 'fulfilled' && result.value)
      .map(result => result.value);
  } catch (error) {
    throw new Error(handleApiError(error, 'Failed to load conversations'));
  }
};

export default api;
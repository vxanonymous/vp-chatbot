import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const authApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token management
export const getToken = () => localStorage.getItem('token');

// User management

export const setToken = (token) => localStorage.setItem('token', token);

export const removeToken = () => localStorage.removeItem('token');


export const getUser = () => {

  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
};
// Auth API calls

export const setUser = (user) => localStorage.setItem('user', JSON.stringify(user));

export const removeUser = () => localStorage.removeItem('user');


export const login = async (email, password) => {

  try {

    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await authApi.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    const { access_token, user_id, email: userEmail, full_name } = response.data;
    

    const user = {
      id: user_id,
      email: userEmail,
      full_name: full_name,
    };
    
    setToken(access_token);
    setUser(user);
    
    return response.data;
  } catch (error) {

    if (error.response?.data?.detail && Array.isArray(error.response.data.detail)) {
      const validationErrors = error.response.data.detail
        .map(err => err.msg || 'Validation error')
        .join(', ');
      throw new Error(validationErrors);
    }
    
    if (error.response?.data?.detail) {
      throw new Error(String(error.response.data.detail));
    }
    
    throw new Error('Login failed. Please try again.');
  }
};

export const signup = async (email, password, fullName) => {

  try {
    const response = await authApi.post('/auth/signup', {
      email,
      password,
      full_name: fullName,
    });
    
    const { access_token, user_id, email: userEmail, full_name } = response.data;
    

    const user = {
      id: user_id,
      email: userEmail,
      full_name: full_name,
    };
    
    setToken(access_token);
    setUser(user);
    
    return response.data;
  } catch (error) {

    if (error.response?.data?.detail && Array.isArray(error.response.data.detail)) {
      const validationErrors = error.response.data.detail
        .map(err => err.msg || 'Validation error')
        .join(', ');
      throw new Error(validationErrors);
    }
    
    if (error.response?.data?.detail) {
      throw new Error(String(error.response.data.detail));
    }
    
    throw new Error('Signup failed. Please try again.');
  }
};

export const logout = () => {

  removeToken();
  removeUser();
};
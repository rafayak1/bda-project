// axiosConfig.tsx
import axios, { AxiosRequestConfig, AxiosInstance } from 'axios';

const axiosInstance: AxiosInstance = axios.create({
  baseURL: 'http://127.0.0.1:5000', // Replace with your backend URL
  withCredentials: true,
});

axiosInstance.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('token'); // Fetch token from localStorage
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`; // Attach token to Authorization header
    }
    return config;
  },
  (error) => {
    return Promise.reject(error); // Handle errors
  }
);

// Make sure you are default exporting the axiosInstance
export default axiosInstance;


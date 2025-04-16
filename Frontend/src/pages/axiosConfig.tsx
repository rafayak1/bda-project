import axios, { AxiosRequestConfig, AxiosInstance } from 'axios';

const axiosInstance: AxiosInstance = axios.create({
  // baseURL: 'http://127.0.0.1:5002',
 // baseURL: 'http://35.188.83.222:5000',
  baseURL: 'https://flask-backend-208526089481.us-central1.run.app',
  withCredentials: true,
});

axiosInstance.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    const token = localStorage.getItem('token'); 
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`; 
    }
    return config;
  },
  (error) => {
    return Promise.reject(error); 
  }
);

export default axiosInstance;


import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL?.trim() || '/api';

export const api = axios.create({
  baseURL,
  timeout: 60000,
});

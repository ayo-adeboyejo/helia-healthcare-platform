import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
    return Promise.reject(err);
  }
);

export const authAPI = {
  register:      (data) => api.post('/auth/register',       data),
  login:         (data) => api.post('/auth/login',          data),
  logout:        (data) => api.post('/auth/logout',         data),
  verifyEmail:   (data) => api.post('/auth/verify-email',   data),
  forgotPassword:(data) => api.post('/auth/forgot-password',data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
  refresh:       (data) => api.post('/auth/refresh',        data),
};

export const userAPI = {
  createPatient:    (data)     => api.post('/patients',                    data),
  getPatient:       (userId)   => api.get(`/patients/${userId}`),
  updatePatient:    (uid, data)=> api.put(`/patients/${uid}`,              data),
  listSpecialties:  ()         => api.get('/specialties'),
  listDoctors:      (params)   => api.get('/doctors',       { params }),
  getDoctor:        (id)       => api.get(`/doctors/${id}`),
  getDoctorSlots:   (id)       => api.get(`/doctors/${id}/availability`),
  getDoctorReviews: (id)       => api.get(`/doctors/${id}/reviews`),
};

export default api;

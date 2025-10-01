// src/services/api.js
const API_BASE_URL = 'http://localhost:8000'; 

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'API request failed');
      }
      
      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Prescription endpoints
  async uploadPrescription(file) {
    const formData = new FormData();
    formData.append('image', file);
    
    const response = await fetch(`${API_BASE_URL}/analyze-prescription`, {
      method: 'POST',
      body: formData,
    });
    
    return response.json();
  }

  async analyzeDiagnostic(file) {
    const formData = new FormData();
    formData.append('image', file);
    
    return this.request('/analyze-diagnostic', {
      method: 'POST',
      body: formData,
      headers: {}, // Remove Content-Type for FormData
    });
  }

  // Patient endpoints
  async getPatientPreferences(patientName) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/preferences`);
  }

  async updatePatientPreferences(patientName, preferences) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/preferences`, {
      method: 'POST',
      body: JSON.stringify(preferences),
    });
  }

  async getPatientProfile(patientName) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/profile`);
  }

  async updatePatientProfile(patientName, profile) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/profile`, {
      method: 'PUT',
      body: JSON.stringify(profile),
    });
  }

  // Reminder endpoints
  async getScheduledReminders(patientName) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/scheduled-reminders`);
  }

  async getAllScheduledReminders() {
    return this.request('/scheduled-reminders');
  }

  async getReminderHistory(patientName, days = 7) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/history?days=${days}`);
  }

  async removePatientReminders(patientName) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/reminders`, {
      method: 'DELETE',
    });
  }

  // Notification endpoints
  async testNotification(patientName) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/test-notification`, {
      method: 'POST',
    });
  }

  async getPatientNotifications(patientName, unreadOnly = false) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/notifications?unread_only=${unreadOnly}`);
  }

  async markNotificationRead(patientName, notificationId) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/notifications/${notificationId}/read`, {
      method: 'POST',
    });
  }

  // Device token management
  async addDeviceToken(patientName, token) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/device-tokens`, {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  async removeDeviceToken(patientName, token) {
    return this.request(`/patients/${encodeURIComponent(patientName)}/device-tokens`, {
      method: 'DELETE',
      body: JSON.stringify({ token }),
    });
  }

  // System endpoints
  async getAllPatients() {
    return this.request('/patients');
  }

  async getSchedulerStatus() {
    return this.request('/scheduler/status');
  }

  async getAvailableVoices() {
    return this.request('/voices');
  }

  async setVoice(voiceName) {
    return this.request('/set-voice', {
      method: 'POST',
      body: JSON.stringify({ voice_name: voiceName }),
    });
  }

  async testVoiceSystem(patientName = 'Test User') {
    return this.request(`/test-voice?patient_name=${encodeURIComponent(patientName)}`, {
      method: 'POST',
    });
  }
}

const apiService = new ApiService();
export default apiService;
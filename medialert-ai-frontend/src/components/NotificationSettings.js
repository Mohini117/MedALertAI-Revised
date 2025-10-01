import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Settings, Bell, Mail, Phone, MessageCircle, Volume2, TestTube, Save, CheckCircle, AlertCircle } from 'lucide-react';
import apiService from '../services/api'; // Import real API service

// Create a stable ContactInput component outside the main component
const ContactInput = React.memo(({ icon: Icon, label, field, type, placeholder, enabled, value, onChange, isLoading }) => {
  return (
    <div className={`transition-all duration-300 ${enabled ? 'opacity-100' : 'opacity-50'}`}>
      <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center">
        <div className="p-2 bg-blue-100 rounded-lg mr-3">
          <Icon className="h-4 w-4 text-blue-600" />
        </div>
        {label}
        {enabled && <span className="text-red-500 ml-1">*</span>}
      </label>
      <input
        type={type}
        placeholder={placeholder}
        value={value || ''}
        onChange={onChange}
        disabled={!enabled || isLoading}
        className={`w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 transition-all duration-300 ${
          !enabled ? 'bg-gray-50 cursor-not-allowed text-gray-400' : 'bg-white hover:border-gray-300'
        }`}
      />
    </div>
  );
});

ContactInput.displayName = 'ContactInput';

// Create a stable NotificationToggle component outside the main component
const NotificationToggle = React.memo(({ icon: Icon, label, field, description, checked, onChange, isLoading }) => (
  <div className="flex items-center justify-between p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100 hover:shadow-md transition-all duration-300 hover:scale-[1.02]">
    <div className="flex items-center space-x-4">
      <div className="p-3 bg-white rounded-lg shadow-sm">
        <Icon className="h-6 w-6 text-blue-600" />
      </div>
      <div className="flex-1">
        <p className="font-semibold text-gray-900 text-lg">{label}</p>
        {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
      </div>
    </div>
    <label className="relative inline-flex items-center cursor-pointer">
      <input
        type="checkbox"
        checked={checked || false}
        onChange={onChange}
        className="sr-only peer"
        disabled={isLoading}
      />
      <div className="w-14 h-8 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-6 peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-7 after:w-7 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-blue-500 peer-checked:to-indigo-600 shadow-lg disabled:opacity-50"></div>
    </label>
  </div>
));

NotificationToggle.displayName = 'NotificationToggle';

const NotificationSettings = ({ patientName = "Demo Patient", onSettingsUpdate }) => {
  const [preferences, setPreferences] = useState({
    notification_sound: 'default',
    reminder_frequency: 'daily',
    voice_enabled: true,
    push_notifications: true,
    email_notifications: false,
    sms_notifications: false,
    whatsapp_notifications: false,
    email: '',
    phone: '',
    whatsapp: ''
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (patientName) {
      loadPreferences();
    }
  }, [patientName]);

  const loadPreferences = useCallback(async () => {
    setIsLoading(true);
    setError('');
    
    try {
      const result = await apiService.getPatientPreferences(patientName);
      if (result.status === 'success' && result.data) {
        setPreferences(prevPrefs => ({ ...prevPrefs, ...result.data }));
      } else {
        throw new Error(result.message || 'Failed to load preferences');
      }
    } catch (error) {
      console.error('Error loading preferences:', error);
      setError('Failed to load notification preferences');
      
      // Handle specific API errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        setError('Unable to connect to server. Please check if the backend is running.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [patientName]);

  const handleInputChange = useCallback((field, value) => {
    setPreferences(prev => ({ 
      ...prev, 
      [field]: value 
    }));
    setSaveStatus('');
    setError('');
  }, []);

  // Create stable handlers for each input field
  const handleEmailChange = useCallback((e) => {
    handleInputChange('email', e.target.value);
  }, [handleInputChange]);

  const handlePhoneChange = useCallback((e) => {
    handleInputChange('phone', e.target.value);
  }, [handleInputChange]);

  const handleWhatsAppChange = useCallback((e) => {
    handleInputChange('whatsapp', e.target.value);
  }, [handleInputChange]);

  // Create stable handlers for toggles
  const createToggleHandler = useCallback((field) => {
    return (e) => handleInputChange(field, e.target.checked);
  }, [handleInputChange]);

  const handleSave = useCallback(async () => {
    setIsLoading(true);
    setSaveStatus('');
    setError('');
    
    try {
      // Validate required fields if notifications are enabled
      if (preferences.email_notifications && !preferences.email) {
        throw new Error('Email address is required for email notifications');
      }
      if (preferences.sms_notifications && !preferences.phone) {
        throw new Error('Phone number is required for SMS notifications');
      }
      if (preferences.whatsapp_notifications && !preferences.whatsapp) {
        throw new Error('WhatsApp number is required for WhatsApp notifications');
      }

      const result = await apiService.updatePatientPreferences(patientName, preferences);
      if (result.status === 'success') {
        setSaveStatus('success');
        if (onSettingsUpdate) {
          onSettingsUpdate();
        }
        setTimeout(() => setSaveStatus(''), 3000);
      } else {
        throw new Error(result.message || 'Failed to save settings');
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      setSaveStatus('error');
      setError(error.message);
      setTimeout(() => setSaveStatus(''), 5000);
    } finally {
      setIsLoading(false);
    }
  }, [preferences, patientName, onSettingsUpdate]);

  const handleTest = useCallback(async () => {
    setIsTesting(true);
    setError('');
    
    try {
      const result = await apiService.testNotification(patientName);
      if (result.status === 'success') {
        const methods = result.sent_via?.length > 0 
          ? result.sent_via.join(', ') 
          : 'configured methods';
        alert(`✅ Test notification sent successfully via: ${methods}`);
      } else {
        alert(`⚠️ ${result.message || 'Test notification failed'}`);
      }
    } catch (error) {
      console.error('Error testing notification:', error);
      setError('Failed to send test notification');
      alert(`❌ Error testing notification: ${error.message}`);
    } finally {
      setIsTesting(false);
    }
  }, [patientName]);

  // Create stable callback functions for select dropdowns
  const handleNotificationSoundChange = useCallback((e) => {
    handleInputChange('notification_sound', e.target.value);
  }, [handleInputChange]);

  const handleReminderFrequencyChange = useCallback((e) => {
    handleInputChange('reminder_frequency', e.target.value);
  }, [handleInputChange]);

  // Loading state
  if (isLoading && !preferences.notification_sound) {
    return (
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-8 text-white">
          <h3 className="text-2xl font-bold flex items-center">
            <Settings className="mr-3 h-7 w-7" />
            Notification Settings
          </h3>
        </div>
        <div className="flex flex-col items-center justify-center py-20">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mb-4"></div>
          <span className="text-gray-600 text-lg font-medium">Loading settings...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 p-8 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="relative z-10">
          <h3 className="text-2xl font-bold mb-2 flex items-center">
            <Settings className="mr-3 h-7 w-7" />
            Notification Settings
          </h3>
          <p className="text-blue-100 text-lg">Configure alerts for {patientName}</p>
        </div>
      </div>

      <div className="p-8 space-y-10">
        {/* Error Display */}
        {error && (
          <div className="p-6 bg-red-50 border-l-4 border-red-400 rounded-xl">
            <div className="flex items-center">
              <AlertCircle className="h-6 w-6 text-red-600 mr-3" />
              <p className="text-red-700 font-semibold">{error}</p>
            </div>
          </div>
        )}

        {/* Basic Notification Settings */}
        <div>
          <h4 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-3">
              <Bell className="h-5 w-5 text-blue-600" />
            </div>
            Basic Settings
          </h4>
          <div className="space-y-4">
            <NotificationToggle
              icon={Bell}
              label="Push Notifications"
              field="push_notifications"
              description="Receive notifications on your mobile device"
              checked={preferences.push_notifications}
              onChange={createToggleHandler('push_notifications')}
              isLoading={isLoading}
            />
            <NotificationToggle
              icon={Volume2}
              label="Voice Alerts"
              field="voice_enabled"
              description="Play voice announcements for reminders"
              checked={preferences.voice_enabled}
              onChange={createToggleHandler('voice_enabled')}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Communication Methods */}
        <div>
          <h4 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
            <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-3">
              <MessageCircle className="h-5 w-5 text-green-600" />
            </div>
            Communication Methods
          </h4>
          <div className="space-y-4">
            <NotificationToggle
              icon={Mail}
              label="Email Notifications"
              field="email_notifications"
              description="Send reminders to your email address"
              checked={preferences.email_notifications}
              onChange={createToggleHandler('email_notifications')}
              isLoading={isLoading}
            />
            <NotificationToggle
              icon={Phone}
              label="SMS Notifications"
              field="sms_notifications"
              description="Send text message reminders"
              checked={preferences.sms_notifications}
              onChange={createToggleHandler('sms_notifications')}
              isLoading={isLoading}
            />
            <NotificationToggle
              icon={MessageCircle}
              label="WhatsApp Notifications"
              field="whatsapp_notifications"
              description="Send reminders via WhatsApp"
              checked={preferences.whatsapp_notifications}
              onChange={createToggleHandler('whatsapp_notifications')}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Contact Information */}
        <div>
          <h4 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
            <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
              <Phone className="h-5 w-5 text-purple-600" />
            </div>
            Contact Information
          </h4>
          <div className="grid gap-6">
            <ContactInput
              icon={Mail}
              label="Email Address"
              field="email"
              type="email"
              placeholder="Enter your email address"
              enabled={preferences.email_notifications}
              value={preferences.email}
              onChange={handleEmailChange}
              isLoading={isLoading}
            />
            <ContactInput
              icon={Phone}
              label="Phone Number"
              field="phone"
              type="tel"
              placeholder="Enter your phone number (e.g., +1234567890)"
              enabled={preferences.sms_notifications}
              value={preferences.phone}
              onChange={handlePhoneChange}
              isLoading={isLoading}
            />
            <ContactInput
              icon={MessageCircle}
              label="WhatsApp Number"
              field="whatsapp"
              type="tel"
              placeholder="Enter your WhatsApp number (e.g., +1234567890)"
              enabled={preferences.whatsapp_notifications}
              value={preferences.whatsapp}
              onChange={handleWhatsAppChange}
              isLoading={isLoading}
            />
          </div>
        </div>

        {/* Additional Settings */}
        <div>
          <h4 className="text-xl font-bold text-gray-800 mb-6 flex items-center">
            <div className="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center mr-3">
              <Settings className="h-5 w-5 text-orange-600" />
            </div>
            Additional Settings
          </h4>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Notification Sound
              </label>
              <select
                value={preferences.notification_sound || 'default'}
                onChange={handleNotificationSoundChange}
                disabled={isLoading}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 bg-white disabled:opacity-50"
              >
                <option value="default">Default</option>
                <option value="gentle">Gentle Bell</option>
                <option value="urgent">Urgent Tone</option>
                <option value="melody">Melody</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Reminder Frequency
              </label>
              <select
                value={preferences.reminder_frequency || 'daily'}
                onChange={handleReminderFrequencyChange}
                disabled={isLoading}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 bg-white disabled:opacity-50"
              >
                <option value="daily">Daily</option>
                <option value="custom">Custom Schedule</option>
              </select>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 pt-8 border-t-2 border-gray-100">
          <button
            onClick={handleSave}
            disabled={isLoading}
            className={`flex-1 flex items-center justify-center px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-300 ${
              isLoading
                ? 'bg-gray-400 text-white cursor-not-allowed'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg hover:scale-[1.02]'
            }`}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/30 border-t-white mr-3"></div>
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-3 h-5 w-5" />
                Save Settings
              </>
            )}
          </button>
          
          <button
            onClick={handleTest}
            disabled={isTesting || isLoading}
            className={`px-8 py-4 border-2 border-gray-300 rounded-xl font-semibold text-lg transition-all duration-300 ${
              (isTesting || isLoading)
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-400 hover:shadow-md hover:scale-[1.02]'
            }`}
          >
            {isTesting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-gray-400/30 border-t-gray-600 mr-3"></div>
                Testing...
              </>
            ) : (
              <>
                <TestTube className="mr-3 h-5 w-5" />
                Test Notification
              </>
            )}
          </button>
        </div>

        {/* Save Status */}
        {saveStatus && (
          <div className={`p-6 rounded-xl border-2 flex items-center space-x-3 ${
            saveStatus === 'success' 
              ? 'bg-green-50 border-green-200' 
              : 'bg-red-50 border-red-200'
          }`}>
            {saveStatus === 'success' ? (
              <CheckCircle className="h-6 w-6 text-green-600" />
            ) : (
              <AlertCircle className="h-6 w-6 text-red-600" />
            )}
            <p className={`font-semibold ${
              saveStatus === 'success' ? 'text-green-700' : 'text-red-700'
            }`}>
              {saveStatus === 'success' 
                ? 'Settings saved successfully!' 
                : 'Failed to save settings. Please try again.'
              }
            </p>
          </div>
        )}

        {/* Info Note */}
        <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-400 rounded-xl">
          <div className="flex items-start space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <CheckCircle className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="font-bold text-blue-900 text-lg mb-2">Notification System</p>
              <p className="text-blue-700 leading-relaxed">
                Your notification preferences will be applied to all future medication reminders. 
                Changes take effect immediately for new reminders.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings; 
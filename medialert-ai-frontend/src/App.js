// src/App.js - Updated with full backend integration
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Pill, CheckCircle, Upload, Calendar, Settings, Bell, AlertCircle } from 'lucide-react';
import './App.css';

// Import components
import PrescriptionUpload from './components/PrescriptionUpload';
import PrescriptionDetails from './components/PrescriptionDetails';
import NotificationSettings from './components/NotificationSettings';
import ScheduledReminders from './components/ScheduledReminders';
// import apiService from './services/api';

// Move TabButton component outside to prevent recreation on every render
const TabButton = React.memo(({ tabKey, label, Icon, disabled = false, isActive, onClick }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`tab-button ${isActive ? 'active' : ''} ${disabled ? 'disabled' : ''}`}
    title={disabled ? 'Upload a prescription first' : ''}
  >
    <span className="tab-icon-label">
      <Icon size={16} />
      {label}
    </span>
  </button>
));

TabButton.displayName = 'TabButton';

// Move SuccessMessage component outside to prevent recreation
const SuccessMessage = React.memo(({ prescription, patientName, onViewDetails, onConfigureNotifications }) => (
  <div className="success-container">
    <CheckCircle className="success-icon" size={64} />
    <h2 className="success-title">Prescription Analyzed Successfully!</h2>
    <p className="success-text">
      Medication reminders have been automatically scheduled for <strong>{patientName}</strong>
    </p>
    <div className="prescription-summary">
      {prescription && prescription.Medicines && (
        <div className="summary-stats">
          <div className="stat-item">
            <span className="stat-number">{prescription.Medicines.length}</span>
            <span className="stat-label">Medicines</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">
              {prescription.Medicines.reduce((total, medicine) => 
                total + (medicine.Timings ? medicine.Timings.length : 0), 0
              )}
            </span>
            <span className="stat-label">Daily Reminders</span>
          </div>
          <div className="stat-item">
            <span className="stat-number">
              {new Set(prescription.Medicines.map(m => m.Type)).size}
            </span>
            <span className="stat-label">Medicine Types</span>
          </div>
        </div>
      )}
    </div>
    <p className="success-subtext">
      You can now configure your notification preferences and view scheduled reminders.
    </p>
    <div className="success-buttons">
      <button onClick={onViewDetails} className="button-primary">
        View Details
      </button>
      <button onClick={onConfigureNotifications} className="button-secondary">
        Configure Notifications
      </button>
    </div>
  </div>
));

SuccessMessage.displayName = 'SuccessMessage';

const App = () => {
  const [prescription, setPrescription] = useState(null);
  const [patientName, setPatientName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  // Check backend health on component mount
  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      if (!response.ok) {
        throw new Error('Backend not responding');
      }
      const health = await response.json();
      console.log('Backend health:', health);
    } catch (error) {
      console.error('Backend health check failed:', error);
      setError('Unable to connect to backend. Please ensure the server is running on port 8000.');
    }
  }, []);

  const handleUploadSuccess = useCallback((prescriptionData) => {
    try {
      setPrescription(prescriptionData);
      const patientName = prescriptionData.Patient?.Name || 'Unknown Patient';
      setPatientName(patientName);
      setSuccessMessage(`Prescription analyzed successfully for ${patientName}!`);
      setActiveTab('details');
      setError('');
      
      // Auto-hide success message after 5 seconds
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch (error) {
      console.error('Error processing upload success:', error);
      setError('Error processing prescription data');
    }
  }, []);

  const handleUploadError = useCallback((errorMessage) => {
    setError(errorMessage);
    setSuccessMessage('');
  }, []);

  const handleSettingsUpdate = useCallback(() => {
    setSuccessMessage('Settings updated successfully!');
    setTimeout(() => setSuccessMessage(''), 3000);
  }, []);

  const handleTabChange = useCallback((tabKey) => {
    setActiveTab(tabKey);
  }, []);

  const handleViewDetails = useCallback(() => {
    setActiveTab('details');
  }, []);

  const handleConfigureNotifications = useCallback(() => {
    setActiveTab('settings');
  }, []);

  // Memoize tab buttons to prevent unnecessary re-renders
  const tabButtons = useMemo(() => [
    {
      tabKey: 'upload',
      label: 'Upload Prescription',
      Icon: Upload,
      disabled: false
    },
    {
      tabKey: 'details',
      label: 'Prescription Details',
      Icon: Calendar,
      disabled: !prescription
    },
    {
      tabKey: 'settings',
      label: 'Notification Settings',
      Icon: Settings,
      disabled: !patientName
    },
    {
      tabKey: 'reminders',
      label: 'Scheduled Reminders',
      Icon: Bell,
      disabled: !patientName
    }
  ], [prescription, patientName]);

  // Removed unused ErrorMessage component

  // Removed ContentSection wrapper to avoid nested padding and inconsistent widths

  return (
    <div className="app-container">
      {/* Header */}
      <div className="app-header">
        <div className="header-container">
          <div className="header-left">
            <Pill className="header-icon" size={24} />
            <div className="header-content">
              <h1>MedAlert AI</h1>
              <p>Smart Prescription Reminder System</p>
            </div>
          </div>
          {patientName && (
            <div className="patient-info">
              <p className="patient-label">Patient</p>
              <p className="patient-name">{patientName}</p>
            </div>
          )}
        </div>
      </div>

      {/* Success/Error Messages */}
      {successMessage && (
        <div className="notification-banner success">
          <CheckCircle size={20} />
          <span>{successMessage}</span>
          <button onClick={() => setSuccessMessage('')} className="close-button">×</button>
        </div>
      )}

      {error && (
        <div className="notification-banner error">
          <AlertCircle size={20} />
          <span>{error}</span>
          <button onClick={() => setError('')} className="close-button">×</button>
        </div>
      )}

      {/* Main Container */}
      <div className="main-container">
        {/* Tab Navigation */}
        <div className="tab-container">
          <div className="tab-flex">
            {tabButtons.map(({ tabKey, label, Icon, disabled }) => (
              <TabButton 
                key={tabKey}
                tabKey={tabKey}
                label={label}
                Icon={Icon}
                disabled={disabled}
                isActive={activeTab === tabKey}
                onClick={() => !disabled && handleTabChange(tabKey)}
              />
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="content-area">
          {activeTab === 'upload' && (
            <div className="centered-section">
              <PrescriptionUpload
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
                isLoading={isLoading}
                setIsLoading={setIsLoading}
              />
              {prescription && (
                <SuccessMessage 
                  prescription={prescription}
                  patientName={patientName}
                  onViewDetails={handleViewDetails}
                  onConfigureNotifications={handleConfigureNotifications}
                />
              )}
            </div>
          )}

          {activeTab === 'details' && prescription && (
            <PrescriptionDetails prescription={prescription} />
          )}

          {activeTab === 'settings' && patientName && (
            <NotificationSettings 
              patientName={patientName}
              onSettingsUpdate={handleSettingsUpdate}
            />
          )}

          {activeTab === 'reminders' && patientName && (
            <ScheduledReminders patientName={patientName} />
          )}

          {/* Default content when no prescription is uploaded */}
          {activeTab !== 'upload' && !prescription && !patientName && (
            <div className="empty-state">
              <Upload className="empty-icon" size={64} />
              <h3 className="empty-title">No Prescription Uploaded</h3>
              <p className="empty-text">
                Please upload a prescription image to access patient details, 
                notification settings, and scheduled reminders.
              </p>
              <button 
                onClick={() => setActiveTab('upload')} 
                className="button-primary"
              >
                Upload Prescription
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="footer">
        <p>© 2025 MedAlert AI - Your Health, Our Priority</p>
        <p>Always consult with your healthcare provider for medical advice.</p>
      </div>
    </div>
  );
};

export default App; 
import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, Clock, Pill, RefreshCw, Trash2, AlertCircle, CheckCircle, Activity } from 'lucide-react';
import apiService from '../services/api'; // Use real API service instead of mock

const ScheduledReminders = ({ patientName = "Demo Patient", refreshTrigger = 0 }) => {
  const [reminders, setReminders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const loadReminders = useCallback(async () => {
    setIsLoading(true);
    setError('');
    
    try {
      // Use real API service instead of mock
      const result = await apiService.getScheduledReminders(patientName);
      if (result.status === 'success') {
        setReminders(result.data || []);
      } else {
        throw new Error(result.message || 'Failed to load reminders');
      }
    } catch (error) {
      console.error('Error loading reminders:', error);
      setError(error.message);
      
      // Fallback to empty array on error instead of keeping old data
      setReminders([]);
    } finally {
      setIsLoading(false);
    }
  }, [patientName]);

  useEffect(() => {
    if (patientName) {
      loadReminders();
    }
  }, [patientName, refreshTrigger, loadReminders]);

  const handleRefresh = () => {
    loadReminders();
  };

  const handleRemoveAllReminders = async () => {
    if (!window.confirm('Are you sure you want to remove all reminders for this patient?')) {
      return;
    }

    try {
      setIsLoading(true);
      // Use real API service
      const result = await apiService.removePatientReminders(patientName);
      if (result.status === 'success') {
        setReminders([]);
        alert('All reminders removed successfully');
      } else {
        throw new Error(result.message || 'Failed to remove reminders');
      }
    } catch (error) {
      console.error('Error removing reminders:', error);
      alert('Error removing reminders: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  const formatNextReminder = (nextReminderTime) => {
    try {
      const date = new Date(nextReminderTime);
      const now = new Date();
      const diffMs = date - now;
      const diffHours = Math.ceil(diffMs / (1000 * 60 * 60));
      
      if (diffHours < 0) {
        return { text: 'Overdue', color: 'text-red-600', bg: 'bg-red-100' };
      } else if (diffHours < 1) {
        return { text: 'Soon', color: 'text-orange-600', bg: 'bg-orange-100' };
      } else if (diffHours < 24) {
        return { text: `In ${diffHours}h`, color: 'text-blue-600', bg: 'bg-blue-100' };
      } else {
        const diffDays = Math.ceil(diffHours / 24);
        return { text: `In ${diffDays}d`, color: 'text-green-600', bg: 'bg-green-100' };
      }
    } catch (error) {
      return { text: 'Invalid', color: 'text-gray-600', bg: 'bg-gray-100' };
    }
  };

  const getStatusConfig = (status) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return {
          color: 'text-green-700',
          bg: 'bg-green-100',
          border: 'border-green-200',
          icon: CheckCircle
        };
      case 'paused':
        return {
          color: 'text-yellow-700',
          bg: 'bg-yellow-100',
          border: 'border-yellow-200',
          icon: Clock
        };
      case 'completed':
        return {
          color: 'text-gray-700',
          bg: 'bg-gray-100',
          border: 'border-gray-200',
          icon: CheckCircle
        };
      default:
        return {
          color: 'text-blue-700',
          bg: 'bg-blue-100',
          border: 'border-blue-200',
          icon: Activity
        };
    }
  };

  const ReminderCard = ({ reminder, index }) => {
    const statusConfig = getStatusConfig(reminder.status);
    const nextReminderConfig = formatNextReminder(reminder.next_reminder);
    const StatusIcon = statusConfig.icon;

    return (
      <div className="group bg-white border-2 border-gray-100 rounded-2xl p-6 hover:shadow-2xl hover:border-blue-200 transition-all duration-300 hover:scale-[1.02] relative overflow-hidden">
        {/* Status indicator line */}
        <div className={`absolute top-0 left-0 w-full h-1 ${statusConfig.bg}`}></div>
        
        <div className="flex justify-between items-start mb-6">
          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-2 bg-blue-100 rounded-xl">
                <Pill className="h-5 w-5 text-blue-600" />
              </div>
              <h4 className="font-bold text-xl text-gray-900">
                {reminder.medicine_name || 'Unknown Medicine'}
              </h4>
            </div>
            <p className="text-gray-600 font-medium flex items-center">
              <span className="inline-block w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
              {reminder.medicine_type || 'Unknown Type'}
            </p>
          </div>
          
          <div className={`flex items-center px-3 py-2 rounded-xl text-sm font-bold border-2 ${statusConfig.bg} ${statusConfig.color} ${statusConfig.border}`}>
            <StatusIcon className="h-4 w-4 mr-2" />
            {reminder.status || 'Unknown'}
          </div>
        </div>

        <div className="space-y-4 mb-6">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center space-x-3">
              <Clock className="h-5 w-5 text-gray-600" />
              <span className="font-semibold text-gray-700">Dosage:</span>
            </div>
            <span className="font-bold text-gray-900">{reminder.dosage || 'Not specified'}</span>
          </div>
          
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
            <div className="flex items-center space-x-3">
              <Calendar className="h-5 w-5 text-gray-600" />
              <span className="font-semibold text-gray-700">Time:</span>
            </div>
            <span className="font-bold text-gray-900 font-mono bg-white px-3 py-1 rounded-lg border">
              {reminder.timing || 'Not specified'}
            </span>
          </div>
          
          {reminder.next_reminder && (
            <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100">
              <div className="flex items-center space-x-3">
                <RefreshCw className="h-5 w-5 text-blue-600" />
                <div>
                  <span className="font-semibold text-blue-700">Next reminder:</span>
                  <div className="text-sm text-gray-600">
                    {new Date(reminder.next_reminder).toLocaleString()}
                  </div>
                </div>
              </div>
              <span className={`px-3 py-2 rounded-lg font-bold text-sm ${nextReminderConfig.bg} ${nextReminderConfig.color}`}>
                {nextReminderConfig.text}
              </span>
            </div>
          )}
        </div>

        <div className="pt-4 border-t-2 border-gray-100">
          <div className="flex justify-between items-center text-xs">
            <span className="text-gray-500 font-medium">
              Created: {reminder.created_at ? new Date(reminder.created_at).toLocaleDateString() : 'Unknown'}
            </span>
            <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded-md font-mono text-xs">
              ID: {reminder.reminder_id?.substring(0, 8) || `rem_${index}`}
            </span>
          </div>
        </div>
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden max-w-4xl w-full mx-auto">
        <div className="bg-gradient-to-r from-orange-500 to-red-500 p-8 text-white">
          <h3 className="text-2xl font-bold flex items-center">
            <Calendar className="mr-3 h-7 w-7" />
            Scheduled Reminders
          </h3>
        </div>
        <div className="flex flex-col items-center justify-center py-20">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-4 border-blue-200 border-t-blue-600 mb-4"></div>
            <div className="absolute inset-0 rounded-full border-4 border-blue-100 animate-pulse"></div>
          </div>
          <span className="text-gray-600 text-lg font-medium">Loading reminders...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-xl border border-red-200 overflow-hidden max-w-4xl w-full mx-auto">
        <div className="bg-gradient-to-r from-red-500 to-pink-500 p-8 text-white">
          <h3 className="text-2xl font-bold flex items-center">
            <AlertCircle className="mr-3 h-7 w-7" />
            Error Loading Reminders
          </h3>
        </div>
        <div className="text-center py-16">
          <AlertCircle className="mx-auto h-20 w-20 text-red-400 mb-6" />
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Something went wrong</h3>
          <p className="text-gray-600 mb-8 text-lg">{error}</p>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 font-semibold text-lg transition-all duration-300 hover:scale-105"
          >
            <RefreshCw className="mr-3 h-5 w-5" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 max-w-4xl w-full mx-auto">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-500 to-red-500 p-8 text-white relative overflow-hidden">
        <div className="absolute inset-0 bg-black/10"></div>
        <div className="flex justify-between items-center relative z-10">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-white/20 rounded-xl backdrop-blur-sm">
              <Calendar className="h-8 w-8" />
            </div>
            <div>
              <h3 className="text-2xl font-bold flex items-center">
                Scheduled Reminders
                {reminders.length > 0 && (
                  <span className="ml-4 px-4 py-2 bg-white/20 rounded-full text-sm font-bold backdrop-blur-sm">
                  {reminders.length}
                </span>
              )}
              </h3>
            </div>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={handleRefresh}
              disabled={isLoading}
              className="inline-flex items-center px-6 py-3 border-2 border-white/30 rounded-xl bg-white/10 text-white font-semibold transition-all duration-300 hover:bg-white/20 hover:scale-105 disabled:opacity-50 backdrop-blur-sm"
            >
              <RefreshCw className={`mr-2 h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            
            {reminders.length > 0 && (
              <button
                onClick={handleRemoveAllReminders}
                disabled={isLoading}
                className="inline-flex items-center px-6 py-3 border-2 border-red-300/50 rounded-xl bg-red-500/20 text-white font-semibold hover:bg-red-500/30 transition-all duration-300 hover:scale-105 disabled:opacity-50 backdrop-blur-sm"
              >
                <Trash2 className="mr-2 h-5 w-5" />
                Remove All
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="p-8">
        {reminders.length === 0 ? (
          <div className="text-center py-20">
            <div className="relative mb-8">
              <Calendar className="mx-auto h-24 w-24 text-gray-300" />
              <div className="absolute -top-2 -right-2 w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                <Clock className="h-4 w-4 text-orange-600" />
              </div>
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">No Reminders Scheduled</h3>
            <p className="text-gray-600 mb-8 text-lg max-w-md mx-auto">
              Upload a prescription to automatically schedule medication reminders for your treatments.
            </p>
          </div>
        ) : (
          <>
            {/* Summary Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl p-6 text-center border border-blue-200">
                <div className="text-3xl font-bold text-blue-600 mb-2">{reminders.length}</div>
                <div className="text-sm font-semibold text-blue-800">Total Reminders</div>
              </div>
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-2xl p-6 text-center border border-green-200">
                <div className="text-3xl font-bold text-green-600 mb-2">
                  {reminders.filter(r => r.status === 'active').length}
                </div>
                <div className="text-sm font-semibold text-green-800">Active</div>
              </div>
              <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-2xl p-6 text-center border border-yellow-200">
                <div className="text-3xl font-bold text-yellow-600 mb-2">
                  {reminders.filter(r => r.status === 'paused').length}
                </div>
                <div className="text-sm font-semibold text-yellow-800">Paused</div>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-2xl p-6 text-center border border-purple-200">
                <div className="text-3xl font-bold text-purple-600 mb-2">
                  {new Set(reminders.map(r => r.medicine_name)).size}
                </div>
                <div className="text-sm font-semibold text-purple-800">Medicines</div>
              </div>
            </div>

            {/* Reminders Grid */}
            <div className="grid gap-6 lg:grid-cols-2">
              {reminders.map((reminder, index) => (
                <ReminderCard key={reminder.reminder_id || index} reminder={reminder} index={index} />
              ))}
            </div>

            {/* Footer Info */}
            <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-l-4 border-blue-400 rounded-xl">
              <div className="flex items-start space-x-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <CheckCircle className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="font-bold text-blue-900 text-lg mb-2">Reminder System Active</p>
                  <p className="text-blue-700 leading-relaxed">
                    All scheduled reminders are being processed automatically. 
                    You'll receive notifications based on your preferences in the Settings tab.
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ScheduledReminders;
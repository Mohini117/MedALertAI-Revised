// src/components/PrescriptionUpload.js - Updated for real API integration
import React, { useState } from 'react';
import { Upload, CheckCircle } from 'lucide-react';
import apiService from '../services/api';
import '../styles/PrescriptionUpload.css'; // Assuming you have some styles for this component

const PrescriptionUpload = ({ onUploadSuccess, onUploadError, isLoading, setIsLoading }) => {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);

  const validateFile = (file) => {
    if (!file) {
      throw new Error('Please select a file');
    }

    if (!file.type.startsWith('image/')) {
      throw new Error('Please upload a valid image file (PNG, JPG, JPEG)');
    }

    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      throw new Error('File size must be less than 5MB');
    }

    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    if (!allowedTypes.includes(file.type.toLowerCase())) {
      throw new Error('Only PNG, JPG, and JPEG files are allowed');
    }

    return true;
  };

  const simulateProgress = () => {
    setUploadProgress(0);
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90; // Stop at 90%, complete when actual upload finishes
        }
        return prev + Math.random() * 15;
      });
    }, 200);
    return interval;
  };

  const handleFile = async (file) => {
    if (onUploadError) onUploadError('');
    
    try {
      validateFile(file);
      setFileName(file.name);
      setIsLoading(true);
      
      // Start progress simulation
      const progressInterval = simulateProgress();
      
      try {
        console.log('Uploading file:', file.name, 'Size:', file.size);
        
        // Call the API service
        const result = await apiService.uploadPrescription(file);
        
        clearInterval(progressInterval);
        setUploadProgress(100);
        
        console.log('Upload result:', result);
        
        if (result.status === 'success') {
          // Add a small delay to show 100% progress
          setTimeout(() => {
            onUploadSuccess(result.data);
            setUploadProgress(0);
          }, 500);
        } else {
          throw new Error(result.message || 'Failed to analyze prescription');
        }
      } catch (apiError) {
        clearInterval(progressInterval);
        setUploadProgress(0);
        throw apiError;
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadProgress(0);
      setFileName('');
      
      let errorMessage = error.message;
      
      // Handle specific API errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        errorMessage = 'Unable to connect to server. Please check if the backend is running on port 8000.';
      } else if (error.message.includes('500')) {
        errorMessage = 'Server error occurred. Please try again or contact support.';
      } else if (error.message.includes('413')) {
        errorMessage = 'File is too large. Please upload a smaller image (max 5MB).';
      } else if (error.message.includes('400')) {
        errorMessage = 'Invalid file format. Please upload a valid prescription image.';
      }
      
      if (onUploadError) {
        onUploadError(errorMessage);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    setDragActive(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragActive(false);
  };

  const clearFile = () => {
    setFileName('');
    setUploadProgress(0);
    // Reset file input
    const fileInput = document.getElementById('prescription-upload');
    if (fileInput) {
      fileInput.value = '';
    }
  };

  return (
    <div className="upload-container">
      <Upload className="upload-icon" size={48} />
      <h2 className="upload-title">Upload prescription image</h2>
      <p className="upload-subtitle">
        Drag and drop your prescription or click to browse files
      </p>

      <div className="file-input-container">
        <div
          className={`file-drop-zone ${dragActive ? 'drag-active' : ''} ${isLoading ? 'loading' : ''}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          <input
            type="file"
            className="file-input"
            id="prescription-upload"
            accept=".png,.jpg,.jpeg,image/*"
            onChange={handleFileInput}
            disabled={isLoading}
          />
          
          <label htmlFor="prescription-upload" className="file-input-label">
            {isLoading ? (
              <div className="upload-loading">
                <div className="spinner" />
                <span>Processing...</span>
              </div>
            ) : (
              <>
                <Upload size={20} />
                <span>Choose File</span>
              </>
            )}
          </label>
        </div>

        {/* Progress Bar */}
        {isLoading && uploadProgress > 0 && (
          <div className="progress-container">
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <div className="progress-text">
              {uploadProgress < 90 ? 'Uploading...' : 'Analyzing prescription...'} {Math.round(uploadProgress)}%
            </div>
          </div>
        )}
      </div>

      {/* File Preview */}
      {fileName && !isLoading && (
        <div className="file-preview">
          <div className="file-info">
            <CheckCircle size={16} className="file-success-icon" />
            <span className="file-name">📄 {fileName}</span>
            <button onClick={clearFile} className="clear-file-button">
              ×
            </button>
          </div>
        </div>
      )}

      <div className="file-info">
        Supports PNG, JPG, JPEG (Max 5MB)
      </div>

      {/* Upload Tips */}
      <div className="upload-tips">
        <h4>For best results:</h4>
        <ul>
          <li>✓ Ensure the prescription is clearly visible</li>
          <li>✓ Use good lighting and avoid shadows</li>
          <li>✓ Include all medicine details and timings</li>
          <li>✓ Make sure text is readable and not blurred</li>
        </ul>
      </div>
    </div>
  );
};

export default PrescriptionUpload;
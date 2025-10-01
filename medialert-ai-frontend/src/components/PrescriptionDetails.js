// src/components/PrescriptionDetails.js
import React from 'react';
import { Pill, User, Calendar, Clock, FileText } from 'lucide-react';
// Removed unused CSS import to avoid style conflicts

const PrescriptionDetails = ({ prescription }) => {
  if (!prescription) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center max-w-md w-full mx-auto">
        <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <p className="text-gray-500">No prescription data available</p>
      </div>
    );
  }

  const patient = prescription.Patient || {};
  const medicines = prescription.Medicines || [];

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6 max-w-3xl w-full mx-auto">
      <h3 className="text-lg font-semibold text-gray-800 mb-6 flex items-center">
        <Pill className="mr-2 h-5 w-5 text-blue-600" />
        Prescription Details
      </h3>
      
      {/* Patient Information */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <h4 className="font-medium text-gray-700 mb-3 flex items-center">
          <User className="mr-2 h-4 w-4 text-gray-600" />
          Patient Information
        </h4>
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600">Name</p>
            <p className="font-medium text-gray-900">
              {patient.Name || 'Not specified'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Age</p>
            <p className="font-medium text-gray-900">
              {patient.Age || 'Not specified'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 flex items-center">
              <Calendar className="mr-1 h-3 w-3" />
              Prescription Date
            </p>
            <p className="font-medium text-gray-900">
              {prescription.Date || 'Not specified'}
            </p>
          </div>
        </div>
      </div>

      {/* Medicines List */}
      <div>
        <h4 className="font-medium text-gray-700 mb-4 flex items-center">
          <Pill className="mr-2 h-4 w-4 text-gray-600" />
          Prescribed Medicines ({medicines.length})
        </h4>
        
        {medicines.length > 0 ? (
          <div className="space-y-4">
            {medicines.map((medicine, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                <div className="flex justify-between items-start mb-3">
                  <h5 className="font-semibold text-gray-800 text-lg">
                    {medicine.Medicine || 'Unknown Medicine'}
                  </h5>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {medicine.Type || 'Unknown Type'}
                  </span>
                </div>
                
                <div className="mb-3">
                  <p className="text-sm text-gray-600 mb-1">Dosage Instructions</p>
                  <p className="font-medium text-gray-900">
                    {medicine.Dosage || 'Not specified'}
                  </p>
                </div>

                <div>
                  <p className="text-sm text-gray-600 mb-2 flex items-center">
                    <Clock className="mr-1 h-3 w-3" />
                    Reminder Times
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {medicine.Timings && medicine.Timings.length > 0 ? (
                      medicine.Timings.map((timing, idx) => (
                        <span 
                          key={idx} 
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800 border border-green-200"
                        >
                          <Clock className="mr-1 h-3 w-3" />
                          {timing}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-gray-500 italic">
                        No timing specified
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 bg-gray-50 rounded-lg">
            <Pill className="mx-auto h-8 w-8 text-gray-400 mb-2" />
            <p className="text-gray-500">No medicines found in prescription</p>
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="bg-blue-50 rounded-lg p-3">
            <p className="text-2xl font-bold text-blue-600">{medicines.length}</p>
            <p className="text-sm text-blue-800">Medicines</p>
          </div>
          <div className="bg-green-50 rounded-lg p-3">
            <p className="text-2xl font-bold text-green-600">
              {medicines.reduce((total, medicine) => 
                total + (medicine.Timings ? medicine.Timings.length : 0), 0
              )}
            </p>
            <p className="text-sm text-green-800">Daily Reminders</p>
          </div>
          <div className="bg-purple-50 rounded-lg p-3">
            <p className="text-2xl font-bold text-purple-600">
              {new Set(medicines.map(m => m.Type)).size}
            </p>
            <p className="text-sm text-purple-800">Medicine Types</p>
          </div>
          <div className="bg-orange-50 rounded-lg p-3">
            <p className="text-2xl font-bold text-orange-600">
              {patient.Name ? '1' : '0'}
            </p>
            <p className="text-sm text-orange-800">Patient</p>
          </div>
        </div>
      </div>

      {/* Action Note */}
      <div className="mt-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
        <p className="text-sm text-blue-700">
          <strong>Note:</strong> Medication reminders have been automatically scheduled based on the prescribed timings. 
          You can customize notification preferences in the Settings tab.
        </p>
      </div>
    </div>
  );
};

export default PrescriptionDetails;
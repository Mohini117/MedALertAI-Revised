# app.py - Complete FastAPI Backend
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime, timedelta
import logging
import os

# Import your existing modules
from model.llm_model_parser import ImageAnalyzer
from utils.storage import create_storage_directories, save_json_data, get_all_prescriptions
from services.notification_scheduler import (
    medication_scheduler, 
    start_medication_scheduler, 
    stop_medication_scheduler,
    add_prescription_reminders
)
from services.notification_sender import NotificationSender
from utils.user_manager import (
    get_user_preferences, 
    update_user_preferences,
    get_user_profile,
    update_user_profile,
    add_device_token,
    remove_device_token,
    get_user_device_tokens
)

# Pydantic models for request/response
from pydantic import BaseModel
from typing import Any

class UserPreferences(BaseModel):
    notification_sound: str = "default"
    reminder_frequency: str = "daily"
    voice_enabled: bool = True
    push_notifications: bool = True
    email_notifications: bool = False
    sms_notifications: bool = False
    whatsapp_notifications: bool = False
    email: str = ""
    phone: str = ""
    whatsapp: str = ""

class UserProfile(BaseModel):
    name: str
    age: Optional[int] = None
    medical_conditions: List[str] = []
    allergies: List[str] = []
    emergency_contact: str = ""

class DeviceToken(BaseModel):
    token: str

class VoiceSettings(BaseModel):
    voice_name: str

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MedAlert AI Backend",
    description="Smart Prescription Reminder System API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
analyzer = ImageAnalyzer()
notification_sender = NotificationSender()
prescriptions_dir, diagnostics_dir = create_storage_directories()

# Global startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        logger.info("Starting MediScan AI Backend...")
        
        # Start the medication scheduler
        start_medication_scheduler()
        
        logger.info("Backend services started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        logger.info("Shutting down MediScan AI Backend...")
        
        # Stop the medication scheduler
        stop_medication_scheduler()
        
        logger.info("Backend services stopped successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# ==================== PRESCRIPTION ENDPOINTS ====================

@app.post("/analyze-prescription")
async def analyze_prescription(image: UploadFile = File(...)):
    """Analyze prescription image and schedule reminders"""
    try:
        logger.info(f"Analyzing prescription image: {image.filename}")
        
        # Analyze the prescription
        result = await analyzer.analyze_prescription(image)
        
        if result:
            # Save prescription data
            file_path = save_json_data(result, prescriptions_dir, "prescription")
            result['file_path'] = str(file_path)
            
            # Add reminders to scheduler
            add_prescription_reminders(result)
            
            logger.info(f"Successfully analyzed prescription for patient: {result.get('Patient', {}).get('Name', 'Unknown')}")
            
            return {"status": "success", "data": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to analyze prescription")
            
    except Exception as e:
        logger.error(f"Error analyzing prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing prescription: {str(e)}")

@app.post("/analyze-diagnostic")
async def analyze_diagnostic(image: UploadFile = File(...)):
    """Analyze diagnostic image"""
    try:
        logger.info(f"Analyzing diagnostic image: {image.filename}")
        
        result = await analyzer.analyze_diagnostic_image(image)
        
        if result:
            file_path = save_json_data(result, diagnostics_dir, "diagnostic")
            result['file_path'] = str(file_path)
            
            return {"status": "success", "data": result}
        else:
            raise HTTPException(status_code=400, detail="Failed to analyze diagnostic image")
            
    except Exception as e:
        logger.error(f"Error analyzing diagnostic image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing diagnostic image: {str(e)}")

# ==================== PATIENT ENDPOINTS ====================

@app.get("/patients/{patient_name}/preferences")
async def get_patient_preferences(patient_name: str):
    """Get patient notification preferences"""
    try:
        preferences = await get_user_preferences(patient_name)
        return {"status": "success", "data": preferences}
    except Exception as e:
        logger.error(f"Error getting patient preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patients/{patient_name}/preferences")
async def update_patient_preferences(patient_name: str, preferences: UserPreferences):
    """Update patient notification preferences"""
    try:
        preferences_dict = preferences.dict()
        await update_user_preferences(patient_name, preferences_dict)
        return {"status": "success", "message": "Preferences updated successfully"}
    except Exception as e:
        logger.error(f"Error updating patient preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients/{patient_name}/profile")
async def get_patient_profile(patient_name: str):
    """Get patient profile"""
    try:
        profile = await get_user_profile(patient_name)
        return {"status": "success", "data": profile}
    except Exception as e:
        logger.error(f"Error getting patient profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/patients/{patient_name}/profile")
async def update_patient_profile(patient_name: str, profile: UserProfile):
    """Update patient profile"""
    try:
        profile_dict = profile.dict()
        await update_user_profile(patient_name, profile_dict)
        return {"status": "success", "message": "Profile updated successfully"}
    except Exception as e:
        logger.error(f"Error updating patient profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients")
async def get_all_patients():
    """Get list of all patients"""
    try:
        prescriptions = get_all_prescriptions()
        patients = []
        seen_patients = set()
        
        for prescription in prescriptions:
            patient_name = prescription.get('Patient', {}).get('Name')
            if patient_name and patient_name not in seen_patients:
                patients.append({
                    "name": patient_name,
                    "age": prescription.get('Patient', {}).get('Age'),
                    "prescription_date": prescription.get('Date'),
                    "medicines_count": len(prescription.get('Medicines', []))
                })
                seen_patients.add(patient_name)
        
        return {"status": "success", "data": patients}
    except Exception as e:
        logger.error(f"Error getting all patients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== REMINDER ENDPOINTS ====================

@app.get("/patients/{patient_name}/scheduled-reminders")
async def get_patient_scheduled_reminders(patient_name: str):
    """Get scheduled reminders for a patient"""
    try:
        reminders = medication_scheduler.get_patient_scheduled_reminders(patient_name)
        return {"status": "success", "data": reminders}
    except Exception as e:
        logger.error(f"Error getting scheduled reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scheduled-reminders")
async def get_all_scheduled_reminders():
    """Get all scheduled reminders for all patients"""
    try:
        reminders = medication_scheduler.get_all_scheduled_reminders()
        return {"status": "success", "data": reminders}
    except Exception as e:
        logger.error(f"Error getting all scheduled reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients/{patient_name}/history")
async def get_reminder_history(patient_name: str, days: int = Query(7, ge=1, le=30)):
    """Get reminder history for a patient"""
    try:
        history = medication_scheduler.get_reminder_history(patient_name, days)
        return {"status": "success", "data": history}
    except Exception as e:
        logger.error(f"Error getting reminder history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/patients/{patient_name}/reminders")
async def remove_patient_reminders(patient_name: str):
    """Remove all reminders for a patient"""
    try:
        medication_scheduler.remove_patient_reminders(patient_name)
        return {"status": "success", "message": f"All reminders removed for {patient_name}"}
    except Exception as e:
        logger.error(f"Error removing patient reminders: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== NOTIFICATION ENDPOINTS ====================

@app.post("/patients/{patient_name}/test-notification")
async def test_notification(patient_name: str):
    """Send a test notification to patient"""
    try:
        # Get user preferences to determine which methods to test
        preferences = await get_user_preferences(patient_name)
        
        test_message = f"🧪 This is a test notification for {patient_name}. Your MediScan AI system is working correctly!"
        sent_via = []
        
        # Test push notification
        if preferences.get('push_notifications', True):
            push_success = await notification_sender.send_push_notification(
                title="🧪 Test Notification",
                body=test_message,
                patient_name=patient_name
            )
            if push_success:
                sent_via.append('push')
        
        # Test email notification
        if preferences.get('email_notifications', False) and preferences.get('email'):
            email_success = await notification_sender.send_email_notification(
                preferences['email'], 
                "Test Notification - MediScan AI", 
                test_message
            )
            if email_success:
                sent_via.append('email')
        
        # Test SMS notification
        if preferences.get('sms_notifications', False) and preferences.get('phone'):
            sms_success = await notification_sender.send_sms_notification(
                preferences['phone'], 
                test_message
            )
            if sms_success:
                sent_via.append('sms')
        
        # Test WhatsApp notification
        if preferences.get('whatsapp_notifications', False) and preferences.get('whatsapp'):
            whatsapp_success = await notification_sender.send_whatsapp_notification(
                preferences['whatsapp'], 
                test_message
            )
            if whatsapp_success:
                sent_via.append('whatsapp')
        
        if sent_via:
            return {
                "status": "success", 
                "message": "Test notification sent successfully",
                "sent_via": sent_via
            }
        else:
            return {
                "status": "warning",
                "message": "No notification methods are configured or available",
                "sent_via": []
            }
            
    except Exception as e:
        logger.error(f"Error sending test notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/patients/{patient_name}/notifications")
async def get_patient_notifications(patient_name: str, unread_only: bool = Query(False)):
    """Get notifications for a patient"""
    try:
        notifications = await notification_sender.get_patient_notifications(patient_name, unread_only)
        return {"status": "success", "data": notifications}
    except Exception as e:
        logger.error(f"Error getting patient notifications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/patients/{patient_name}/notifications/{notification_id}/read")
async def mark_notification_read(patient_name: str, notification_id: str):
    """Mark a notification as read"""
    try:
        success = await notification_sender.mark_notification_read(patient_name, notification_id)
        if success:
            return {"status": "success", "message": "Notification marked as read"}
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DEVICE TOKEN ENDPOINTS ====================

@app.post("/patients/{patient_name}/device-tokens")
async def add_patient_device_token(patient_name: str, token_data: DeviceToken):
    """Add device token for push notifications"""
    try:
        await add_device_token(patient_name, token_data.token)
        return {"status": "success", "message": "Device token added successfully"}
    except Exception as e:
        logger.error(f"Error adding device token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/patients/{patient_name}/device-tokens")
async def remove_patient_device_token(patient_name: str, token_data: DeviceToken):
    """Remove device token"""
    try:
        await remove_device_token(patient_name, token_data.token)
        return {"status": "success", "message": "Device token removed successfully"}
    except Exception as e:
        logger.error(f"Error removing device token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SYSTEM ENDPOINTS ====================

@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get medication scheduler status"""
    try:
        status = {
            "is_running": medication_scheduler.is_running,
            "total_jobs": len(medication_scheduler.scheduled_reminders_cache),
            "patients_with_reminders": len(medication_scheduler.scheduled_reminders_cache.keys()),
            "uptime": "Running" if medication_scheduler.is_running else "Stopped"
        }
        return {"status": "success", "data": status}
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/voices")
async def get_available_voices():
    """Get available voice options for notifications"""
    try:
        # This would integrate with your voice system
        voices = [
            {"name": "default", "description": "Default System Voice"},
            {"name": "female", "description": "Female Voice"},
            {"name": "male", "description": "Male Voice"},
            {"name": "gentle", "description": "Gentle Voice"}
        ]
        return {"status": "success", "data": voices}
    except Exception as e:
        logger.error(f"Error getting available voices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/set-voice")
async def set_voice(voice_settings: VoiceSettings):
    """Set voice for notifications"""
    try:
        # Store voice preference in system settings
        voice_config_dir = Path("data/system_config")
        voice_config_dir.mkdir(exist_ok=True)
        
        voice_config = {
            "voice_name": voice_settings.voice_name,
            "updated_at": datetime.now().isoformat()
        }
        
        with open(voice_config_dir / "voice_settings.json", 'w') as f:
            json.dump(voice_config, f, indent=2)
        
        return {"status": "success", "message": f"Voice set to {voice_settings.voice_name}"}
    except Exception as e:
        logger.error(f"Error setting voice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/test-voice")
async def test_voice_system(patient_name: str = Query("Test User")):
    """Test voice system"""
    try:
        # This would integrate with your TTS system
        test_message = f"Hello {patient_name}, this is a test of the voice notification system."
        
        # Log the voice test (replace with actual TTS implementation)
        logger.info(f"Voice test message: {test_message}")
        
        return {
            "status": "success", 
            "message": "Voice test completed",
            "test_message": test_message
        }
    except Exception as e:
        logger.error(f"Error testing voice system: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== INTERNAL ENDPOINTS ====================

@app.post("/internal/websocket-notification")
async def internal_websocket_notification(notification_data: Dict[str, Any]):
    """Internal endpoint for WebSocket notifications"""
    try:
        # This would handle WebSocket broadcasting
        logger.info(f"WebSocket notification received: {notification_data}")
        return {"status": "success", "message": "WebSocket notification processed"}
    except Exception as e:
        logger.error(f"Error processing WebSocket notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HEALTH CHECK ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "scheduler": medication_scheduler.is_running,
            "notification_sender": True,
            "image_analyzer": True
        }
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MedALert AI Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
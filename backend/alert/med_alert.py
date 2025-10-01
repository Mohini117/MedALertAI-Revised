# medicine_alert_system.py
import json
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import threading
from dataclasses import dataclass
from enum import Enum
import logging

# For notifications
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests  # For WhatsApp API
import pyttsx3  # For voice alerts
from plyer import notification  # For system notifications

# FastAPI imports
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, EmailStr, validator
from typing import Optional
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationType(Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    VOICE = "voice"
    SYSTEM = "system"

@dataclass
class Patient:
    name: str
    age: int
    phone: str = ""
    email: str = ""
    whatsapp: str = ""
    preferred_notifications: List[str] = None
    
    def __post_init__(self):
        if self.preferred_notifications is None:
            self.preferred_notifications = ["voice", "system"]

@dataclass
class Medicine:
    type: str
    medicine: str
    dosage: str
    timings: List[str]

@dataclass
class Prescription:
    date: str
    patient: Patient
    medicines: List[Medicine]

class NotificationService:
    def __init__(self):
        self.tts_engine = pyttsx3.init()
        self.setup_tts()
    
    def setup_tts(self):
        """Configure text-to-speech engine"""
        voices = self.tts_engine.getProperty('voices')
        self.tts_engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 0.9)
    
    async def send_email(self, patient: Patient, medicine: str, dosage: str):
        """Send email notification"""
        try:
            # Configure your email settings
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            sender_email = "your_email@gmail.com"  # Replace with your email
            sender_password = "your_app_password"  # Use app password for Gmail
            
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = patient.email
            msg['Subject'] = f"Medicine Reminder - {medicine}"
            
            body = f"""
            Dear {patient.name},
            
            This is a reminder to take your medicine:
            
            Medicine: {medicine}
            Dosage: {dosage}
            Time: {datetime.now().strftime('%I:%M %p')}
            
            Please take your medicine as prescribed.
            
            Best regards,
            Your Medicine Reminder System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, patient.email, text)
            server.quit()
            
            logger.info(f"Email sent to {patient.email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_whatsapp(self, patient: Patient, medicine: str, dosage: str):
        """Send WhatsApp notification using WhatsApp Business API"""
        try:
            # You'll need to set up WhatsApp Business API
            # This is a placeholder for the API call
            url = "https://graph.facebook.com/v17.0/YOUR_PHONE_NUMBER_ID/messages"
            headers = {
                "Authorization": "Bearer YOUR_ACCESS_TOKEN",
                "Content-Type": "application/json"
            }
            
            message = f"🔔 Medicine Reminder\n\nHi {patient.name}!\n\nTime to take your medicine:\n📋 {medicine}\n💊 {dosage}\n⏰ {datetime.now().strftime('%I:%M %p')}\n\nStay healthy! 💚"
            
            data = {
                "messaging_product": "whatsapp",
                "to": patient.whatsapp,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"WhatsApp message sent to {patient.whatsapp}")
                return True
            else:
                logger.error(f"Failed to send WhatsApp message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False
    
    async def send_sms(self, patient: Patient, medicine: str, dosage: str):
        """Send SMS notification using Twilio or similar service"""
        try:
            from twilio.rest import Client
            
            # Configure Twilio (you'll need to sign up and get credentials)
            account_sid = 'your_account_sid'
            auth_token = 'your_auth_token'
            client = Client(account_sid, auth_token)
            
            message = f"Medicine Reminder: Hi {patient.name}! Time to take {medicine} - {dosage}. Time: {datetime.now().strftime('%I:%M %p')}"
            
            message = client.messages.create(
                body=message,
                from_='+1234567890',  # Your Twilio phone number
                to=patient.phone
            )
            
            logger.info(f"SMS sent to {patient.phone}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False
    
    def send_voice_alert(self, patient: Patient, medicine: str, dosage: str):
        """Send voice notification"""
        try:
            message = f"Hello {patient.name}. This is your medicine reminder. It's time to take {medicine}. The dosage is {dosage}. Please take your medicine now."
            
            self.tts_engine.say(message)
            self.tts_engine.runAndWait()
            
            logger.info(f"Voice alert played for {patient.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to play voice alert: {e}")
            return False
    
    async def send_telegram(self, patient: Patient, medicine: str, dosage: str):
        """Send Telegram notification"""
        try:
            # You'll need to create a Telegram bot and get the bot token
            bot_token = "YOUR_TELEGRAM_BOT_TOKEN"
            chat_id = patient.telegram  # User's Telegram chat ID
            
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            message = f"🔔 *Medicine Reminder*\n\nHi {patient.name}!\n\nTime to take your medicine:\n📋 {medicine}\n💊 {dosage}\n⏰ {datetime.now().strftime('%I:%M %p')}\n\nStay healthy! 💚"
            
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logger.info(f"Telegram message sent to {patient.telegram}")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        """Send system notification"""
        try:
            notification.notify(
                title="Medicine Reminder",
                message=f"Hi {patient.name}! Time to take {medicine} - {dosage}",
                timeout=10
            )
            
            logger.info(f"System notification sent for {patient.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send system notification: {e}")
            return False

# Pydantic models for API requests
class UserPreferences(BaseModel):
    name: str
    age: int
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    whatsapp: Optional[str] = None
    telegram: Optional[str] = None
    preferred_notifications: List[str] = ["voice", "system"]
    
    @validator('preferred_notifications')
    def validate_notifications(cls, v):
        valid_types = ["email", "whatsapp", "sms", "voice", "system", "telegram"]
        for notification_type in v:
            if notification_type not in valid_types:
                raise ValueError(f"Invalid notification type: {notification_type}. Valid types: {valid_types}")
        return v
    
    @validator('phone', 'whatsapp')
    def validate_phone_numbers(cls, v):
        if v and not v.startswith('+'):
            raise ValueError("Phone numbers must include country code (e.g., +1234567890)")
        return v

class PrescriptionRequest(BaseModel):
    prescription_data: dict
    user_preferences: UserPreferences

class NotificationTest(BaseModel):
    user_preferences: UserPreferences
    test_message: str = "This is a test notification from your Medicine Reminder System"
    def __init__(self):
        self.notification_service = NotificationService()
        self.scheduled_jobs = {}
        self.app = FastAPI(title="Medicine Reminder API")
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.post("/register_user")
        async def register_user(user_preferences: UserPreferences):
            """Register user with their notification preferences"""
            return await self.register_user_preferences(user_preferences)
        
        @self.app.post("/test_notifications")
        async def test_notifications(test_request: NotificationTest, background_tasks: BackgroundTasks):
            """Test user's notification channels"""
            return await self.test_user_notifications(test_request, background_tasks)
        
        @self.app.post("/set_medicine_reminders")
        async def set_medicine_reminders(request: PrescriptionRequest, background_tasks: BackgroundTasks):
            """Set medicine reminders with user preferences"""
            return await self.process_prescription_with_preferences(request, background_tasks)
        
        @self.app.put("/update_user_preferences/{user_name}")
        async def update_user_preferences(user_name: str, user_preferences: UserPreferences):
            """Update user notification preferences"""
            return await self.update_user_preferences_endpoint(user_name, user_preferences)
        
        @self.app.get("/user_preferences/{user_name}")
        async def get_user_preferences(user_name: str):
            """Get user notification preferences"""
            return await self.get_user_preferences_endpoint(user_name)
        
        @self.app.post("/cancel_reminders/{patient_name}")
        async def cancel_reminders(patient_name: str):
            return await self.cancel_patient_reminders(patient_name)
        
        @self.app.get("/active_reminders")
        async def get_active_reminders():
            return {"active_reminders": list(self.scheduled_jobs.keys())}
        
        @self.app.get("/supported_notifications")
        async def get_supported_notifications():
            """Get list of supported notification types"""
            return {
                "supported_types": [
                    {"type": "email", "description": "Email notifications", "required_field": "email"},
                    {"type": "whatsapp", "description": "WhatsApp messages", "required_field": "whatsapp"},
                    {"type": "sms", "description": "SMS text messages", "required_field": "phone"},
                    {"type": "telegram", "description": "Telegram messages", "required_field": "telegram"},
                    {"type": "voice", "description": "Voice alerts on device", "required_field": None},
                    {"type": "system", "description": "System notifications", "required_field": None}
                ]
            }
    
    async def register_user_preferences(self, user_preferences: UserPreferences):
        """Register or update user preferences"""
        try:
            # Validate that user has provided contact info for their preferred notifications
            validation_errors = []
            
            for notification_type in user_preferences.preferred_notifications:
                if notification_type == "email" and not user_preferences.email:
                    validation_errors.append("Email address required for email notifications")
                elif notification_type == "whatsapp" and not user_preferences.whatsapp:
                    validation_errors.append("WhatsApp number required for WhatsApp notifications")
                elif notification_type == "sms" and not user_preferences.phone:
                    validation_errors.append("Phone number required for SMS notifications")
                elif notification_type == "telegram" and not user_preferences.telegram:
                    validation_errors.append("Telegram chat ID required for Telegram notifications")
            
            if validation_errors:
                raise HTTPException(status_code=400, detail=validation_errors)
            
            # Store user preferences
            self.user_preferences[user_preferences.name] = user_preferences
            
            return {
                "status": "success",
                "message": f"User preferences registered for {user_preferences.name}",
                "user": user_preferences.name,
                "preferred_notifications": user_preferences.preferred_notifications
            }
        
        except Exception as e:
            logger.error(f"Error registering user preferences: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def test_user_notifications(self, test_request: NotificationTest, background_tasks: BackgroundTasks):
        """Test user's notification channels"""
        try:
            user_prefs = test_request.user_preferences
            
            # Create a test patient object
            patient = Patient(
                name=user_prefs.name,
                age=user_prefs.age,
                phone=user_prefs.phone or "",
                email=user_prefs.email or "",
                whatsapp=user_prefs.whatsapp or "",
                preferred_notifications=user_prefs.preferred_notifications
            )
            
            # Add telegram if provided
            if hasattr(user_prefs, 'telegram'):
                patient.telegram = user_prefs.telegram or ""
            
            # Convert string notification types to enum
            notification_types = []
            for notif_type in user_prefs.preferred_notifications:
                if notif_type == "email":
                    notification_types.append(NotificationType.EMAIL)
                elif notif_type == "whatsapp":
                    notification_types.append(NotificationType.WHATSAPP)
                elif notif_type == "sms":
                    notification_types.append(NotificationType.SMS)
                elif notif_type == "voice":
                    notification_types.append(NotificationType.VOICE)
                elif notif_type == "system":
                    notification_types.append(NotificationType.SYSTEM)
            
            # Send test notifications
            background_tasks.add_task(
                self.send_test_notification,
                patient,
                test_request.test_message,
                notification_types
            )
            
            return {
                "status": "success",
                "message": f"Test notifications sent to {len(notification_types)} channels",
                "channels": user_prefs.preferred_notifications
            }
        
        except Exception as e:
            logger.error(f"Error testing notifications: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def send_test_notification(self, patient: Patient, message: str, notification_types: List[NotificationType]):
        """Send test notifications"""
        tasks = []
        
        for notification_type in notification_types:
            if notification_type == NotificationType.EMAIL and patient.email:
                tasks.append(self.notification_service.send_email(patient, "Test Medicine", message))
            elif notification_type == NotificationType.WHATSAPP and patient.whatsapp:
                tasks.append(self.notification_service.send_whatsapp(patient, "Test Medicine", message))
            elif notification_type == NotificationType.SMS and patient.phone:
                tasks.append(self.notification_service.send_sms(patient, "Test Medicine", message))
            elif notification_type == NotificationType.VOICE:
                threading.Thread(target=self.notification_service.send_voice_alert, 
                               args=(patient, "Test Medicine", message)).start()
            elif notification_type == NotificationType.SYSTEM:
                threading.Thread(target=self.notification_service.send_system_notification,
                               args=(patient, "Test Medicine", message)).start()
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def update_user_preferences_endpoint(self, user_name: str, user_preferences: UserPreferences):
        """Update existing user preferences"""
        if user_name not in self.user_preferences:
            raise HTTPException(status_code=404, detail=f"User {user_name} not found")
        
        return await self.register_user_preferences(user_preferences)
    
    async def get_user_preferences_endpoint(self, user_name: str):
        """Get user preferences"""
        if user_name not in self.user_preferences:
            raise HTTPException(status_code=404, detail=f"User {user_name} not found")
        
        return {
            "status": "success",
            "user_preferences": self.user_preferences[user_name]
        }
    
    def extract_timings_with_preferences(self, prescription_data: Dict[str, Any], user_preferences: UserPreferences) -> List[Dict]:
        """Extract timing information and merge with user preferences"""
        timings_list = []
        
        # Create patient object with user preferences
        patient_info = prescription_data.get("Patient", {})
        patient = Patient(
            name=user_preferences.name,
            age=user_preferences.age,
            phone=user_preferences.phone or "",
            email=user_preferences.email or "",
            whatsapp=user_preferences.whatsapp or "",
            preferred_notifications=user_preferences.preferred_notifications
        )
        
        # Add telegram if provided
        if hasattr(user_preferences, 'telegram'):
            patient.telegram = user_preferences.telegram or ""
        
        medicines = prescription_data.get("Medicines", [])
        
        for medicine_data in medicines:
            medicine = Medicine(
                type=medicine_data.get("Type", ""),
                medicine=medicine_data.get("Medicine", ""),
                dosage=medicine_data.get("Dosage", ""),
                timings=medicine_data.get("Timings", [])
            )
            
            for timing in medicine.timings:
                timing_info = {
                    "patient": patient,
                    "medicine": medicine,
                    "timing": timing,
                    "raw_timing": timing
                }
                timings_list.append(timing_info)
        
        return timings_list
        """Extract timing information from prescription JSON"""
        timings_list = []
        
        patient_info = prescription_data.get("Patient", {})
        patient = Patient(
            name=patient_info.get("Name", "Unknown"),
            age=patient_info.get("Age", 0),
            # These would typically come from user profile or registration
            phone=patient_info.get("Phone", ""),
            email=patient_info.get("Email", ""),
            whatsapp=patient_info.get("WhatsApp", "")
        )
        
        medicines = prescription_data.get("Medicines", [])
        
        for medicine_data in medicines:
            medicine = Medicine(
                type=medicine_data.get("Type", ""),
                medicine=medicine_data.get("Medicine", ""),
                dosage=medicine_data.get("Dosage", ""),
                timings=medicine_data.get("Timings", [])
            )
            
            for timing in medicine.timings:
                timing_info = {
                    "patient": patient,
                    "medicine": medicine,
                    "timing": timing,
                    "raw_timing": timing
                }
                timings_list.append(timing_info)
        
        return timings_list
    
    def parse_timing(self, timing_str: str) -> List[datetime]:
        """Parse timing string and return list of datetime objects"""
        parsed_times = []
        
        # Handle different timing formats
        if "-" in timing_str:
            # Range format like "1:00AM-5:00PM"
            start_time, end_time = timing_str.split("-")
            
            # For range, we might want to set reminders at specific intervals
            # For now, let's just use the start time
            try:
                parsed_time = datetime.strptime(start_time.strip(), "%I:%M%p")
                today = datetime.now().replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
                parsed_times.append(today)
            except ValueError:
                logger.error(f"Failed to parse timing: {timing_str}")
        else:
            # Single time format
            try:
                parsed_time = datetime.strptime(timing_str.strip(), "%I:%M%p")
                today = datetime.now().replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)
                parsed_times.append(today)
            except ValueError:
                logger.error(f"Failed to parse timing: {timing_str}")
        
        return parsed_times
    
    async def send_medicine_reminder(self, patient: Patient, medicine: Medicine, notification_types: List[NotificationType]):
        """Send medicine reminder through specified channels"""
        logger.info(f"Sending reminder for {patient.name} - {medicine.medicine}")
        
        # Send notifications through all specified channels
        tasks = []
        
        for notification_type in notification_types:
            if notification_type == NotificationType.EMAIL and patient.email:
                tasks.append(self.notification_service.send_email(patient, medicine.medicine, medicine.dosage))
            elif notification_type == NotificationType.WHATSAPP and patient.whatsapp:
                tasks.append(self.notification_service.send_whatsapp(patient, medicine.medicine, medicine.dosage))
            elif notification_type == NotificationType.SMS and patient.phone:
                tasks.append(self.notification_service.send_sms(patient, medicine.medicine, medicine.dosage))
            elif notification_type == NotificationType.VOICE:
                # Voice is synchronous, run in thread
                threading.Thread(target=self.notification_service.send_voice_alert, 
                               args=(patient, medicine.medicine, medicine.dosage)).start()
            elif notification_type == NotificationType.SYSTEM:
                threading.Thread(target=self.notification_service.send_system_notification,
                               args=(patient, medicine.medicine, medicine.dosage)).start()
        
        # Wait for async tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def schedule_reminders(self, timings_list: List[Dict], notification_types: List[NotificationType]):
        """Schedule reminders for all timings"""
        for timing_info in timings_list:
            patient = timing_info["patient"]
            medicine = timing_info["medicine"]
            timing_str = timing_info["timing"]
            
            parsed_times = self.parse_timing(timing_str)
            
            for parsed_time in parsed_times:
                # Schedule daily reminder
                schedule_time = parsed_time.strftime("%H:%M")
                
                job = schedule.every().day.at(schedule_time).do(
                    lambda p=patient, m=medicine, nt=notification_types: 
                    asyncio.create_task(self.send_medicine_reminder(p, m, nt))
                )
                
                job_key = f"{patient.name}_{medicine.medicine}_{schedule_time}"
                self.scheduled_jobs[job_key] = job
                
                logger.info(f"Scheduled reminder for {patient.name} - {medicine.medicine} at {schedule_time}")
    
    async def process_prescription_with_preferences(self, request: PrescriptionRequest, background_tasks: BackgroundTasks):
        """Process prescription with user preferences"""
        try:
            # First register/update user preferences
            await self.register_user_preferences(request.user_preferences)
            
            # Extract timings with user preferences
            timings_list = self.extract_timings_with_preferences(
                request.prescription_data, 
                request.user_preferences
            )
            
            if not timings_list:
                return {"status": "error", "message": "No valid timings found in prescription"}
            
            # Convert string notification types to enum
            notification_types = []
            for notif_type in request.user_preferences.preferred_notifications:
                if notif_type == "email":
                    notification_types.append(NotificationType.EMAIL)
                elif notif_type == "whatsapp":
                    notification_types.append(NotificationType.WHATSAPP)
                elif notif_type == "sms":
                    notification_types.append(NotificationType.SMS)
                elif notif_type == "voice":
                    notification_types.append(NotificationType.VOICE)
                elif notif_type == "system":
                    notification_types.append(NotificationType.SYSTEM)
            
            # Schedule reminders
            background_tasks.add_task(self.schedule_reminders, timings_list, notification_types)
            
            return {
                "status": "success",
                "message": f"Reminders set for {len(timings_list)} medicine timings",
                "user": request.user_preferences.name,
                "notification_channels": request.user_preferences.preferred_notifications,
                "timings": [
                    {
                        "patient": timing["patient"].name,
                        "medicine": timing["medicine"].medicine,
                        "timing": timing["timing"]
                    } for timing in timings_list
                ]
            }
        
        except Exception as e:
            logger.error(f"Error processing prescription with preferences: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        """Main function to process prescription and set up reminders"""
        try:
            # Extract timings from JSON
            timings_list = self.extract_timings(prescription_data)
            
            if not timings_list:
                return {"status": "error", "message": "No valid timings found in prescription"}
            
            # Default notification types (can be customized per user)
            notification_types = [
                NotificationType.VOICE,
                NotificationType.SYSTEM,
                NotificationType.EMAIL,  # if email is available
                NotificationType.WHATSAPP  # if WhatsApp is available
            ]
            
            # Schedule reminders
            background_tasks.add_task(self.schedule_reminders, timings_list, notification_types)
            
            return {
                "status": "success",
                "message": f"Reminders set for {len(timings_list)} medicine timings",
                "timings": [
                    {
                        "patient": timing["patient"].name,
                        "medicine": timing["medicine"].medicine,
                        "timing": timing["timing"]
                    } for timing in timings_list
                ]
            }
        
        except Exception as e:
            logger.error(f"Error processing prescription: {e}")
            return {"status": "error", "message": str(e)}
    
    async def cancel_patient_reminders(self, patient_name: str):
        """Cancel all reminders for a specific patient"""
        cancelled_jobs = []
        
        for job_key in list(self.scheduled_jobs.keys()):
            if job_key.startswith(patient_name):
                schedule.cancel_job(self.scheduled_jobs[job_key])
                del self.scheduled_jobs[job_key]
                cancelled_jobs.append(job_key)
        
        return {
            "status": "success",
            "message": f"Cancelled {len(cancelled_jobs)} reminders for {patient_name}",
            "cancelled_jobs": cancelled_jobs
        }
    
    def run_scheduler(self):
        """Run the scheduler in a separate thread"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def start(self):
        """Start the reminder system"""
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        # Start FastAPI server
        uvicorn.run(self.app, host="0.0.0.0", port=8001)

# Example usage and testing
if __name__ == "__main__":
    # Example prescription data
    prescription_json = {
        "Date": "6/21/2012",
        "Patient": {
            "Name": "Sarah Gonzales",
            "Age": 8,
            "Phone": "+917499732486",
            "Email": "mohinig127@gmail.com",
            "WhatsApp": "+917499732486"
        },
        "Medicines": [
            {
                "Type": "Tablet",
                "Medicine": "Amoxicillin 250mg/Susp.",
                "Dosage": "Reconstitute with water to make 60 mL suspension",
                "Timings": [
                    "1:00PM",
                    "10:00PM"
                ]
            }
        ]
    }
    
    # Initialize and start the system
    reminder_system = MedicineReminderSystem()
    
    # For testing, you can process a prescription directly
    # asyncio.run(reminder_system.process_prescription(prescription_json, None))
    
    # Start the system
    reminder_system.start() 
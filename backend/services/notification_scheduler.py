# services/notification_scheduler.py
import asyncio
import json
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from utils.storage import get_all_prescriptions
from services.notification_sender import NotificationSender
import threading
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MedicineReminder:
    patient_name: str
    medicine_name: str
    dosage: str
    timing: str
    medicine_type: str
    prescription_date: str
    file_path: str
    reminder_id: str = None
    
    def __post_init__(self):
        if self.reminder_id is None:
            self.reminder_id = str(uuid.uuid4())

@dataclass
class ScheduledReminder:
    reminder_id: str
    patient_name: str
    medicine_name: str
    dosage: str
    timing: str
    medicine_type: str
    next_reminder: str
    status: str  # 'active', 'paused', 'completed'
    created_at: str
    prescription_date: str

class MedicationScheduler:
    def __init__(self):
        self.notification_sender = NotificationSender()
        self.active_reminders = {}
        self.scheduled_reminders_cache = {}  # Cache for UI display
        self.is_running = False
        self.scheduler_thread = None
        self.async_loop = None
        self.async_thread = None
        
    def start_scheduler(self):
        """Start the medication reminder scheduler"""
        if self.is_running:
            logger.info("Scheduler is already running")
            return
            
        self.is_running = True
        logger.info("Starting medication reminder scheduler...")
        
        # Start async event loop in separate thread
        self._start_async_loop()
        
        # Load existing prescriptions and schedule reminders
        self.load_and_schedule_all_prescriptions()
        
        # Start the scheduling thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Medication scheduler started successfully")
    
    def _start_async_loop(self):
        """Start a dedicated async event loop in a separate thread"""
        def run_async_loop():
            self.async_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.async_loop)
            try:
                self.async_loop.run_forever()
            except Exception as e:
                logger.error(f"Error in async loop: {str(e)}")
            finally:
                self.async_loop.close()
        
        self.async_thread = threading.Thread(target=run_async_loop, daemon=True)
        self.async_thread.start()
        
        # Wait for loop to be ready
        while self.async_loop is None:
            time.sleep(0.01)
    
    def stop_scheduler(self):
        """Stop the medication reminder scheduler"""
        self.is_running = False
        schedule.clear()
        
        # Stop async loop
        if self.async_loop and not self.async_loop.is_closed():
            self.async_loop.call_soon_threadsafe(self.async_loop.stop)
        
        logger.info("Medication scheduler stopped")
    
    def _run_scheduler(self):
        """Internal method to run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)
    
    def load_and_schedule_all_prescriptions(self):
        """Load all prescriptions and schedule reminders"""
        try:
            prescriptions = get_all_prescriptions()
            logger.info(f"Found {len(prescriptions)} prescriptions to process")
            
            for prescription_data in prescriptions:
                self.schedule_prescription_reminders(prescription_data)
                
        except Exception as e:
            logger.error(f"Error loading prescriptions: {str(e)}")
    
    def schedule_prescription_reminders(self, prescription_data: Dict[str, Any]):
        """Schedule reminders for a single prescription"""
        try:
            patient_name = prescription_data.get('Patient', {}).get('Name', 'Unknown Patient')
            medicines = prescription_data.get('Medicines', [])
            prescription_date = prescription_data.get('Date', 'Unknown Date')
            
            for medicine in medicines:
                medicine_name = medicine.get('Medicine', 'Unknown Medicine')
                dosage = medicine.get('Dosage', 'Unknown Dosage')
                timings = medicine.get('Timings', [])
                medicine_type = medicine.get('Type', 'Unknown Type')
                
                for timing in timings:
                    reminder = MedicineReminder(
                        patient_name=patient_name,
                        medicine_name=medicine_name,
                        dosage=dosage,
                        timing=timing,
                        medicine_type=medicine_type,
                        prescription_date=prescription_date,
                        file_path=prescription_data.get('file_path', '')
                    )
                    
                    self._schedule_daily_reminder(reminder)
                    
            logger.info(f"Scheduled reminders for patient: {patient_name}")
            
        except Exception as e:
            logger.error(f"Error scheduling prescription reminders: {str(e)}")
    
    def _schedule_daily_reminder(self, reminder: MedicineReminder):
        """Schedule a daily reminder for a specific medicine timing"""
        try:
            # Convert timing to 24h format if needed
            reminder_time = self._parse_time(reminder.timing)
            
            # Create unique job identifier
            job_id = f"{reminder.patient_name}_{reminder.medicine_name}_{reminder.timing}".replace(" ", "_")
            
            # Schedule the reminder using asyncio-compatible function
            job = schedule.every().day.at(reminder_time).do(
                self._schedule_reminder_job, 
                reminder
            ).tag(job_id)
            
            # Store in cache for UI display
            scheduled_reminder = ScheduledReminder(
                reminder_id=reminder.reminder_id,
                patient_name=reminder.patient_name,
                medicine_name=reminder.medicine_name,
                dosage=reminder.dosage,
                timing=reminder.timing,
                medicine_type=reminder.medicine_type,
                next_reminder=self._get_next_reminder_time(reminder_time),
                status='active',
                created_at=datetime.now().isoformat(),
                prescription_date=reminder.prescription_date
            )
            
            # Store in patient-specific cache
            if reminder.patient_name not in self.scheduled_reminders_cache:
                self.scheduled_reminders_cache[reminder.patient_name] = []
            
            self.scheduled_reminders_cache[reminder.patient_name].append(scheduled_reminder)
            
            # Save to persistent storage for UI
            self._save_scheduled_reminders_to_file()
            
            logger.info(f"Scheduled reminder for {reminder.patient_name} - {reminder.medicine_name} at {reminder_time}")
            
        except Exception as e:
            logger.error(f"Error scheduling reminder: {str(e)}")
    
    def _get_next_reminder_time(self, reminder_time: str) -> str:
        """Calculate next reminder time"""
        try:
            today = datetime.now().date()
            reminder_datetime = datetime.combine(today, datetime.strptime(reminder_time, "%H:%M").time())
            
            # If time has passed today, schedule for tomorrow
            if reminder_datetime <= datetime.now():
                reminder_datetime += timedelta(days=1)
            
            return reminder_datetime.isoformat()
        except Exception as e:
            logger.error(f"Error calculating next reminder time: {str(e)}")
            return datetime.now().isoformat()
    
    def _save_scheduled_reminders_to_file(self):
        """Save scheduled reminders to file for UI access"""
        try:
            reminders_dir = Path("data/scheduled_reminders")
            reminders_dir.mkdir(parents=True, exist_ok=True)
            
            all_reminders = {}
            for patient_name, reminders in self.scheduled_reminders_cache.items():
                all_reminders[patient_name] = [asdict(reminder) for reminder in reminders]
            
            reminders_file = reminders_dir / "active_reminders.json"
            with open(reminders_file, 'w') as f:
                json.dump(all_reminders, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error saving scheduled reminders to file: {str(e)}")
    
    def get_patient_scheduled_reminders(self, patient_name: str) -> List[Dict]:
        """Get scheduled reminders for a specific patient for UI display"""
        try:
            if patient_name in self.scheduled_reminders_cache:
                return [asdict(reminder) for reminder in self.scheduled_reminders_cache[patient_name]]
            
            # Try to load from file if not in cache
            reminders_dir = Path("data/scheduled_reminders")
            reminders_file = reminders_dir / "active_reminders.json"
            
            if reminders_file.exists():
                with open(reminders_file, 'r') as f:
                    all_reminders = json.load(f)
                    return all_reminders.get(patient_name, [])
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting patient scheduled reminders: {str(e)}")
            return []
    
    def get_all_scheduled_reminders(self) -> Dict[str, List[Dict]]:
        """Get all scheduled reminders for all patients"""
        try:
            all_reminders = {}
            for patient_name in self.scheduled_reminders_cache:
                all_reminders[patient_name] = self.get_patient_scheduled_reminders(patient_name)
            
            return all_reminders
            
        except Exception as e:
            logger.error(f"Error getting all scheduled reminders: {str(e)}")
            return {}
    
    def _schedule_reminder_job(self, reminder: MedicineReminder):
        """Wrapper to handle async reminder sending"""
        try:
            if self.async_loop and not self.async_loop.is_closed():
                # Schedule the async task on our dedicated event loop
                asyncio.run_coroutine_threadsafe(
                    self._send_medicine_reminder(reminder), 
                    self.async_loop
                )
            else:
                logger.error("Async loop not available for reminder job")
                
        except Exception as e:
            logger.error(f"Error in reminder job: {str(e)}")
    
    def _run_async_task_safely(self, coro):
        """Safely run async task in the dedicated event loop"""
        try:
            if self.async_loop and not self.async_loop.is_closed():
                future = asyncio.run_coroutine_threadsafe(coro, self.async_loop)
                return future.result(timeout=30)  # 30 second timeout
            else:
                logger.error("Async loop not available")
                return None
        except Exception as e:
            logger.error(f"Error running async task: {str(e)}")
            return None
    
    def _parse_time(self, time_str: str) -> str:
        """Parse time string to 24h format"""
        try:
            # Handle various time formats
            time_str = time_str.strip().upper()
            original_time = time_str
            
            # Remove common suffixes and clean up
            has_pm = "PM" in time_str
            has_am = "AM" in time_str
            time_str = time_str.replace("AM", "").replace("PM", "").strip()
            
            # If time contains PM and not 12, add 12 hours
            if has_pm and not time_str.startswith("12"):
                if ":" in time_str:
                    hour, minute = time_str.split(":")
                    hour = str(int(hour) + 12)
                    time_str = f"{hour}:{minute}"
                else:
                    hour = str(int(time_str) + 12)
                    time_str = f"{hour}:00"
            elif has_am and time_str.startswith("12"):
                if ":" in time_str:
                    time_str = time_str.replace("12", "00", 1)
                else:
                    time_str = "00:00"
            
            # Ensure proper format
            if ":" not in time_str:
                time_str += ":00"
            
            # Validate time format
            hour, minute = time_str.split(":")
            hour = int(hour)
            minute = int(minute)
            
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError("Invalid time")
                
            return f"{hour:02d}:{minute:02d}"
            
        except Exception as e:
            logger.error(f"Error parsing time {original_time}: {str(e)}")
            return "09:00"  # Default time
    
    async def _send_medicine_reminder(self, reminder: MedicineReminder):
        """Send medicine reminder notification based on user preferences"""
        try:
            # Get user preferences
            from utils.user_manager import get_user_preferences
            preferences = await get_user_preferences(reminder.patient_name)
            
            # Create reminder message
            message = self._create_reminder_message(reminder)
            
            sent_successfully = False
            sent_via = []
            
            # Send notifications based on user preferences
            if preferences.get('push_notifications', True):
                push_success = await self.notification_sender.send_push_notification(
                    title="💊 Medicine Reminder",
                    body=message,
                    patient_name=reminder.patient_name
                )
                if push_success:
                    sent_successfully = True
                    sent_via.append('push')
            
            if preferences.get('email_notifications', False):
                email = preferences.get('email', '')
                if email:
                    email_success = await self.notification_sender.send_email_notification(
                        email, "Medicine Reminder", message
                    )
                    if email_success:
                        sent_successfully = True
                        sent_via.append('email')
            
            if preferences.get('sms_notifications', False):
                phone = preferences.get('phone', '')
                if phone:
                    sms_success = await self.notification_sender.send_sms_notification(
                        phone, message
                    )
                    if sms_success:
                        sent_successfully = True
                        sent_via.append('sms')
            
            if preferences.get('whatsapp_notifications', False):
                whatsapp = preferences.get('whatsapp', '')
                if whatsapp:
                    whatsapp_success = await self.notification_sender.send_whatsapp_notification(
                        whatsapp, message
                    )
                    if whatsapp_success:
                        sent_successfully = True
                        sent_via.append('whatsapp')
            
            # Log the reminder
            if sent_successfully:
                logger.info(f"Sent reminder to {reminder.patient_name} for {reminder.medicine_name} via {', '.join(sent_via)}")
                await self._store_reminder_history(reminder, sent_successfully, preferences, sent_via)
            else:
                logger.warning(f"Failed to send reminder to {reminder.patient_name} for {reminder.medicine_name}")
            
        except Exception as e:
            logger.error(f"Error sending reminder: {str(e)}")
    
    def _create_reminder_message(self, reminder: MedicineReminder) -> str:
        """Create a friendly reminder message"""
        return (f"Hi {reminder.patient_name}! It's time to take your "
                f"{reminder.medicine_name}. Dosage: {reminder.dosage}. "
                f"Remember to take your medication on time for better health! 💊")
    
    async def _store_reminder_history(self, reminder: MedicineReminder, success: bool, preferences: Dict, sent_via: List[str]):
        """Store reminder history for tracking"""
        try:
            history_dir = Path("data/reminder_history")
            history_dir.mkdir(parents=True, exist_ok=True)
            
            history_file = history_dir / f"{reminder.patient_name.replace(' ', '_')}_history.json"
            
            # Load existing history
            history = []
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
            
            # Add new reminder record
            history_record = {
                "timestamp": datetime.now().isoformat(),
                "reminder_id": reminder.reminder_id,
                "patient_name": reminder.patient_name,
                "medicine_name": reminder.medicine_name,
                "dosage": reminder.dosage,
                "timing": reminder.timing,
                "sent_via": sent_via,
                "status": "sent" if success else "failed"
            }
            
            history.append(history_record)
            
            # Keep only last 100 records per patient
            history = history[-100:]
            
            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error storing reminder history: {str(e)}")
    
    def add_new_prescription_reminders(self, prescription_data: Dict[str, Any]):
        """Add reminders for a newly uploaded prescription"""
        try:
            # Schedule the prescription reminders first
            self.schedule_prescription_reminders(prescription_data)
            
            patient_name = prescription_data.get('Patient', {}).get('Name', 'Unknown Patient')
            logger.info(f"Successfully added prescription reminders for {patient_name}")
            
        except Exception as e:
            logger.error(f"Error adding new prescription reminders: {str(e)}")
        
    def remove_patient_reminders(self, patient_name: str):
        """Remove all reminders for a specific patient"""
        try:
            # Find and cancel jobs for this patient
            jobs_to_cancel = [job for job in schedule.jobs 
                            if patient_name.replace(" ", "_") in str(job.tags)]
            
            for job in jobs_to_cancel:
                schedule.cancel_job(job)
            
            # Remove from cache
            if patient_name in self.scheduled_reminders_cache:
                del self.scheduled_reminders_cache[patient_name]
            
            # Update persistent storage
            self._save_scheduled_reminders_to_file()
                
            logger.info(f"Removed all reminders for patient: {patient_name}")
            
        except Exception as e:
            logger.error(f"Error removing patient reminders: {str(e)}")
    
    def get_scheduled_reminders(self, patient_name: str = None) -> List[Dict]:
        """Get list of scheduled reminders (legacy method for compatibility)"""
        try:
            reminders = []
            for job in schedule.jobs:
                job_info = {
                    "next_run": str(job.next_run),
                    "job_func": str(job.job_func),
                    "tags": list(job.tags) if job.tags else []
                }
                
                if patient_name:
                    if patient_name.replace(" ", "_") in str(job.tags):
                        reminders.append(job_info)
                else:
                    reminders.append(job_info)
                    
            return reminders
            
        except Exception as e:
            logger.error(f"Error getting scheduled reminders: {str(e)}")
            return []
    
    def get_reminder_history(self, patient_name: str, days: int = 7) -> List[Dict]:
        """Get reminder history for a patient"""
        try:
            history_dir = Path("data/reminder_history")
            history_file = history_dir / f"{patient_name.replace(' ', '_')}_history.json"
            
            if not history_file.exists():
                return []
            
            with open(history_file, 'r') as f:
                history = json.load(f)
            
            # Filter by days
            cutoff_date = datetime.now() - timedelta(days=days)
            filtered_history = [
                record for record in history
                if datetime.fromisoformat(record['timestamp']) > cutoff_date
            ]
            
            return filtered_history
            
        except Exception as e:
            logger.error(f"Error getting reminder history: {str(e)}")
            return []

# Global scheduler instance
medication_scheduler = MedicationScheduler()

def start_medication_scheduler():
    """Start the global medication scheduler"""
    medication_scheduler.start_scheduler()

def stop_medication_scheduler():
    """Stop the global medication scheduler"""
    medication_scheduler.stop_scheduler()

def add_prescription_reminders(prescription_data: Dict[str, Any]):
    """Add reminders for a new prescription"""
    medication_scheduler.add_new_prescription_reminders(prescription_data) 
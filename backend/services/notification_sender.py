# services/notification_sender.py
import asyncio
import json
import logging
from typing import Dict, List, Optional
import aiohttp
from pathlib import Path
from dataclasses import dataclass, asdict
import firebase_admin
from firebase_admin import credentials, messaging
from utils.user_manager import get_user_device_tokens
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class NotificationData:
    title: str
    body: str
    patient_name: str
    notification_type: str = "medicine_reminder"
    data: Dict = None

class NotificationSender:
    def __init__(self):
        self.firebase_app = None
        self.initialize_firebase()
        self.initialize_email_config()
        
    def initialize_firebase(self):
        """Initialize Firebase Admin SDK for push notifications"""
        try:
            # Path to your Firebase service account key
            service_account_path = Path("config/firebase_service_account.json")
            
            if service_account_path.exists():
                cred = credentials.Certificate(str(service_account_path))
                if not firebase_admin._apps:
                    self.firebase_app = firebase_admin.initialize_app(cred)
                else:
                    self.firebase_app = firebase_admin.get_app()
                logger.info("Firebase initialized successfully")
            else:
                logger.warning("Firebase service account file not found. Push notifications disabled.")
                
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
    
    def initialize_email_config(self):
        """Initialize email configuration"""
        try:
            self.email_config = {
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'email_user': os.getenv('EMAIL_USER', ''),
                'email_password': os.getenv('EMAIL_PASSWORD', ''),
                'from_name': os.getenv('FROM_NAME', 'MediScan AI')
            }
            
            if self.email_config['email_user']:
                logger.info("Email configuration initialized")
            else:
                logger.warning("Email configuration not found. Email notifications disabled.")
                
        except Exception as e:
            logger.error(f"Error initializing email config: {str(e)}")
            
    async def send_push_notification(self, title: str, body: str, patient_name: str, 
                                   notification_data: Dict = None):
        """Send push notification to user's devices"""
        try:
            if not self.firebase_app:
                logger.warning("Firebase not initialized. Cannot send push notification.")
                return False
                
            # Get user device tokens
            device_tokens = await get_user_device_tokens(patient_name)
            
            if not device_tokens:
                logger.warning(f"No device tokens found for patient: {patient_name}")
                return False
            
            # Create notification payload
            notification = messaging.Notification(
                title=title,
                body=body
            )
            
            # Create data payload
            data = {
                "type": "medicine_reminder",
                "patient_name": patient_name,
                "timestamp": str(asyncio.get_event_loop().time()),
                **(notification_data or {})
            }
            
            # Send to multiple devices
            messages = []
            for token in device_tokens:
                message = messaging.Message(
                    notification=notification,
                    data=data,
                    token=token,
                    android=messaging.AndroidConfig(
                        priority='high',
                        notification=messaging.AndroidNotification(
                            icon='medicine_icon',
                            sound='medicine_reminder_sound',
                            default_sound=True,
                            vibrate_timings_millis=[200, 200, 200],
                            priority='max'
                        )
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                alert=messaging.ApsAlert(
                                    title=title,
                                    body=body
                                ),
                                sound='medicine_reminder.wav',
                                badge=1,
                                category='MEDICINE_REMINDER'
                            )
                        )
                    )
                )
                messages.append(message)
            
            # Send batch notification
            response = messaging.send_all(messages)
            
            logger.info(f"Sent {response.success_count} push notifications successfully")
            if response.failure_count > 0:
                logger.warning(f"Failed to send {response.failure_count} push notifications")
                
            return response.success_count > 0
            
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return False
    
    async def send_web_notification(self, notification_data: NotificationData):
        """Send web push notification using WebSocket or Server-Sent Events"""
        try:
            # Store notification for web clients
            await self._store_web_notification(notification_data)
            
            # Send via WebSocket if available
            await self._send_websocket_notification(notification_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending web notification: {str(e)}")
            return False
    
    async def _store_web_notification(self, notification_data: NotificationData):
        """Store notification for web clients to retrieve"""
        try:
            notifications_dir = Path("data/notifications")
            notifications_dir.mkdir(exist_ok=True)
            
            patient_file = notifications_dir / f"{notification_data.patient_name.replace(' ', '_')}_notifications.json"
            
            # Load existing notifications
            notifications = []
            if patient_file.exists():
                with open(patient_file, 'r') as f:
                    notifications = json.load(f)
            
            # Add new notification
            notification_dict = asdict(notification_data)
            notification_dict['timestamp'] = asyncio.get_event_loop().time()
            notification_dict['read'] = False
            
            notifications.append(notification_dict)
            
            # Keep only last 50 notifications per patient
            notifications = notifications[-50:]
            
            # Save updated notifications
            with open(patient_file, 'w') as f:
                json.dump(notifications, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error storing web notification: {str(e)}")
    
    async def _send_websocket_notification(self, notification_data: NotificationData):
        """Send notification via WebSocket to connected clients"""
        try:
            # This would integrate with your WebSocket server
            # For now, we'll implement a simple HTTP endpoint call
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    "type": "notification",
                    "data": asdict(notification_data)
                }
                
                # Send to local WebSocket server endpoint
                async with session.post(
                    "http://localhost:8000/internal/websocket-notification",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        logger.info("WebSocket notification sent successfully")
                    else:
                        logger.warning(f"WebSocket notification failed: {response.status}")
                        
        except Exception as e:
            logger.debug(f"WebSocket notification not available: {str(e)}")
    
    async def send_email_notification(self, email: str, subject: str, content: str):
        """Send email notification"""
        try:
            if not self.email_config.get('email_user'):
                logger.warning("Email configuration not available")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.email_config['from_name']} <{self.email_config['email_user']}>"
            msg['To'] = email
            msg['Subject'] = subject
            
            # Add HTML content
            html_content = f"""
            <html>
                <body>
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                        <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
                            <h2>💊 MediScan AI - Medicine Reminder</h2>
                        </div>
                        <div style="padding: 20px; background-color: #f9f9f9;">
                            <p style="font-size: 16px; line-height: 1.6;">{content}</p>
                            <p style="color: #666; font-size: 14px; margin-top: 20px;">
                                This is an automated reminder from your MediScan AI system.
                            </p>
                        </div>
                        <div style="background-color: #333; color: white; padding: 10px; text-align: center; font-size: 12px;">
                            MediScan AI - Your Health, Our Priority
                        </div>
                    </div>
                </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email_user'], self.email_config['email_password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['email_user'], email, text)
            server.quit()
            
            logger.info(f"Email notification sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    async def send_sms_notification(self, phone_number: str, message: str):
        """Send SMS notification using Twilio or similar service"""
        try:
            # This is a placeholder for SMS implementation
            # You would integrate with Twilio, AWS SNS, or other SMS service
            
            # For demonstration, we'll use a mock implementation
            # In production, replace with actual SMS service
            
            sms_config = {
                'account_sid': os.getenv('TWILIO_ACCOUNT_SID', ''),
                'auth_token': os.getenv('TWILIO_AUTH_TOKEN', ''),
                'from_number': os.getenv('TWILIO_FROM_NUMBER', '')
            }
            
            if not sms_config['account_sid']:
                logger.warning("SMS configuration not available")
                return False
            
            # Simulated SMS sending (replace with actual Twilio implementation)
            logger.info(f"SMS would be sent to {phone_number}: {message}")
            
            # Store SMS in local file for testing
            sms_dir = Path("data/sms_logs")
            sms_dir.mkdir(exist_ok=True)
            
            sms_log = {
                "timestamp": asyncio.get_event_loop().time(),
                "phone_number": phone_number,
                "message": message,
                "status": "sent"
            }
            
            sms_file = sms_dir / f"sms_log_{datetime.now().strftime('%Y%m%d')}.json"
            
            sms_logs = []
            if sms_file.exists():
                with open(sms_file, 'r') as f:
                    sms_logs = json.load(f)
            
            sms_logs.append(sms_log)
            
            with open(sms_file, 'w') as f:
                json.dump(sms_logs, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
            return False
    
    async def send_whatsapp_notification(self, whatsapp_number: str, message: str):
        """Send WhatsApp notification using WhatsApp Business API"""
        try:
            # This is a placeholder for WhatsApp implementation
            # You would integrate with WhatsApp Business API, Twilio WhatsApp, or similar
            # WhatsApp Business API integration
                        
            whatsapp_config = {
                'api_key': os.getenv('WHATSAPP_API_KEY', ''),
                'phone_id': os.getenv('WHATSAPP_PHONE_ID', ''),
                'access_token': os.getenv('WHATSAPP_ACCESS_TOKEN', '')
            }
            
            if not whatsapp_config['api_key']:
                logger.warning("WhatsApp configuration not available")
                return False
            
            # Simulated WhatsApp sending (replace with actual WhatsApp Business API)
            logger.info(f"WhatsApp would be sent to {whatsapp_number}: {message}")
            
            # Store WhatsApp message in local file for testing
            whatsapp_dir = Path("data/whatsapp_logs")
            whatsapp_dir.mkdir(exist_ok=True)
            
            whatsapp_log = {
                "timestamp": asyncio.get_event_loop().time(),
                "whatsapp_number": whatsapp_number,
                "message": message,
                "status": "sent"
            }
            
            whatsapp_file = whatsapp_dir / f"whatsapp_log_{datetime.now().strftime('%Y%m%d')}.json"
            
            whatsapp_logs = []
            if whatsapp_file.exists():
                with open(whatsapp_file, 'r') as f:
                    whatsapp_logs = json.load(f)
            
            whatsapp_logs.append(whatsapp_log)
            
            with open(whatsapp_file, 'w') as f:
                json.dump(whatsapp_logs, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending WhatsApp notification: {str(e)}")
            return False
    
    async def get_patient_notifications(self, patient_name: str, unread_only: bool = False) -> List[Dict]:
        """Get stored notifications for a patient"""
        try:
            notifications_dir = Path("data/notifications")
            patient_file = notifications_dir / f"{patient_name.replace(' ', '_')}_notifications.json"
            
            if not patient_file.exists():
                return []
            
            with open(patient_file, 'r') as f:
                notifications = json.load(f)
            
            if unread_only:
                notifications = [n for n in notifications if not n.get('read', False)]
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting patient notifications: {str(e)}")
            return []
    
    async def mark_notification_read(self, patient_name: str, notification_id: str):
        """Mark a notification as read"""
        try:
            notifications_dir = Path("data/notifications")
            patient_file = notifications_dir / f"{patient_name.replace(' ', '_')}_notifications.json"
            
            if not patient_file.exists():
                return False
            
            with open(patient_file, 'r') as f:
                notifications = json.load(f)
            
            # Find and mark notification as read
            for notification in notifications:
                if notification.get('id') == notification_id:
                    notification['read'] = True
                    break
            
            with open(patient_file, 'w') as f:
                json.dump(notifications, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error marking notification as read: {str(e)}")
            return False
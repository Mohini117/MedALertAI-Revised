# services/voice_agent.py
import asyncio
import logging
import edge_tts
import io
import json
from typing import Dict, Any
from pathlib import Path
import base64
import os
from datetime import datetime
import aiofiles

logger = logging.getLogger(__name__)

class VoiceAgent:
    def __init__(self):
        self.default_voice = "en-US-JennyNeural"  # Friendly female voice
        self.voice_rate = "+0%"  # Normal speed
        self.voice_pitch = "+0Hz"  # Normal pitch
        self.voice_templates = self._load_voice_templates()
        
    def _load_voice_templates(self) -> Dict[str, str]:
        """Load voice message templates"""
        return {
            "medicine_reminder": (
                "Hello {patient_name}! This is your MediScan AI assistant. "
                "It's time to take your {medicine_name}. Please remember to take {dosage}. "
                "Taking your medication on time is important for your health. "
                "Have a wonderful day!"
            ),
            "missed_medicine": (
                "Hi {patient_name}, I noticed you might have missed your {medicine_name} "
                "that was scheduled for {timing}. If you haven't taken it yet, please do so now. "
                "If you've already taken it, please ignore this reminder."
            ),
            "daily_summary": (
                "Good morning {patient_name}! Here's your medication schedule for today: "
                "{medicine_list}. Remember to take each medication as prescribed. "
                "Have a healthy day ahead!"
            ),
            "prescription_uploaded": (
                "Hello {patient_name}! I've successfully processed your new prescription. "
                "I'll start sending you reminders for your medications. "
                "Your health is our priority!"
            )
        }
    
    async def send_voice_reminder(self, reminder):
        """Send voice reminder to patient"""
        try:
            # Generate voice message
            message_text = self._generate_reminder_text(reminder)
            
            # Convert text to speech using Edge TTS
            audio_data = await self._edge_tts(message_text)
            
            if audio_data:
                # Save audio file
                audio_file = await self._save_audio_file(audio_data, reminder.patient_name)
                
                # Send audio notification
                await self._send_audio_notification(audio_file, reminder.patient_name, message_text)
                
                logger.info(f"Voice reminder sent to {reminder.patient_name}")
                return True
            else:
                logger.error("Failed to generate voice audio")
                return False
                
        except Exception as e:
            logger.error(f"Error sending voice reminder: {str(e)}")
            return False
    
    def _generate_reminder_text(self, reminder) -> str:
        """Generate personalized reminder text"""
        template = self.voice_templates["medicine_reminder"]
        
        return template.format(
            patient_name=reminder.patient_name,
            medicine_name=reminder.medicine_name,
            dosage=reminder.dosage,
            timing=reminder.timing,
            medicine_type=reminder.medicine_type
        )
    
    async def _edge_tts(self, text: str) -> bytes:
        """Convert text to speech using Microsoft Edge TTS"""
        try:
            # Create TTS communication
            communicate = edge_tts.Communicate(text, self.default_voice)
            
            # Generate audio data
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            logger.info("Edge TTS conversion successful")
            return audio_data
            
        except Exception as e:
            logger.error(f"Edge TTS error: {str(e)}")
            return None
    
    async def _save_audio_file(self, audio_data: bytes, patient_name: str) -> str:
        """Save audio file to storage"""
        try:
            # Create audio directory
            audio_dir = Path("data/audio_reminders")
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{patient_name.replace(' ', '_')}_{timestamp}.mp3"
            audio_path = audio_dir / filename
            
            # Save audio file asynchronously
            async with aiofiles.open(audio_path, 'wb') as f:
                await f.write(audio_data)
            
            logger.info(f"Audio file saved: {audio_path}")
            return str(audio_path)
            
        except Exception as e:
            logger.error(f"Error saving audio file: {str(e)}")
            return None
    
    async def _send_audio_notification(self, audio_file: str, patient_name: str, message_text: str):
        """Send audio notification to patient's device"""
        try:
            # Convert audio to base64 for web transmission
            audio_base64 = await self._audio_to_base64(audio_file)
            
            notification_data = {
                "audio_file": audio_file,
                "audio_base64": audio_base64,
                "message_text": message_text,
                "type": "voice_reminder",
                "patient_name": patient_name,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send via notification sender
            from services.notification_sender import NotificationSender, NotificationData
            sender = NotificationSender()
            
            await sender.send_web_notification(
                NotificationData(
                    title="🎵 Voice Reminder",
                    body=f"Voice message: It's time for your medication!",
                    patient_name=patient_name,
                    notification_type="voice_reminder",
                    data=notification_data
                )
            )
            
            logger.info(f"Audio notification sent for {patient_name}")
            
        except Exception as e:
            logger.error(f"Error sending audio notification: {str(e)}")
    
    async def _audio_to_base64(self, audio_file: str) -> str:
        """Convert audio file to base64 for web transmission"""
        try:
            async with aiofiles.open(audio_file, 'rb') as f:
                audio_data = await f.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                return audio_base64
        except Exception as e:
            logger.error(f"Error converting audio to base64: {str(e)}")
            return None
    
    async def generate_daily_summary(self, patient_name: str, medicines: list) -> str:
        """Generate daily medication summary audio"""
        try:
            # Create medicine list text
            medicine_list = []
            for medicine in medicines:
                timing_text = ", ".join(medicine.get('Timings', []))
                medicine_list.append(
                    f"{medicine.get('Medicine', 'Unknown')} at {timing_text}"
                )
            
            medicine_text = ". ".join(medicine_list)
            
            message_text = self.voice_templates["daily_summary"].format(
                patient_name=patient_name,
                medicine_list=medicine_text
            )
            
            # Generate audio
            audio_data = await self._edge_tts(message_text)
            
            if audio_data:
                audio_file = await self._save_audio_file(audio_data, f"{patient_name}_daily_summary")
                await self._send_audio_notification(audio_file, patient_name, message_text)
                return audio_file
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating daily summary: {str(e)}")
            return None
    
    async def send_prescription_confirmation(self, patient_name: str):
        """Send voice confirmation for new prescription"""
        try:
            message_text = self.voice_templates["prescription_uploaded"].format(
                patient_name=patient_name
            )
            
            audio_data = await self._edge_tts(message_text)
            
            if audio_data:
                audio_file = await self._save_audio_file(audio_data, f"{patient_name}_prescription_confirmation")
                await self._send_audio_notification(audio_file, patient_name, message_text)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending prescription confirmation: {str(e)}")
            return False
    
    async def get_available_voices(self) -> list:
        """Get list of available Edge TTS voices"""
        try:
            voices = await edge_tts.list_voices()
            return [
                {
                    "name": voice["Name"],
                    "short_name": voice["ShortName"],
                    "gender": voice["Gender"],
                    "locale": voice["Locale"]
                }
                for voice in voices
            ]
        except Exception as e:
            logger.error(f"Error getting available voices: {str(e)}")
            return []
    
    def set_voice(self, voice_name: str):
        """Set the TTS voice to use"""
        self.default_voice = voice_name
        logger.info(f"Voice set to: {voice_name}")
    
    def set_speech_rate(self, rate: str):
        """Set speech rate (+50%, -20%, etc.)"""
        self.voice_rate = rate
        logger.info(f"Speech rate set to: {rate}")
    
    def add_voice_template(self, template_name: str, template_text: str):
        """Add custom voice message template"""
        self.voice_templates[template_name] = template_text
        logger.info(f"Added voice template: {template_name}")
        
    async def test_voice_system(self, patient_name: str = "Test User") -> bool:
        """Test the voice system"""
        try:
            test_message = f"Hello {patient_name}! This is a test of your MediScan AI voice notification system. Everything is working perfectly!"
            
            audio_data = await self._edge_tts(test_message)
            
            if audio_data:
                audio_file = await self._save_audio_file(audio_data, f"{patient_name}_test")
                await self._send_audio_notification(audio_file, patient_name, test_message)
                logger.info("Voice system test successful")
                return True
            else:
                logger.error("Voice system test failed")
                return False
                
        except Exception as e:
            logger.error(f"Voice system test error: {str(e)}")
            return False 
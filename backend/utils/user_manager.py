# utils/user_manager.py
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Default user preferences
DEFAULT_PREFERENCES = {
    'notification_sound': 'default',
    'reminder_frequency': 'daily',
    'voice_enabled': True,
    'push_notifications': True,
    'email_notifications': False,
    'sms_notifications': False,
    'whatsapp_notifications': False,
    'email': '',
    'phone': '',
    'whatsapp': ''
}

# Default user profile
DEFAULT_PROFILE = {
    'name': '',
    'age': None,
    'medical_conditions': [],
    'allergies': [],
    'emergency_contact': ''
}

def ensure_user_directories():
    """Ensure user data directories exist"""
    user_data_dir = Path("data/users")
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    preferences_dir = user_data_dir / "preferences"
    preferences_dir.mkdir(exist_ok=True)
    
    profiles_dir = user_data_dir / "profiles"
    profiles_dir.mkdir(exist_ok=True)
    
    device_tokens_dir = user_data_dir / "device_tokens"
    device_tokens_dir.mkdir(exist_ok=True)
    
    return user_data_dir, preferences_dir, profiles_dir, device_tokens_dir

def sanitize_filename(name: str) -> str:
    """Sanitize patient name for use as filename"""
    return name.replace(' ', '_').replace('/', '_').replace('\\', '_').lower()

async def get_user_preferences(patient_name: str) -> Dict[str, Any]:
    """Get user preferences from storage"""
    try:
        _, preferences_dir, _, _ = ensure_user_directories()
        
        filename = sanitize_filename(patient_name)
        preferences_file = preferences_dir / f"{filename}_preferences.json"
        
        if preferences_file.exists():
            with open(preferences_file, 'r') as f:
                stored_preferences = json.load(f)
                
            # Merge with defaults to ensure all keys exist
            preferences = DEFAULT_PREFERENCES.copy()
            preferences.update(stored_preferences)
            return preferences
        else:
            # Return default preferences for new users
            return DEFAULT_PREFERENCES.copy()
            
    except Exception as e:
        logger.error(f"Error getting user preferences for {patient_name}: {str(e)}")
        return DEFAULT_PREFERENCES.copy()

async def update_user_preferences(patient_name: str, preferences: Dict[str, Any]) -> bool:
    """Update user preferences in storage"""
    try:
        _, preferences_dir, _, _ = ensure_user_directories()
        
        filename = sanitize_filename(patient_name)
        preferences_file = preferences_dir / f"{filename}_preferences.json"
        
        # Get existing preferences and merge with new ones
        existing_preferences = await get_user_preferences(patient_name)
        existing_preferences.update(preferences)
        existing_preferences['updated_at'] = datetime.now().isoformat()
        
        # Save updated preferences
        with open(preferences_file, 'w') as f:
            json.dump(existing_preferences, f, indent=2)
            
        logger.info(f"Updated preferences for {patient_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating user preferences for {patient_name}: {str(e)}")
        return False

async def get_user_profile(patient_name: str) -> Dict[str, Any]:
    """Get user profile from storage"""
    try:
        _, _, profiles_dir, _ = ensure_user_directories()
        
        filename = sanitize_filename(patient_name)
        profile_file = profiles_dir / f"{filename}_profile.json"
        
        if profile_file.exists():
            with open(profile_file, 'r') as f:
                stored_profile = json.load(f)
                
            # Merge with defaults
            profile = DEFAULT_PROFILE.copy()
            profile.update(stored_profile)
            profile['name'] = patient_name  # Ensure name is correct
            return profile
        else:
            # Return default profile with patient name
            profile = DEFAULT_PROFILE.copy()
            profile['name'] = patient_name
            return profile
            
    except Exception as e:
        logger.error(f"Error getting user profile for {patient_name}: {str(e)}")
        profile = DEFAULT_PROFILE.copy()
        profile['name'] = patient_name
        return profile

async def update_user_profile(patient_name: str, profile: Dict[str, Any]) -> bool:
    """Update user profile in storage"""
    try:
        _, _, profiles_dir, _ = ensure_user_directories()
        
        filename = sanitize_filename(patient_name)
        profile_file = profiles_dir / f"{filename}_profile.json"
        
        # Get existing profile and merge with new data
        existing_profile = await get_user_profile(patient_name)
        existing_profile.update(profile)
        existing_profile['name'] = patient_name  # Ensure name is preserved
        existing_profile['updated_at'] = datetime.now().isoformat()
        
        # Save updated profile
        with open(profile_file, 'w') as f:
            json.dump(existing_profile, f, indent=2)
            
        logger.info(f"Updated profile for {patient_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating user profile for {patient_name}: {str(e)}")
        return False

async def add_device_token(patient_name: str, token: str) -> bool:
    """Add device token for push notifications"""
    try:
        _, _, _, device_tokens_dir = ensure_user_directories()
        
        filename = sanitize_filename(patient_name)
        tokens_file = device_tokens_dir / f"{filename}_tokens.json"
        
        # Load existing tokens
        tokens = []
        if tokens_file.exists():
            with open(tokens_file, 'r') as f:
                tokens = json.load(f)
        
        # Add new token if not already present
        if token not in tokens:
            tokens.append(token)
            
            # Save updated tokens
            with open(tokens_file, 'w') as f:
                json.dump(tokens, f, indent=2)
                
            logger.info(f"Added device token for {patient_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error adding device token for {patient_name}: {str(e)}")
        return False

async def remove_device_token(patient_name: str, token: str) -> bool:
    """Remove device token"""
    try:
        _, _, _, device_tokens_dir = ensure_user_directories()
        
        filename = sanitize_filename(patient_name)
        tokens_file = device_tokens_dir / f"{filename}_tokens.json"
        
        if tokens_file.exists():
            with open(tokens_file, 'r') as f:
                tokens = json.load(f)
            
            # Remove token if present
            if token in tokens:
                tokens.remove(token)
                
                # Save updated tokens
                with open(tokens_file, 'w') as f:
                    json.dump(tokens, f, indent=2)
                    
                logger.info(f"Removed device token for {patient_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error removing device token for {patient_name}: {str(e)}")
        return False

async def get_user_device_tokens(patient_name: str) -> List[str]:
    """Get all device tokens for a user"""
    try:
        _, _, _, device_tokens_dir = ensure_user_directories()
        
        filename = sanitize_filename(patient_name)
        tokens_file = device_tokens_dir / f"{filename}_tokens.json"
        
        if tokens_file.exists():
            with open(tokens_file, 'r') as f:
                tokens = json.load(f)
            return tokens
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting device tokens for {patient_name}: {str(e)}")
        return []

async def get_all_users() -> List[Dict[str, Any]]:
    """Get list of all users with their basic info"""
    try:
        _, preferences_dir, profiles_dir, _ = ensure_user_directories()
        
        users = []
        
        # Get all preference files
        for pref_file in preferences_dir.glob("*_preferences.json"):
            try:
                # Extract patient name from filename
                filename = pref_file.stem.replace('_preferences', '')
                patient_name = filename.replace('_', ' ').title()
                
                # Get basic user info
                preferences = await get_user_preferences(patient_name)
                profile = await get_user_profile(patient_name)
                device_tokens = await get_user_device_tokens(patient_name)
                
                user_info = {
                    'name': patient_name,
                    'email': preferences.get('email', ''),
                    'phone': preferences.get('phone', ''),
                    'age': profile.get('age'),
                    'notifications_enabled': preferences.get('push_notifications', True),
                    'device_count': len(device_tokens),
                    'last_updated': preferences.get('updated_at', 'Never')
                }
                
                users.append(user_info)
                
            except Exception as e:
                logger.error(f"Error processing user file {pref_file}: {str(e)}")
                continue
        
        return users
        
    except Exception as e:
        logger.error(f"Error getting all users: {str(e)}")
        return []

async def delete_user_data(patient_name: str) -> bool:
    """Delete all data for a user"""
    try:
        _, preferences_dir, profiles_dir, device_tokens_dir = ensure_user_directories()
        
        filename = sanitize_filename(patient_name)
        
        # Files to delete
        files_to_delete = [
            preferences_dir / f"{filename}_preferences.json",
            profiles_dir / f"{filename}_profile.json",
            device_tokens_dir / f"{filename}_tokens.json"
        ]
        
        # Delete user files
        deleted_count = 0
        for file_path in files_to_delete:
            if file_path.exists():
                file_path.unlink()
                deleted_count += 1
        
        # Also delete notification history and reminder history
        history_dir = Path("data/reminder_history")
        if history_dir.exists():
            history_file = history_dir / f"{filename}_history.json"
            if history_file.exists():
                history_file.unlink()
                deleted_count += 1
        
        notifications_dir = Path("data/notifications")
        if notifications_dir.exists():
            notifications_file = notifications_dir / f"{filename}_notifications.json"
            if notifications_file.exists():
                notifications_file.unlink()
                deleted_count += 1
        
        logger.info(f"Deleted {deleted_count} files for user {patient_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting user data for {patient_name}: {str(e)}")
        return False

async def backup_user_data(patient_name: str) -> Optional[Dict[str, Any]]:
    """Create a backup of all user data"""
    try:
        backup_data = {
            'patient_name': patient_name,
            'backup_timestamp': datetime.now().isoformat(),
            'preferences': await get_user_preferences(patient_name),
            'profile': await get_user_profile(patient_name),
            'device_tokens': await get_user_device_tokens(patient_name)
        }
        
        # Create backup directory
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Save backup
        filename = sanitize_filename(patient_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{filename}_backup_{timestamp}.json"
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"Created backup for {patient_name}")
        return backup_data
        
    except Exception as e:
        logger.error(f"Error creating backup for {patient_name}: {str(e)}")
        return None

async def restore_user_data(backup_data: Dict[str, Any]) -> bool:
    """Restore user data from backup"""
    try:
        patient_name = backup_data.get('patient_name')
        if not patient_name:
            raise ValueError("Invalid backup data: missing patient_name")
        
        # Restore preferences
        if 'preferences' in backup_data:
            await update_user_preferences(patient_name, backup_data['preferences'])
        
        # Restore profile
        if 'profile' in backup_data:
            await update_user_profile(patient_name, backup_data['profile'])
        
        # Restore device tokens
        if 'device_tokens' in backup_data:
            for token in backup_data['device_tokens']:
                await add_device_token(patient_name, token)
        
        logger.info(f"Restored data for {patient_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error restoring user data: {str(e)}")
        return False

async def validate_user_preferences(preferences: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize user preferences"""
    try:
        validated = DEFAULT_PREFERENCES.copy()
        
        # Validate notification settings
        for key in ['voice_enabled', 'push_notifications', 'email_notifications', 
                   'sms_notifications', 'whatsapp_notifications']:
            if key in preferences:
                validated[key] = bool(preferences[key])
        
        # Validate string fields
        for key in ['notification_sound', 'reminder_frequency', 'email', 'phone', 'whatsapp']:
            if key in preferences and isinstance(preferences[key], str):
                validated[key] = preferences[key].strip()
        
        # Validate email format (basic validation)
        if validated['email']:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, validated['email']):
                logger.warning(f"Invalid email format: {validated['email']}")
                validated['email'] = ''
        
        # Validate phone numbers (basic validation)
        for phone_field in ['phone', 'whatsapp']:
            if validated[phone_field]:
                # Remove non-digit characters except +
                phone = re.sub(r'[^\d+]', '', validated[phone_field])
                if phone and (phone.startswith('+') or phone.isdigit()):
                    validated[phone_field] = phone
                else:
                    logger.warning(f"Invalid phone format: {validated[phone_field]}")
                    validated[phone_field] = ''
        
        return validated
        
    except Exception as e:
        logger.error(f"Error validating preferences: {str(e)}")
        return DEFAULT_PREFERENCES.copy()

async def get_user_statistics() -> Dict[str, Any]:
    """Get statistics about all users"""
    try:
        users = await get_all_users()
        
        stats = {
            'total_users': len(users),
            'users_with_email': len([u for u in users if u.get('email')]),
            'users_with_phone': len([u for u in users if u.get('phone')]),
            'users_with_notifications': len([u for u in users if u.get('notifications_enabled')]),
            'total_devices': sum(u.get('device_count', 0) for u in users),
            'average_age': 0,
            'age_distribution': {'unknown': 0, 'under_30': 0, '30_50': 0, 'over_50': 0}
        }
        
        # Calculate age statistics
        ages = [u.get('age') for u in users if u.get('age') is not None]
        if ages:
            stats['average_age'] = round(sum(ages) / len(ages), 1)
            
            for age in ages:
                if age < 30:
                    stats['age_distribution']['under_30'] += 1
                elif age <= 50:
                    stats['age_distribution']['30_50'] += 1
                else:
                    stats['age_distribution']['over_50'] += 1
        
        stats['age_distribution']['unknown'] = len(users) - len(ages)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting user statistics: {str(e)}")
        return {'error': str(e)}

# Utility functions for data migration and cleanup
async def migrate_user_data():
    """Migrate user data to new format if needed"""
    try:
        # This function can be used for future data migrations
        logger.info("User data migration completed")
        return True
    except Exception as e:
        logger.error(f"Error during user data migration: {str(e)}")
        return False

async def cleanup_old_data(days_old: int = 90):
    """Clean up old backup files and logs"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleanup_count = 0
        
        # Clean up old backups
        backup_dir = Path("data/backups")
        if backup_dir.exists():
            for backup_file in backup_dir.glob("*_backup_*.json"):
                try:
                    # Extract timestamp from filename
                    timestamp_str = backup_file.stem.split('_backup_')[-1]
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if file_date < cutoff_date:
                        backup_file.unlink()
                        cleanup_count += 1
                except Exception:
                    continue
        
        logger.info(f"Cleaned up {cleanup_count} old backup files")
        return True
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return False 
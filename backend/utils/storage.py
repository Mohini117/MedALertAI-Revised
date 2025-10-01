# utils/storage.py
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_storage_directories():
    """Create necessary storage directories"""
    try:
        # Main data directories
        prescriptions_dir = Path("data/prescriptions")
        diagnostics_dir = Path("data/diagnostics")
        notifications_dir = Path("data/notifications")
        users_dir = Path("data/users")
        scheduled_reminders_dir = Path("data/scheduled_reminders")
        reminder_history_dir = Path("data/reminder_history")
        sms_logs_dir = Path("data/sms_logs")
        whatsapp_logs_dir = Path("data/whatsapp_logs")
        
        # Create directories if they don't exist
        directories = [
            prescriptions_dir, diagnostics_dir, notifications_dir,
            users_dir, scheduled_reminders_dir, reminder_history_dir,
            sms_logs_dir, whatsapp_logs_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("Storage directories created successfully")
        return prescriptions_dir, diagnostics_dir
        
    except Exception as e:
        logger.error(f"Error creating storage directories: {str(e)}")
        raise

def save_json_data(data: Dict[str, Any], directory: Path, prefix: str) -> str:
    """Save JSON data to file"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        filepath = directory / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {filepath}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error saving JSON data: {str(e)}")
        raise

def load_json_data(filepath: str) -> Optional[Dict[str, Any]]:
    """Load JSON data from file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON data from {filepath}: {str(e)}")
        return None

def get_all_prescriptions() -> List[Dict[str, Any]]:
    """Get all prescription files"""
    try:
        prescriptions_dir = Path("data/prescriptions")
        if not prescriptions_dir.exists():
            return []
        
        prescriptions = []
        for file_path in prescriptions_dir.glob("prescription_*.json"):
            data = load_json_data(str(file_path))
            if data:
                data['file_path'] = str(file_path)
                data['created_at'] = datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                prescriptions.append(data)
        
        # Sort by creation time (newest first)
        prescriptions.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return prescriptions
        
    except Exception as e:
        logger.error(f"Error getting all prescriptions: {str(e)}")
        return []

def get_all_diagnostics() -> List[Dict[str, Any]]:
    """Get all diagnostic files"""
    try:
        diagnostics_dir = Path("data/diagnostics")
        if not diagnostics_dir.exists():
            return []
        
        diagnostics = []
        for file_path in diagnostics_dir.glob("diagnostic_*.json"):
            data = load_json_data(str(file_path))
            if data:
                data['file_path'] = str(file_path)
                data['created_at'] = datetime.fromtimestamp(file_path.stat().st_ctime).isoformat()
                diagnostics.append(data)
        
        # Sort by creation time (newest first)
        diagnostics.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return diagnostics
        
    except Exception as e:
        logger.error(f"Error getting all diagnostics: {str(e)}")
        return []

def get_patient_prescriptions(patient_name: str) -> List[Dict[str, Any]]:
    """Get prescriptions for a specific patient"""
    try:
        all_prescriptions = get_all_prescriptions()
        patient_prescriptions = []
        
        for prescription in all_prescriptions:
            # Check if patient name matches
            patient_data = prescription.get('Patient', {})
            if isinstance(patient_data, dict):
                stored_name = patient_data.get('Name', '').lower().strip()
            else:
                stored_name = str(patient_data).lower().strip()
            
            if stored_name == patient_name.lower().strip():
                patient_prescriptions.append(prescription)
        
        return patient_prescriptions
        
    except Exception as e:
        logger.error(f"Error getting patient prescriptions: {str(e)}")
        return []

def get_patient_medicines_summary(patient_name: str) -> Dict[str, Any]:
    """Get a summary of all medicines for a patient"""
    try:
        patient_prescriptions = get_patient_prescriptions(patient_name)
        
        all_medicines = []
        total_prescriptions = len(patient_prescriptions)
        
        for prescription in patient_prescriptions:
            medicines = prescription.get('Medicines', [])
            for medicine in medicines:
                medicine_info = {
                    'medicine_name': medicine.get('Medicine', 'Unknown'),
                    'dosage': medicine.get('Dosage', 'Unknown'),
                    'timings': medicine.get('Timings', []),
                    'type': medicine.get('Type', 'Unknown'),
                    'prescription_date': prescription.get('Date', 'Unknown'),
                    'prescription_file': prescription.get('file_path', '')
                }
                all_medicines.append(medicine_info)
        
        return {
            'patient_name': patient_name,
            'total_prescriptions': total_prescriptions,
            'total_medicines': len(all_medicines),
            'medicines': all_medicines,
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting patient medicines summary: {str(e)}")
        return {}

def search_prescriptions(query: str, search_field: str = 'all') -> List[Dict[str, Any]]:
    """Search prescriptions by various fields"""
    try:
        all_prescriptions = get_all_prescriptions()
        results = []
        
        query_lower = query.lower().strip()
        
        for prescription in all_prescriptions:
            match_found = False
            
            # Search in patient name
            if search_field in ['all', 'patient']:
                patient_name = prescription.get('Patient', {}).get('Name', '').lower()
                if query_lower in patient_name:
                    match_found = True
            
            # Search in medicines
            if search_field in ['all', 'medicine'] and not match_found:
                medicines = prescription.get('Medicines', [])
                for medicine in medicines:
                    medicine_name = medicine.get('Medicine', '').lower()
                    if query_lower in medicine_name:
                        match_found = True
                        break
            
            # Search in date
            if search_field in ['all', 'date'] and not match_found:
                date = prescription.get('Date', '').lower()
                if query_lower in date:
                    match_found = True
            
            if match_found:
                results.append(prescription)
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching prescriptions: {str(e)}")
        return []

def get_system_statistics() -> Dict[str, Any]:
    """Get system statistics"""
    try:
        stats = {
            'total_prescriptions': len(get_all_prescriptions()),
            'total_diagnostics': len(get_all_diagnostics()),
            'total_patients': 0,
            'storage_usage': {},
            'last_updated': datetime.now().isoformat()
        }
        
        # Count unique patients
        all_prescriptions = get_all_prescriptions()
        unique_patients = set()
        for prescription in all_prescriptions:
            patient_name = prescription.get('Patient', {}).get('Name', '').strip()
            if patient_name:
                unique_patients.add(patient_name.lower())
        
        stats['total_patients'] = len(unique_patients)
        
        # Calculate storage usage
        data_dir = Path("data")
        if data_dir.exists():
            for subdir in data_dir.iterdir():
                if subdir.is_dir():
                    size = sum(f.stat().st_size for f in subdir.glob('**/*') if f.is_file())
                    stats['storage_usage'][subdir.name] = {
                        'size_bytes': size,
                        'size_mb': round(size / (1024 * 1024), 2),
                        'file_count': len(list(subdir.glob('**/*')))
                    }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting system statistics: {str(e)}")
        return {}

def backup_data(backup_name: str = None) -> str:
    """Create a backup of all data"""
    try:
        import shutil
        
        if not backup_name:
            backup_name = f"mediscan_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / backup_name
        data_dir = Path("data")
        
        if data_dir.exists():
            shutil.copytree(data_dir, backup_path)
            logger.info(f"Data backup created at {backup_path}")
            return str(backup_path)
        else:
            raise FileNotFoundError("Data directory not found")
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise

def restore_data(backup_path: str) -> bool:
    """Restore data from backup"""
    try:
        import shutil
        
        backup_dir = Path(backup_path)
        data_dir = Path("data")
        
        if not backup_dir.exists():
            raise FileNotFoundError(f"Backup directory not found: {backup_path}")
        
        # Create backup of current data
        if data_dir.exists():
            current_backup = f"data_backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.move(str(data_dir), f"backups/{current_backup}")
            logger.info(f"Current data backed up to backups/{current_backup}")
        
        # Restore from backup
        shutil.copytree(backup_dir, data_dir)
        logger.info(f"Data restored from {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error restoring data: {str(e)}")
        return False

def delete_file(filepath: str) -> bool:
    """Delete a file"""
    try:
        file_path = Path(filepath)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"File deleted: {filepath}")
            return True
        else:
            logger.warning(f"File not found: {filepath}")
            return False
    except Exception as e:
        logger.error(f"Error deleting file {filepath}: {str(e)}")
        return False

def cleanup_old_files(directory: Path, days: int = 30):
    """Clean up files older than specified days"""
    try:
        import time
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        deleted_count = 0
        for file_path in directory.glob("**/*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old files from {directory}")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error cleaning up old files: {str(e)}")
        return 0

def get_recent_activity(days: int = 7) -> Dict[str, Any]:
    """Get recent activity summary"""
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Recent prescriptions
        recent_prescriptions = []
        all_prescriptions = get_all_prescriptions()
        
        for prescription in all_prescriptions:
            created_at = prescription.get('created_at')
            if created_at:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00') if created_at.endswith('Z') else created_at)
                if created_date > cutoff_date:
                    recent_prescriptions.append(prescription)
        
        # Recent diagnostics
        recent_diagnostics = []
        all_diagnostics = get_all_diagnostics()
        
        for diagnostic in all_diagnostics:
            created_at = diagnostic.get('created_at')
            if created_at:
                created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00') if created_at.endswith('Z') else created_at)
                if created_date > cutoff_date:
                    recent_diagnostics.append(diagnostic)
        
        return {
            'period_days': days,
            'recent_prescriptions': recent_prescriptions,
            'recent_diagnostics': recent_diagnostics,
            'prescription_count': len(recent_prescriptions),
            'diagnostic_count': len(recent_diagnostics),
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        return {}  
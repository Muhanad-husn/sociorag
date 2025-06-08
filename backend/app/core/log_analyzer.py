"""Log analysis utilities for SocioRAG."""
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from .config import get_config


class LogAnalyzer:
    """Analyze application logs for insights and troubleshooting."""
    
    def __init__(self):
        self.config = get_config()
        self.logs_dir = self.config.BASE_DIR / "logs"
    def get_log_files(self) -> List[Path]:
        """Get all log files."""
        if not self.logs_dir.exists():
            return []
        
        # Return only the primary log files, not backup/rotated files
        return [p for p in self.logs_dir.glob("*.log") if not re.search(r'\.\d+$', p.name)]
    
    def parse_structured_logs(self, hours_back: int = 24) -> List[Dict]:
        """Parse structured JSON logs."""
        structured_log = self.logs_dir / "sociorag_structured.log"
        if not structured_log.exists():
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        logs = []
        
        try:
            with open(structured_log, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if 'timestamp' in entry:
                            timestamp = datetime.fromisoformat(entry['timestamp'])
                            if timestamp >= cutoff_time:
                                logs.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except FileNotFoundError:
            pass
        
        return logs
    
    def get_error_summary(self, hours_back: int = 24) -> Dict:
        """Get summary of errors in the specified time period."""
        logs = self.parse_structured_logs(hours_back)
        errors = [log for log in logs if log.get('level') in ['ERROR', 'CRITICAL']]
        
        error_counts = Counter()
        error_details = defaultdict(list)
        
        for error in errors:
            error_type = error.get('error_type', 'Unknown')
            error_counts[error_type] += 1
            error_details[error_type].append({
                'timestamp': error['timestamp'],
                'message': error['message'],
                'correlation_id': error.get('correlation_id'),
                'module': error.get('module')
            })
        
        return {
            'total_errors': len(errors),
            'error_counts': dict(error_counts),
            'error_details': dict(error_details)
        }
    
    def get_performance_summary(self, hours_back: int = 24) -> Dict:
        """Get performance metrics summary."""
        logs = self.parse_structured_logs(hours_back)
        
        # API performance
        api_logs = [log for log in logs if log.get('request_type') == 'api']
        operation_logs = [log for log in logs if log.get('operation_phase') == 'end']
        
        api_performance = defaultdict(list)
        operation_performance = defaultdict(list)
        
        for log in api_logs:
            endpoint = log.get('endpoint', 'unknown')
            duration = log.get('duration_seconds', 0)
            api_performance[endpoint].append(duration)
        
        for log in operation_logs:
            operation = log.get('operation', 'unknown')
            duration = log.get('duration_seconds', 0)
            operation_performance[operation].append(duration)
        
        # Calculate stats
        def calculate_stats(durations):
            if not durations:
                return {}
            return {
                'count': len(durations),
                'avg': sum(durations) / len(durations),
                'min': min(durations),
                'max': max(durations),
                'p95': sorted(durations)[int(len(durations) * 0.95)] if durations else 0
            }
        
        return {
            'api_performance': {
                endpoint: calculate_stats(durations)
                for endpoint, durations in api_performance.items()
            },
            'operation_performance': {
                operation: calculate_stats(durations)
                for operation, durations in operation_performance.items()
            }
        }
    
    def get_user_activity(self, hours_back: int = 24) -> Dict:
        """Get user activity summary."""
        logs = self.parse_structured_logs(hours_back)
        
        user_actions = defaultdict(list)
        api_requests = defaultdict(int)
        
        for log in logs:
            if log.get('action_type') == 'user':
                user_id = log.get('user_id', 'anonymous')
                user_actions[user_id].append({
                    'timestamp': log['timestamp'],
                    'action': log.get('action'),
                    'correlation_id': log.get('correlation_id')
                })
            
            if log.get('request_type') == 'api':
                user_id = log.get('user_id', 'anonymous')
                api_requests[user_id] += 1
        
        return {
            'user_actions': dict(user_actions),
            'api_requests_by_user': dict(api_requests),
            'total_users': len(set(list(user_actions.keys()) + list(api_requests.keys())))
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status and warnings."""
        health = {
            "status": "healthy",
            "uptime": "unknown",
            "error_rate": 0.0,
            "average_response_time": 0.0,
            "active_operations": 0,
            "warnings": []
        }
        
        try:
            # Calculate uptime from oldest log entry
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            # Get recent errors to calculate error rate
            recent_errors = self._get_recent_entries(
                level="ERROR", 
                since=one_hour_ago,
                limit=1000
            )
            
            # Calculate error rate (errors per minute)
            if recent_errors:
                time_span_minutes = 60  # 1 hour
                health["error_rate"] = len(recent_errors) / time_span_minutes
                
                # Add warning if error rate is high
                if health["error_rate"] > 1.0:
                    health["warnings"].append(f"High error rate: {health['error_rate']:.1f} errors/min")
                    health["status"] = "warning"
                    
                if health["error_rate"] > 5.0:
                    health["status"] = "critical"
            
        except Exception as e:
            from .singletons import get_logger
            logger = get_logger()
            logger.error(f"Error checking system health: {e}")
            health["status"] = "unknown"
            health["warnings"].append(f"Health check failed: {str(e)}")
            
        return health
    
    def _get_recent_entries(self, level: str, since: datetime, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent log entries by level."""
        entries = []
        
        try:
            for log_file in self.get_log_files():
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if len(entries) >= limit:
                            break
                            
                        try:
                            if line.strip().startswith('{'):
                                entry = json.loads(line.strip())
                                entry_time = datetime.fromisoformat(entry.get('timestamp', ''))
                                entry_level = entry.get('level', '')
                            else:
                                entry_time = self._extract_timestamp(line)
                                entry_level = self._extract_level(line)
                                entry = {
                                    'timestamp': entry_time.isoformat() if entry_time else '',
                                    'level': entry_level,
                                    'message': line.strip()
                                }
                            
                            if (entry_time and entry_time >= since and 
                                entry_level.upper() == level.upper()):
                                entries.append(entry)
                                
                        except (json.JSONDecodeError, ValueError, TypeError):
                            continue
                            
        except Exception as e:
            from .singletons import get_logger
            logger = get_logger()
            logger.warning(f"Error getting recent entries: {e}")
            
        return sorted(entries, key=lambda x: x.get('timestamp', ''), reverse=True)
    
    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from a plain text log line."""
        # Look for ISO format timestamps
        iso_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        match = re.search(iso_pattern, line)
        if match:
            try:
                return datetime.fromisoformat(match.group())
            except ValueError:
                pass
        
        # Look for common log format timestamps
        timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}'
        match = re.search(timestamp_pattern, line)
        if match:
            try:
                return datetime.strptime(match.group(), '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
                
        return None

    def _extract_level(self, line: str) -> str:
        """Extract log level from a plain text log line."""
        for level in ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']:
            if level in line.upper():
                return level
        return 'UNKNOWN'
    
    def export_report(self, output_file: Optional[Path] = None, hours_back: int = 24) -> str:
        """Export a comprehensive log analysis report."""
        if output_file is None:
            output_file = self.logs_dir / f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'time_period_hours': hours_back,
            'system_health': self.get_system_health(),
            'error_summary': self.get_error_summary(hours_back),
            'performance_summary': self.get_performance_summary(hours_back),
            'user_activity': self.get_user_activity(hours_back)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        return str(output_file)
    def search_logs(self, query: str, since: datetime, level: Optional[str] = None, 
                   operation: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Search through log entries with various filters."""
        hours_back = int((datetime.now() - since).total_seconds() / 3600)
        logs = self.parse_structured_logs(hours_back)
        
        results = []
        query_lower = query.lower()
        
        for log in logs:
            # Check query match
            message = log.get('message', '').lower()
            if query_lower not in message:
                continue
            
            # Check level filter
            if level and log.get('level', '').lower() != level.lower():
                continue
            
            # Check operation filter
            if operation and log.get('operation', '') != operation:
                continue
            
            results.append(log)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_correlation_trace(self, correlation_id: str) -> List[Dict]:
        """Get all log entries for a specific correlation ID."""
        # Search through all available logs for the correlation ID
        logs = self.parse_structured_logs(hours_back=168)  # Search last week
        
        trace = []
        for log in logs:
            if log.get('correlation_id') == correlation_id:
                trace.append(log)
        
        # Sort by timestamp
        trace.sort(key=lambda x: x.get('timestamp', ''))
        return trace
    
    def cleanup_old_logs(self, cutoff_date: datetime) -> Dict:
        """Clean up old log files to manage disk space."""
        log_files = self.get_log_files()
        files_processed = 0
        space_freed = 0
        
        for log_file in log_files:
            if log_file.exists():
                # Check file modification time
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    try:
                        file_size = log_file.stat().st_size
                        log_file.unlink()  # Delete the file
                        files_processed += 1
                        space_freed += file_size
                    except Exception:
                        # Skip files that can't be deleted
                        continue
        
        return {
            'files_processed': files_processed,
            'space_freed': space_freed
        }
    
    def get_log_statistics(self) -> Dict:
        """Get general statistics about the logging system."""
        config = get_config()
        log_files = self.get_log_files()
        
        total_size = 0
        file_stats = []
        
        for log_file in log_files:
            if log_file.exists():
                size = log_file.stat().st_size
                total_size += size
                file_stats.append({
                    'name': log_file.name,
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
          # Get recent activity stats
        recent_logs = self.parse_structured_logs(hours_back=24)
        log_levels = {}
        for log in recent_logs:
            level = log.get('level', 'UNKNOWN')
            log_levels[level] = log_levels.get(level, 0) + 1
        
        return {
            'total_log_files': len(file_stats),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_details': file_stats,
            'recent_activity_24h': {
                'total_entries': len(recent_logs),
                'by_level': log_levels
            },
            'configuration': {
                'enhanced_logging_enabled': config.ENHANCED_LOGGING_ENABLED,
                'structured_format': config.LOG_STRUCTURED_FORMAT,
                'correlation_enabled': config.LOG_CORRELATION_ENABLED,
                'performance_tracking': config.LOG_PERFORMANCE_TRACKING,
                'max_file_size_mb': config.LOG_MAX_FILE_SIZE_MB,
                'retention_days': config.LOG_FILE_RETENTION_DAYS
            }
        }

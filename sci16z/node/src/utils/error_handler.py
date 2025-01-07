from typing import Optional, Dict, Any
from utils.logger import get_logger

class ErrorHandler:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.error_codes = {
            # System errors
            'SYS_001': 'System initialization failed',
            'SYS_002': 'Configuration error',
            'SYS_003': 'Resource allocation failed',
            
            # Network errors
            'NET_001': 'Connection failed',
            'NET_002': 'Authentication failed',
            'NET_003': 'Request timeout',
            'NET_004': 'Invalid response',
            
            # Model errors
            'MDL_001': 'Model loading failed',
            'MDL_002': 'Inference error',
            'MDL_003': 'GPU memory error',
            
            # Task errors
            'TSK_001': 'Task validation failed',
            'TSK_002': 'Task processing failed',
            'TSK_003': 'Result submission failed',
            
            # Security errors
            'SEC_001': 'TEE initialization failed',
            'SEC_002': 'Integrity check failed',
            'SEC_003': 'Signature verification failed'
        }

    def handle_error(self, error_code: str, error: Exception) -> Dict[str, Any]:
        """Handle and format error"""
        try:
            error_info = {
                'code': error_code,
                'message': self.error_codes.get(error_code, 'Unknown error'),
                'details': str(error),
                'type': error.__class__.__name__
            }
            
            # Log error
            self.logger.error(
                f"Error {error_code}: {error_info['message']} - {error_info['details']}"
            )
            
            return error_info
            
        except Exception as e:
            self.logger.error(f"Error handler failed: {str(e)}")
            return {
                'code': 'ERR_000',
                'message': 'Error handling failed',
                'details': str(e),
                'type': 'ErrorHandlerError'
            }

    def is_recoverable(self, error_code: str) -> bool:
        """Check if error is recoverable"""
        unrecoverable = [
            'SYS_001',  # System initialization
            'SEC_002',  # Integrity check
            'MDL_001'   # Model loading
        ]
        return error_code not in unrecoverable

    def get_retry_strategy(self, error_code: str) -> Optional[Dict[str, Any]]:
        """Get retry strategy for error"""
        strategies = {
            'NET_001': {
                'max_retries': 3,
                'delay': 5,
                'backoff': 2
            },
            'NET_003': {
                'max_retries': 2,
                'delay': 3,
                'backoff': 1.5
            },
            'TSK_003': {
                'max_retries': 2,
                'delay': 2,
                'backoff': 2
            }
        }
        return strategies.get(error_code)

    def format_user_message(self, error_info: Dict[str, Any]) -> str:
        """Format user-friendly error message"""
        messages = {
            'SYS_001': "System startup failed. Please check system requirements and try again.",
            'NET_001': "Connection failed. Please check your network connection.",
            'NET_002': "Authentication failed. Please check your credentials.",
            'MDL_001': "Model loading failed. Please check GPU memory and disk space.",
            'TSK_002': "Task processing failed. The system will retry automatically.",
            'SEC_002': "Security check failed. Please reinstall the application."
        }
        
        return messages.get(
            error_info['code'],
            f"An error occurred: {error_info['message']}"
        )

    def should_notify_admin(self, error_code: str) -> bool:
        """Check if error requires admin notification"""
        critical_errors = [
            'SYS_001',  # System initialization
            'SEC_002',  # Integrity check
            'SEC_003',  # Signature verification
            'MDL_001'   # Model loading
        ]
        return error_code in critical_errors 
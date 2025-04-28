# ========================================================
# Imports
# ========================================================
import logging
import os



# ========================================================
# Logging configuration
# ========================================================

# Create log directory if it doesn't exist
LOG_DIR = "/logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Path to the Error log file
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error.log")
ACCESS_LOG_FILE = os.path.join(LOG_DIR, "access.log")



# ========================================================
# Create formatter
# ========================================================
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")



# ========================================================
# Level filters
# ========================================================
class ErrorFilter(logging.Filter):
    """Allow only ERROR and CRITICAL levels."""
    def filter(self, record):
        return record.levelno >= logging.ERROR

class NonErrorFilter(logging.Filter):
    """Allow only levels below ERROR (INFO, DEBUG, WARNING)."""
    def filter(self, record):
        return record.levelno < logging.ERROR



# ========================================================
# Main application logger (general logs)
# ========================================================
logger = logging.getLogger("fastapi-backend")
logger.setLevel(logging.INFO)

# -------- Console Handler (non-error levels) --------
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.addFilter(NonErrorFilter())  # Only INFO/WARNING/DEBUG
logger.addHandler(console_handler)

# -------- File Handler (error levels) --------
error_file_handler = logging.FileHandler(ERROR_LOG_FILE)
error_file_handler.setFormatter(formatter)
error_file_handler.addFilter(ErrorFilter())  # Only ERROR/CRITICAL
logger.addHandler(error_file_handler)



# ========================================================
# Login attempts logger (login/logout logs)
# ========================================================

# Login attempts logger (file output)
login_logger = logging.getLogger("login-attempts")
login_logger.setLevel(logging.INFO)

# FileHandler (for file output)
file_handler = logging.FileHandler(ACCESS_LOG_FILE)
file_handler.setFormatter(formatter)
login_logger.addHandler(file_handler)

# StreamHandler (for console output)
console_handler_for_login = logging.StreamHandler()
console_handler_for_login.setFormatter(formatter)
login_logger.addHandler(console_handler_for_login)
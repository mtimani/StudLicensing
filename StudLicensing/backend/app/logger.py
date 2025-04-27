# ========================================================
# Imports
# ========================================================
import logging



# ========================================================
# Logging configuration
# ========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger("fastapi-backend")
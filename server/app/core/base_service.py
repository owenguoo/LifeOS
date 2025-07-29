from abc import ABC
from typing import Any, Dict
import logging
from .exceptions import LifeOSException
from .logging import log_error


class BaseService(ABC):
    def __init__(self, logger_name: str = None):
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)

    def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> None:
        log_error(error, context)
        if isinstance(error, LifeOSException):
            raise error
        raise LifeOSException(str(error))

    async def safe_execute(self, operation, context: Dict[str, Any] = None):
        try:
            return await operation()
        except Exception as e:
            self.handle_error(e, context)


class DatabaseService(BaseService):
    def __init__(self, connection, logger_name: str = None):
        super().__init__(logger_name)
        self.connection = connection

    async def health_check(self) -> bool:
        try:
            # Override in specific database services
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False


class ExternalAPIService(BaseService):
    def __init__(self, api_key: str, base_url: str, logger_name: str = None):
        super().__init__(logger_name)
        self.api_key = api_key
        self.base_url = base_url

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def health_check(self) -> bool:
        try:
            # Override in specific API services
            return True
        except Exception as e:
            self.logger.error(f"External API health check failed: {e}")
            return False

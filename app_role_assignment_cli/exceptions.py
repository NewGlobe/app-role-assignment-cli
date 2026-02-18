from .logging_settings import logging

logger = logging.getLogger(__name__)


class AppRoleAssignmentBaseException(Exception):
    def __init__(self, message, err_logger=logger):
        super().__init__(message)
        err_logger.error(message)

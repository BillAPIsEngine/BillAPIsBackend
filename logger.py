import logging
from logging.handlers import RotatingFileHandler
from .db import db, LogConfig
from sqlalchemy.orm import sessionmaker

# Function to set up logger dynamically
def setup_logger():
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Default log level

    # Fetch the logging configuration from the database
    log_config = LogConfig.query.first()

    if log_config:
        log_level = log_config.log_level.upper()
        logger.setLevel(getattr(logging, log_level, logging.DEBUG))

        if log_config.log_to_file:
            # File logging
            file_handler = RotatingFileHandler('system.log', maxBytes=100000, backupCount=3)
            file_handler.setLevel(getattr(logging, log_level, logging.DEBUG))
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        if log_config.log_to_db:
            # Database logging (custom handler)
            db_handler = DatabaseLogHandler()
            db_handler.setLevel(getattr(logging, log_level, logging.DEBUG))
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            db_handler.setFormatter(formatter)
            logger.addHandler(db_handler)

    return logger


class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = self.format(record)
            # Here you can add your database logging logic, inserting logs into a "logs" table
            # Example (you should define a log entry table for this purpose):
            from .db import LogEntry  # Define a model for log entries
            log_entry = LogEntry(message=log_entry)
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            print(f"Error saving log to DB: {e}")
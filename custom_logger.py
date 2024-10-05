import json
import yaml
import logging
from datetime import datetime
import sys

class StructuredLogger:
    def __init__(self, log_file):
        self.logger = logging.getLogger('StructuredLogger')
        self.logger.setLevel(logging.DEBUG)  # Capture all levels of messages

        # Remove all existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler for all levels
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Custom handler for ERROR and CRITICAL levels
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter('%(levelname)s: %(message)s')
        error_handler.setFormatter(error_formatter)
        self.logger.addHandler(error_handler)

        # Prevent propagation to root logger (which might log to stdout)
        self.logger.propagate = False

    def log(self, issuer, event_type, level, message):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": logging.getLevelName(level),
            "issuer": issuer,
            "event_type": event_type,
            "data": message
        }
        
        log_message = json.dumps(log_entry, indent=4)
        log_message = yaml.dump(log_entry, default_flow_style=False, sort_keys=False, indent=4)
        
        if level == logging.DEBUG:
            self.logger.debug(log_message)
        elif level == logging.INFO:
            self.logger.info(log_message)
        elif level == logging.WARNING:
            self.logger.warning(log_message)
        elif level == logging.ERROR:
            self.logger.error(log_message)
        elif level == logging.CRITICAL:
            self.logger.critical(log_message)
        else:
            self.logger.error(f"Unknown log level: {level}. Message: {log_message}")
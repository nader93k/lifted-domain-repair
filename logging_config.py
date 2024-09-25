import logging


def setup_logging(log_file):    
    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create file handler and set level to info
    file_handler = logging.FileHandler(log_file, mode='a')  # Changed to 'a' for append mode
    file_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter('%(message)s')

    # Add formatter to file handler
    file_handler.setFormatter(formatter)

    # Get the root logger and add the file handler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

    return root_logger

import logging
import sys

def configure_logging(config):
    root = logging.getLogger()
    print("Configuring logging")
    # Get log level with proper ConfigParser syntax and fallback
    try:
        log_level = config.get("logging", "log_level", fallback="INFO")
        level = getattr(logging, log_level.upper())
    except (AttributeError, ValueError):
        print(f'Logging level {log_level} not valid. Defaulting to INFO')
        level = logging.INFO

    root.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Always add console handler for Docker environments
    try:
        stdout_enabled = config.getboolean("logging", "stdout", fallback=True)
    except (ValueError, AttributeError):
        stdout_enabled = True

    if stdout_enabled:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    # Add file handler only if log_file is specified
    try:
        log_file = config.get("logging", "log_file", fallback=None)
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
    except Exception as e:
        print(f"Could not set up file logging: {e}")

    # Set up requests logging if requested
    try:
        if config.getboolean("logging", "log_requests", fallback=False):
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True
    except (ValueError, AttributeError):
        pass

    return root

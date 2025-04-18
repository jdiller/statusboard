import logging
import sys

def configure_logging(config: dict):
    root = logging.getLogger()
    log_level = config.get("logging", "log_level")
    if log_level:
        try:
            level = getattr(logging, log_level)
        except AttributeError:
            print (f'Logging level {log_level} not valid. Defaulting to WARN')
            level = logging.WARN
    root.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if config.getboolean("logging", "stdout"):
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    log_file = config.get("logging", "log_file")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    if config.getboolean("logging", "log_requests"):
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    return root

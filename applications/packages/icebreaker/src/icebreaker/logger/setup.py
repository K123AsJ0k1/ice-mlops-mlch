
def logger_setup_configuration(
    logger_name: str,
    logger_timezone: str
) -> any:
    try:
        import sys
        import logging
        import os
        from datetime import datetime
        from zoneinfo import ZoneInfo
    except ImportError as e:
        raise ImportError("logger/use failed to import", e)
    
    used_tz = None
    try:
        used_tz = ZoneInfo(logger_timezone)
    except Exception as e:
        raise ValueError(f"Invalid timezone provided: {logger_timezone}")
    
    main_script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(main_script_path)
    
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Format: run_YYYYMMDD_HHMMSS.log (e.g., run_20260603_071530.log)
    timestamp_index = datetime.now(used_tz).strftime("%Y%m%d_%H%M%S")
    log_filename = f"run_{timestamp_index}.log"
    full_log_path = os.path.join(logs_dir, log_filename)

    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S %Z"

    logger = logging.getLogger(logger_name)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.INFO)

    class TZFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            dt = datetime.fromtimestamp(record.created, used_tz)
            return dt.strftime(datefmt) if datefmt else dt.isoformat()

    file_formatter = TZFormatter(log_format, datefmt=date_format)
    console_formatter = TZFormatter(log_format, datefmt=date_format)

    file_handler = logging.FileHandler(full_log_path, encoding='utf-8')
    #file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    #console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Archive file created at: {full_log_path}")

    return logger
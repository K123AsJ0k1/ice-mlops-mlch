
def logger_setup_configuration(
    logger_name: str
) -> any:
    try:
        import sys
        import logging
        import os
        from datetime import datetime
    except ImportError as e:
        raise ImportError("logger/use failed to import", e)
    
    main_script_path = os.path.abspath(sys.argv[0])
    script_dir = os.path.dirname(main_script_path)
    
    logs_dir = os.path.join(script_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Format: run_YYYYMMDD_HHMMSS.log (e.g., run_20260603_071530.log)
    timestamp_index = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"run_{timestamp_index}.log"
    full_log_path = os.path.join(logs_dir, log_filename)

    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger(logger_name)
    
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(full_log_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Archive file created at: {full_log_path}")

    return logger
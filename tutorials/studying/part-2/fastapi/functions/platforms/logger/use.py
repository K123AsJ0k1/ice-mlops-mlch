def logger_get_logs(
    log_path: str
):
    listed_logs = {'logs':[]}
    with open(log_path, 'r') as f:
        for line in f:
            listed_logs['logs'].append(line.strip())
    return listed_logs

def slurm_format_sbatch(
    resulted_print: str
) -> any:
    try:
        import re
    except ImportError as e:
        raise ImportError("slurm/use failed to import", e)

    pattern = re.search(r'Submitted batch job (\d+)', resulted_print)
    return pattern.group(1) if pattern else None

def slurm_squeue_columns() -> str:
    columns = [
        '%i',
        '%P',
        '%j',
        '%T',
        '%M',
        '%D',
        '%p',
        '%R'
    ]
    start_command = ' --format='
    column_string = ''
    for column in columns:
        if len(column_string) == 0:
            column_string = column
            continue
        column_string += '|' + column 
    complete_command = start_command + '"' + column_string + '"'
    return complete_command

def slurm_format_squeue(
    resulted_print: str
) -> any:
    data_dict = {}
    lines = resulted_print.strip().split('\n')
    if 1 <= len(lines):
        headers = lines[0].split('|')
        fixed_names = []
        data_dict = {}
        for header in headers:
            formatted_name = header.lower()

            if '(' in formatted_name:
                formatted_name = formatted_name.split('(')[0]

            fixed_names.append(formatted_name)
            data_dict[formatted_name] = []
            
        if 2 <= len(lines):
            for line in lines[1:]:
                if '|' in line:
                    values = line.split('|')
                    for i, val in enumerate(values):
                        data_dict[fixed_names[i]].append(val)
    return data_dict

def slurm_sacct_metrics() -> str:
    columns = [
        'JobID',
        'JobName',
        'Account',
        'Partition',
        'ReqCPUS',
        'AllocCPUS',
        'ReqNodes',
        'AllocNodes',
        'State',
        'AveCPU',
        'AveCPUFreq',
        'AveDiskRead',
        'AveDiskWrite',
        'Timelimit',
        'Submit',
        'Start',
        'Elapsed',
        'Planned',
        'End',
        'PlannedCPU',
        'CPUTime',
        'TotalCPU'
    ] 
    start_command = ' --format='
    column_string = ''
    for column in columns:
        if len(column_string) == 0:
            column_string = column
            continue
        column_string += ',' + column 

    end_command = ' --parsable --delimiter="|"'
    complete_command = start_command + '"' + column_string + '"' + end_command
    return complete_command

def slurm_metric_formatting(
    name: str
) -> any:
    formatted_name = ''
    first = True
    index = -1
    for character in name:
        index += 1
        if character.isupper():
            if first:
                first = False
                formatted_name += character
                continue
            if index + 1 < len(name): 
                if name[index - 1].islower():
                    formatted_name += '-' + character
                    continue
                if name[index - 1].isupper() and name[index + 1].islower():
                    formatted_name += '-' + character
                    continue
        formatted_name += character 
    return formatted_name.lower()

def slurm_format_sacct(
    file_path: str
) -> any:
    try:
        from datetime import datetime
        from ..misc.general import convert_into_seconds,unit_converter
    except ImportError as e:
        raise ImportError("slurm/use failed to import", e)

    sacct_text = None
    with open(file_path, 'r', encoding = 'utf-8') as f:
        sacct_text = f.read()
    
    data_dict = {}
    if not sacct_text is None:
        metrics = {
            'ave-cpu': 'seconds',
            'ave-cpu-freq': 'khz',
            'ave-disk-read': 'bytes',
            'ave-disk-write': 'bytes',
            'timelimit': 'seconds',
            'elapsed': 'seconds',
            'planned': 'seconds',
            'planned-cpu': 'seconds',
            'cpu-time': 'seconds',
            'total-cpu': 'seconds',
            'submit': 'time',
            'start': 'time',
            'end': 'time'
        }

        ignore = [
            'account'
        ]
        
        metadata = [
            'job-name',
            'job-id',
            'partition',
            'state'
        ]
        
        data_dict = {}
        lines = sacct_text.strip().split('\n')
        if 1 <= len(lines):
            headers = lines[0].split('|')[:-1]
            fixed_names = []
            for header in headers:
                formatted_name = slurm_metric_formatting(name = header)
                
                if formatted_name in metrics:
                    formatted_name += '-' + metrics[formatted_name]

                fixed_names.append(formatted_name)
                data_dict[formatted_name] = []

            if 2 <= len(lines):
                for line in lines[1:]:
                    if '|' in line:
                        values = line.split('|')[:-1]
                        for i, val in enumerate(values):
                            key = fixed_names[i]
                            key_value = val
                        
                            if not key in ignore:
                                if key in metadata:
                                    if key == 'job-id':
                                        key_value = key_value.split('.')[0] 
                                elif ':' in key_value:
                                    if 'T' in key_value:
                                        format = datetime.strptime(key_value, '%Y-%m-%dT%H:%M:%S')
                                        key_value = round(format.timestamp())
                                    else:
                                        key_value = convert_into_seconds(
                                            given_time = key_value
                                        )
                                else:
                                    if 'bytes' in key_value:
                                        key_value = unit_converter(
                                            value = key_value,
                                            bytes = True
                                        )
                                    else:
                                        key_value = unit_converter(
                                            value = key_value,
                                            bytes = False
                                        )
                            if key_value == '':
                                key_value = 'NA'
                            data_dict[fixed_names[i]].append(key_value)
    return data_dict

def slurm_fix_sacct(
    sacct_dict: any,
    column_types: any,
    value_replacers: any
) -> any:
    fixed_sacct = {}
    for name,values in sacct_dict.items():
        column_type = column_types[name]
        replacer = value_replacers[column_type]
        fixed_values = []
        for value in values:
            fixed_value = value
            if value == 'NA':
                fixed_value = replacer
            if column_type == 'str':
                fixed_value = str(fixed_value)
            if column_type == 'int':
                fixed_value = int(fixed_value)
            if column_type == 'float':
                fixed_value = float(fixed_value)
            fixed_values.append(fixed_value)
        fixed_sacct[name] = fixed_values
    return fixed_sacct

def format_slurm_logs(
    file_path: str
) -> any:
    log_text = None
    with open(file_path, 'r') as f:
        log_text = f.readlines()
    
    row_list = []
    if 0 < len(log_text):
        for line in log_text:
            filter_1 = line.replace('\n', '')
            filter_2 = filter_1.replace('\t', ' ')
            filter_3 = filter_2.replace('\x1b', ' ')
            if not filter_3.isspace() and 0 < len(filter_3):
                row_list.append(filter_3)
    return row_list 
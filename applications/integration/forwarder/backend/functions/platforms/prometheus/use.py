from prometheus_client import Gauge

def prometheus_set_gauge(
    prometheus_registry: any,
    gauge_structure: any
) -> any:
    gauge = Gauge(
        name = gauge_structure['name'],
        documentation = gauge_structure['docs'],
        labelnames = gauge_structure['labels'],
        registry = prometheus_registry
    )
    return gauge

'''
def get_sacct_gauge_structure():
    # Double check the labels
    structure = {
        'name': 'cloud_hpc_job_sacct_metrics',
        'docs': 'SLURM Sacct metrics collected from completed jobs',
        'labels': [
            'user',
            'jobkey',
            'jobid',
            'row',
            'jobname',
            'partition',
            'state',
            'metric'
        ],
        'names': {
            'req-cpus': 'RqCPUS',
            'alloc-cpus': 'AcCPUS',
            'req-nodes': 'RqNod',
            'alloc-nodes': 'AcNod',
            'ave-cpu-seconds': 'AvCPUSec',
            'ave-cpu-freq-khz': 'AvCPUFreqkhz',
            'ave-disk-read-bytes': 'AvDiReByte',
            'ave-disk-write-bytes': 'AvDiWrByte',
            'timelimit-seconds': 'TiLiSec',
            'elapsed-seconds': 'ElaSec',
            'planned-seconds': 'PlaSec',
            'planned-cpu-seconds': 'PlaCPUSec',
            'cpu-time-seconds': 'CPUTiSec',
            'total-cpu-seconds': 'ToCPUSec',
            'submit-time': 'SuTi',
            'start-time': 'StTi',
            'end-time': 'EnTi'
        }
    }
    return structure

def get_seff_gauge_structure():
    structure = {
        'name': 'cloud_hpc_job_seff_metrics',
        'docs': 'SLURM Seff metrics collected from completed jobs',
        'labels': [
            'user',
            'jobkey',
            'jobid',
            'project',
            'cluster', 
            'state',
            'metric'
        ],
        'names': {
            'nodes': 'Nod',
            'cores-per-node': 'CoPeNod',
            'cpu-utilized-seconds': 'CPUUSec',
            'cpu-efficiency-percentage': 'CPUEffPe',
            'cpu-efficiency-seconds': 'CPUEffSec',
            'job-wall-clock-time-seconds': 'JoWaClTISec',
            'memory-utilized-bytes': 'MemUtiByte',
            'memory-efficiency-percentage': 'MemEffPe',
            'memory-efficiency-bytes': 'MemEffByte',
            'billing-units': 'BiUn'
        }
    }
    return structure

def get_job_time_gauge_structure():
    structure = {
        'name': 'cloud_hpc_job_time_metrics',
        'docs': 'Time metrics collected from submitter jobs',
        'labels': [
            'collector',
            'jobkey',
            'metric'
        ],
        'names': {
            'total-start-seconds': 'ToStaSec',
            'total-configuration-seconds': 'ToConSec',
            'total-run-seconds': 'ToRunSec', 
            'total-cancel-seconds': 'ToCanSec',
            'total-store-seconds': 'ToStoSec'
        }
    }
    return structure

def get_pipeline_time_gauge_structure():
    structure = {
        'name': 'cloud_hpc_pipeline_time_metrics',
        'docs': 'Time metrics collected from pipeline times',
        'labels': [
            'collector',
            'sampleid',
            'group',
            'name',
            'metric'
        ],
        'names': {
            'total-seconds': 'ToSec'
        }
    }
    return structure

def get_task_time_gauge_structure():
    structure = {
        'name': 'cloud_hpc_task_time_metrics',
        'docs': 'Time metrics collected from forwarder and submitter tasks',
        'labels': [
            'collector',
            'sampleid',
            'group',
            'metric'
        ],
        'names': {
            'total-wait-seconds': 'ToWaiSec',
            'total-run-seconds': 'ToRunSec',
            'total-task-seconds': 'ToTasSec'
        }
    }
    return structure

from prometheus_client import CollectorRegistry, multiprocess

from celery.functions.platforms.prometheus.prometheus import set_prometheus_gauge
from celery.functions.platforms.prometheus.gauges import get_sacct_gauge_structure, get_seff_gauge_structure, get_job_time_gauge_structure, get_pipeline_time_gauge_structure, get_task_time_gauge_structure
from functions.utility.collection.artifacts import gather_artifacts
from celery.functions.platforms.prometheus.times import gather_times
from celery.functions.platforms.prometheus.scraping import scrape_sacct,scrape_seff, scrape_job_time, scrape_pipeline_time, scrape_task_time

global_registry = CollectorRegistry()
multiprocess.MultiProcessCollector(global_registry)

sacct_gauge = set_prometheus_gauge(
    prometheus_registry = global_registry,
    gauge_structure = get_sacct_gauge_structure()
)

seff_gauge = set_prometheus_gauge(
    prometheus_registry = global_registry,
    gauge_structure = get_seff_gauge_structure()
)

job_time_gauge = set_prometheus_gauge(
    prometheus_registry = global_registry,
    gauge_structure = get_job_time_gauge_structure()
)

pipeline_time_gauge = set_prometheus_gauge( 
    prometheus_registry = global_registry,
    gauge_structure = get_pipeline_time_gauge_structure()
)

task_time_gauge = set_prometheus_gauge(
    prometheus_registry = global_registry,
    gauge_structure = get_task_time_gauge_structure()
)

def utilize_artifacts(
    storage_client: any, 
    storage_name: str,
    type: str
):
    submitters_artifacts = gather_artifacts(
        storage_client = storage_client,
        storage_name = storage_name,
        type = type
    )

    gauge_structure = {}
    prometheus_gauge = None
    if type == 'sacct':
        gauge_structure = get_sacct_gauge_structure()
        prometheus_gauge = sacct_gauge
    if type == 'seff':
        gauge_structure = get_seff_gauge_structure()
        prometheus_gauge = seff_gauge
    if 0 < len(submitters_artifacts):
        if 0 < len(gauge_structure):
            for submitter_name, artifacts in submitters_artifacts.items():
                for artifact_key, artifact in artifacts.items():
                    submitter_name_split = submitter_name.split('-')
                    submitter_user = '-'.join(submitter_name_split[5:])
                    if type == 'sacct':
                        scrape_sacct(
                            prometheus_gauge = prometheus_gauge,
                            artifact_key = artifact_key,
                            user = submitter_user,
                            metric_names = gauge_structure['names'],
                            data = artifact
                        )
                    if type == 'seff':
                        scrape_seff(
                            prometheus_gauge = prometheus_gauge,
                            artifact_key = artifact_key,
                            user = submitter_user,
                            metric_names = gauge_structure['names'],
                            data = artifact
                        )  

def utilize_time(
    storage_client: any, 
    storage_name: str,
    type: str
): 
    time_artifacts = gather_times(
        storage_client = storage_client,
        storage_name = storage_name,
        type = type
    ) 
    
    gauge_structure = {}
    prometheus_gauge = None
    if type == 'job-time':
        gauge_structure = get_job_time_gauge_structure()
        prometheus_gauge = job_time_gauge
    if type == 'pipeline-time':
        gauge_structure = get_pipeline_time_gauge_structure()
        prometheus_gauge = pipeline_time_gauge
    if type == 'task-time':
        gauge_structure = get_task_time_gauge_structure()
        prometheus_gauge = task_time_gauge
    if 0 < len(time_artifacts):
        if 0 < len(gauge_structure):
            for collector_name, artifacts in time_artifacts.items():
                for artifact_name, artifact in artifacts.items():
                    if type == 'job-time':
                        scrape_job_time(
                            prometheus_gauge = prometheus_gauge,
                            collector = collector_name,
                            job_key = artifact_name,
                            metric_names = gauge_structure['names'],
                            data = artifact
                        )
                    if type == 'pipeline-time':
                        scrape_pipeline_time(
                            prometheus_gauge = prometheus_gauge,
                            collector = collector_name,
                            time_group = artifact_name,
                            metric_names = gauge_structure['names'],
                            data = artifact
                        )
                    if type == 'task-time': 
                        scrape_task_time(
                            prometheus_gauge = prometheus_gauge,
                            collector = collector_name,
                            time_group = artifact_name,
                            metric_names = gauge_structure['names'],
                            data = artifact
                        )

from functions.platforms.slurm import parse_sacct_dict, parse_seff_dict

def scrape_sacct(
    prometheus_gauge: any,
    artifact_key: str,
    user: str,
    metric_names: any,
    data: any
):
    for row, sample in data.items():
        formatted_metrics, formatted_metadata = parse_sacct_dict(
            sacct_data = sample
        )
        
        if 'partition' in formatted_metadata:
            partition = formatted_metadata['partition']
        else:
            formatted_metadata['partition'] = partition

        job_user = str(user)
        job_key = str(artifact_key)
        sacct_row = str(row)
        job_id = str(formatted_metadata['job-id'])
        job_name = str(formatted_metadata['job-name'])
        job_partition = str(formatted_metadata['partition'])
        job_state = str(formatted_metadata['state'])

        for key, value in formatted_metrics.items():
            metric_name = metric_names[key]
            prometheus_gauge.labels(
                user = job_user,
                jobkey = job_key,
                jobid = job_id,
                row = sacct_row,
                jobname = job_name,
                partition = job_partition,
                state = job_state,
                metric = metric_name
            ).set(value)
 
def scrape_seff(
    prometheus_gauge: any,
    artifact_key: str,
    user: str,
    metric_names: any,
    data: any    
):
    formatted_metrics, formatted_metadata = parse_seff_dict(
        seff_data = data
    )
     
    job_user = str(user)
    job_key = str(artifact_key)
    job_id = str(formatted_metadata['job-id'])
    job_cluster = str(formatted_metadata['cluster'])
    job_project = str(formatted_metadata['billed-project'])
    job_state = str(formatted_metadata['status'])
    status = str(formatted_metadata['status'])
    exit_code = str(formatted_metadata['exit-code'])
    job_state = status + '-' + exit_code

    for key, value in formatted_metrics.items():
        metric_name = metric_names[key]
        prometheus_gauge.labels(
            user = job_user,
            jobkey = job_key,
            jobid = job_id,
            project = job_project,
            cluster = job_cluster, 
            state = job_state,
            metric = metric_name
        ).set(value)        

def scrape_job_time(
    prometheus_gauge: any,
    collector: str,
    job_key: str,
    metric_names: any,
    data: any
):
    for key, value in data.items():
        if 'total' in key: 
            metric_name = metric_names[key]
            prometheus_gauge.labels(
                collector = collector,
                jobkey = job_key,
                metric = metric_name
            ).set(value)   

def scrape_pipeline_time(
    prometheus_gauge: any,
    collector: str,
    time_group: str,
    metric_names: any,
    data: any
):
    for time_id, time_info in data.items():
        time_name = time_info['name']
        for key, value in time_info.items():
            if 'total' in key:
                metric_name = metric_names[key]
                prometheus_gauge.labels(
                    collector = collector,
                    sampleid = time_id,
                    group = time_group,
                    name = time_name,
                    metric = metric_name
                ).set(value)  

def scrape_task_time(
    prometheus_gauge: any,
    collector: str,
    time_group: str,
    metric_names: any,
    data: any
):
    for task_id, time_info in data.items():
        for key, value in time_info.items():
            if 'total' in key: 
                metric_name = metric_names[key]
                prometheus_gauge.labels(
                    collector = collector, 
                    sampleid = task_id,
                    group = time_group,
                    metric = metric_name
                ).set(value)  
'''
import ray
import json
from functions.utility import utility_managed_span
from icebreaker.assistant.utility import assistant_format_context

def retrieval_send_query(
    mlflow_client: any,
    span_name: str,
    trace_id: any,
    root_span_id: any,
    retrieval_parameters: dict,
    query_text: str,
    retrieval_ref: any,
    dataset_name: str,
    query_weights: dict,
    pipeline_record: dict
):
    with utility_managed_span( 
        mlflow_client = mlflow_client, 
        span_name = span_name, 
        trace_id = trace_id, 
        parent_span_id = root_span_id 
    ) as retrieval_span:
        collection_name = retrieval_parameters['collection-name']
        query_type = retrieval_parameters['query-type']
        relevance_threshold = retrieval_parameters['relevance-threshold']
        query_limit = retrieval_parameters['query-limit']
        fusion_limit = retrieval_parameters['fusion-limit']
        batch_size = retrieval_parameters['batch-size']
        
        retrieval_span.set_inputs({
            'query': query_text
        })

        retrieval_span.set_attributes({f'request.{k}': v for k, v in retrieval_parameters.items()})

        retrieval_query = [query_text]
        retrieval_query_ref = ray.put(retrieval_query)
        retrieval_payload_ref = retrieval_ref.batch_generate_queries.remote(
            key_name = dataset_name,
            query_type = query_type,
            collection_name = collection_name,
            text_query_batch = retrieval_query_ref,
            relevant_weights_batch = query_weights,
            relevance_threshold = relevance_threshold,
            query_limit = query_limit,
            fusion_limit = fusion_limit,
            batch_size = batch_size 
        )
        retrieval_payload = ray.get(retrieval_payload_ref)

        pipeline_metrics = {
            'p@1': 0,
            'r@3': 0,
            'rr': 0,
            'ap': 0,
            'ndcg@3': 0,
            'ndcg@5': 0,
            'embedding-latency-ms': 0,
            'search-latency-ms': 0,
            'total-latency-ms': 0,
            'total-characters': 0
        }
        created_context = ''
        query_index_list = []
        if 0 < len(retrieval_payload['results']):
            query_index_list = retrieval_payload['metadata'][0]['retrieved-idx']
            pipeline_metrics = retrieval_payload['metrics'][0]
            
            created_context = assistant_format_context(
                query_results = retrieval_payload['results'],
                wrapper_tag = 'context',
                metadata_keys = [
                    'part',
                    'document',
                    'chapter',
                    'index',
                    'absolute-path',
                    'relevance'
                ],
                material_key = 'ref-material',
                path_key = 'ref-paths',
                content_key = 'content'
            )

        pipeline_record['retrieval-data']['metrics'] = pipeline_metrics

        pipeline_output = {
            'query-identities': json.dumps(query_index_list),
            'query-ranks': json.dumps(query_weights), 
            'created-context': created_context
        }
        pipeline_output = pipeline_output | pipeline_metrics
        pipeline_record['retrieval-data']['output'] = pipeline_output
        retrieval_span.set_outputs(pipeline_output)

        return created_context
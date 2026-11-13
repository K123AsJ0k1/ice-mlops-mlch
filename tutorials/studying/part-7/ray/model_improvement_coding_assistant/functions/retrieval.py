import ray
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

        created_context = ''
        if 0 < len(retrieval_payload['results']):
            pipeline_record['retrieval-data']['metrics'] = retrieval_payload['metrics']
            
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

            pipeline_record['retrieval-data']['output'] = created_context
            
        retrieval_span.set_outputs({
            'created-context': created_context
        })

        return created_context
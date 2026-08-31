def assistant_format_context(
    query_results: any,
    wrapper_tag: str,
    metadata_keys: list,
    material_key: str,
    path_key: str,
    content_key: str
) -> any:
    try:
        import xml.etree.ElementTree as ET
        from xml.dom import minidom
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    collected_context = []
    collected_metrics = []
    root = ET.Element(wrapper_tag)
    for j, (result, metrics) in enumerate(query_results):
        for i, point in enumerate(result, 1):
            query_score = point.score
            query_payload = point.payload

            chunk_attributes = {}
            chunk_attributes['id'] = str(i)
            chunk_attributes['score'] = str(round(query_score,2))
            for metadata_key in metadata_keys:
                chunk_attributes[metadata_key] = str(query_payload.get(metadata_key))

            chunk_elem = ET.SubElement(root, "chunk", attrib = chunk_attributes)

            reference_material = query_payload.get(material_key)
            if reference_material:
                material_attributes = {}
                for key, value in reference_material.items():
                    key_split = key.split('|')
                    material_tag = key_split[0]
                    value_type = key_split[1]

                    if not material_tag in material_attributes:
                        material_attributes[material_tag] = {
                            'tag': material_tag
                        }

                    material_attributes[material_tag][value_type] = value

                materials = list(material_attributes.values())
                for item in materials:
                    ET.SubElement(chunk_elem, "reference-material", attrib = item)

            reference_paths = query_payload.get(path_key)
            if reference_paths:
                path_attributes = {}
                id = 1
                for key, value in reference_paths.items():
                    if not id in path_attributes:
                        path_attributes[id] = {
                            'id': str(id)
                        }
                    path_attributes[id]['relative-path'] = key
                    path_attributes[id]['absolute-path'] = value
                    id += 1
                    
                paths = list(path_attributes.values())
                for item in paths:
                    ET.SubElement(chunk_elem, "reference-path", attrib = item)

            content_elem = ET.SubElement(chunk_elem, "content")
            # Use \n{query_payload.get(content_key)}\n for presentation
            query_content = query_payload.get(content_key)
            collected_context.append(query_content)
            content_elem.text = str(f'{query_content.replace('\n','').replace('\r','')}')
        metrics['batch-index'] = j
        collected_metrics.append(metrics)

    raw_xml = ET.tostring(root, encoding="utf-8")
    parsed_xml = minidom.parseString(raw_xml)
    
    # Pretty-print and strip the default <?xml version="1.0"?> declaration header
    formatted_xml = parsed_xml.toprettyxml(indent="")
    xml_lines = formatted_xml.splitlines()
    
    if xml_lines and xml_lines[0].startswith("<?xml"):
        xml_lines = xml_lines[1:]

    formatted_context = "\n".join(xml_lines)
    return collected_context, formatted_context, collected_metrics
            
def assistant_create_requests( 
    target_df: any,
    prompt_parameters: any,
    dataset_name: str,
    target_model: str,
    type_column: str,
    data_ratio: any,
    join_prompts: bool,
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    query_limit: int,
    fusion_limit: int,
    dense_model_name: str,
    dense_model: any,
    sparse_model_name: str,
    sparse_model: any,
    batch_size: int,
    relevance_threshold: float
):
    try:
        import re
        from ..search.use import search_monitored_batch_query
        from ..assistant.use import assistant_format_context
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    print('Creating assistant requests')
    inference_requests = []
    rag_metrics = []
    request_idx = 0
    assistant_type_idx = {}
    for _, row in target_df.iterrows(): 
       
        replacer_dict = {
            'QUERY': row['question']
        }
        for data_type, wanted_amount in data_ratio.items():
            if not data_type in assistant_type_idx:
                assistant_type_idx[data_type] = 0 
            
            system_prompt = prompt_parameters[data_type]['system-prompt']
            user_template = prompt_parameters[data_type]['user-template']
            
            temperature = prompt_parameters[data_type]['temperature'][target_model]
            top_p = prompt_parameters[data_type]['top-p'][target_model]
            max_tokens = prompt_parameters[data_type]['max-tokens'][target_model]

            if 'rag' in data_type:
                text_query_batch = [row['question']]

                relevant_weights_batch = []
                if 'chunk-relevant-weights' in row:
                    relevant_weights_batch = row['chunk-relevant-weights']

                batch_query_results = search_monitored_batch_query(
                    qdrant_client = qdrant_client,
                    query_type = query_type, 
                    collection_name = collection_name,
                    text_query_batch = text_query_batch, 
                    relevant_weights_batch = relevant_weights_batch,
                    relevance_threshold = relevance_threshold,
                    query_limit = query_limit,
                    fusion_limit = fusion_limit,
                    dense_model_name = dense_model_name,
                    dense_model = dense_model,
                    sparse_model_name = sparse_model_name,
                    sparse_model = sparse_model,
                    batch_size = batch_size
                )
                
                _, formatted_context, batch_metrics = assistant_format_context(
                    query_results = batch_query_results,
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

                batch_metadata = {
                    'request-index': request_idx,
                    'assistant-variant': data_type,
                    'question-type': row[type_column],
                    'query-batch': text_query_batch,
                }

                merged_data = batch_metrics[0] | batch_metadata
                
                rag_metrics.append(merged_data)
                replacer_dict['CONTENT'] = formatted_context

            pattern = r'\[([A-Z_1-9]+)\]'
            user_prompt = re.sub(
                pattern, 
                lambda m: str(replacer_dict.get(m.group(1), m.group(0))), 
                user_template
            )
            sent_messages = []
            system_prompt_length = 0
            user_prompt_length = 0
            if join_prompts:
                joined_prompt = f'{system_prompt}\n{user_prompt}'
                user_prompt_length = len(joined_prompt)
                sent_messages.append({
                    "role": "user", 
                    "content": joined_prompt
                })
            else:
                system_prompt_length = len(system_prompt)
                sent_messages.append({
                    "role": "system", 
                    "content": system_prompt
                })
                user_prompt_length = len(user_prompt)
                sent_messages.append({
                    "role": "user", 
                    "content": user_prompt
                })

            for i in range(0, wanted_amount):
                inference_requests.append({
                    'dataset-name': dataset_name,
                    'request-index': request_idx,
                    'question-type': row[type_column],
                    'assistant-variant': data_type,
                    'assistant-index': assistant_type_idx[data_type],
                    'messages': sent_messages,
                    'system-prompt-length': system_prompt_length,
                    'user-prompt-length': user_prompt_length,
                    'target-model': target_model,
                    'temperature': temperature,
                    'top-p': top_p,
                    'max-tokens': max_tokens
                })
                assistant_type_idx[data_type] += 1
        request_idx += 1
    print(f'Amount of requests: {len(inference_requests)}')
    return inference_requests, rag_metrics

def assistant_generate_answers(
    dataset_inference_requests: list,
    request_keys: dict,
    char_to_token_ratio: float,
    length_limit: int,
    inference_parameters: any,
    controller_model: str,
    controller_prompts: any,
    debug_prints: bool
) -> dict:
    try:
        import time as t
        from ..controller.use import controller_create_request
        from ..ray.utility import ray_run_inference
        from ..controller.utility import controller_extract_output
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    process_time_start = t.time()
    print('Getting answers')
    token_limit = char_to_token_ratio * length_limit
    print(f'Request token limit {token_limit}\n')

    # Flat records list for row-based downstream analytics
    run_records = []
    for inference_requests in dataset_inference_requests:
        execution_time_start = t.time()
        
        dataset_name = inference_requests['dataset-name']
        request_index = inference_requests['request-index']
        question_type = inference_requests['question-type']
        assistant_variant = inference_requests['assistant-variant']
        assistant_index = inference_requests['assistant-index']
        
        system_prompt_length = inference_requests['system-prompt-length']
        user_prompt_length = inference_requests['user-prompt-length']
        target_model = inference_requests['target-model']
        used_context = system_prompt_length + user_prompt_length

        print('Assistant request:')
        print(f'Request|{request_index + 1}')
        print(f'Question type|{question_type}')
        print(f'Assistant variant|{assistant_variant}')

        # Base trace schema for single inference run
        record = {
            "metadata": {
                "dataset": dataset_name,
                "request-index": request_index,
                "assistant-variant": assistant_variant,
                "assistant-index": assistant_index,
                "question-type": question_type,
                "system-prompt-length": system_prompt_length,
                "user-prompt-length": user_prompt_length,
                "target-model": target_model,
            },
            "status": "ACCEPTED", # ACCEPTED, REFUSED_CONTEXT, REFUSED_INPUT, REFUSED_OUTPUT
            "refusal-reason": None,
            "assistant-data": {},
            "controller-input-data": {},
            "controller-output-data": {},
            "assistant-request": inference_requests,
            "execution-time-sec": 0.0
        }

        # 1. Context Length Validation
        if token_limit <= used_context:
            record["status"] = "REFUSED_CONTEXT"
            record["refusal-reason"] = "CONTEXT_LIMIT_REACHED"
            record["execution-time-sec"] = round(t.time() - execution_time_start, 5)
            run_records.append(record)
            continue

        user_question = ""

        # Safely extract user question regardless of variant path
        if 'messages' in inference_requests and inference_requests['messages']:
            user_message_content = inference_requests['messages'][-1].get('content', '')
            _, _, after_tag = user_message_content.partition('### USER REQUEST:')
            user_question = after_tag.strip() if after_tag else user_message_content

        # 2. Input Guardrail Verification
        if 'pe-rag-bc-eval' in assistant_variant:
            controller_input_check_request = controller_create_request(
                request_index=request_index, 
                assistant_index=assistant_index,
                assistant_variant=assistant_variant,
                assistant_input=user_question,
                assistant_output='',
                prompt_parameters=controller_prompts,
                dataset_name=dataset_name,
                target_model=controller_model,
                prompt_type='controller-input-eval',
                join_prompts=False
            )

            ctrl_in_out, ctrl_in_meta, ctrl_in_time = ray_run_inference(
                inference_address=inference_parameters['controller']['address'],
                inference_path=inference_parameters['controller']['path'],
                sent_request=controller_input_check_request
            )

            input_behavior = {'reasoning': '', 'secret-leak': 0, 'off-topic': 0}

            try:
                input_behavior = controller_extract_output(
                    output = 
                    ctrl_in_out
                )
            except Exception:
                input_behavior = {'reasoning': 'Malformed JSON returned by guardrail', 'secret-leak': 0, 'off-topic': 0}

            record["controller-input-data"] = {
                "request": controller_input_check_request,
                "output": ctrl_in_out,
                "metrics": ctrl_in_meta,
                "latency-sec": ctrl_in_time,
                "behavior": input_behavior
            }

            if input_behavior.get('secret-leak') == 1 or input_behavior.get('off-topic') == 1:
                reasons = []
                if input_behavior.get('secret-leak') == 1: reasons.append("SECRET_LEAK")
                if input_behavior.get('off-topic') == 1: reasons.append("OFF_TOPIC")
                
                record["status"] = "REFUSED_INPUT"
                record["refusal-reason"] = " | ".join(reasons)
                record["execution-time-sec"] = round(t.time() - execution_time_start, 5)
                run_records.append(record)
                continue

        # 3. Target Assistant Model Execution
        ast_out, ast_meta, ast_time = ray_run_inference(
            inference_address=inference_parameters['assistant']['address'],
            inference_path=inference_parameters['assistant']['path'],
            sent_request = inference_requests
        )

        record["assistant-data"] = {
            "request": inference_requests,
            "output": ast_out,
            "metrics": ast_meta,
            "latency-sec": ast_time
        }

        # 4. Output Guardrail Verification
        if 'pe-rag-bc-eval' in assistant_variant:
            controller_output_check_request = controller_create_request(
                request_index=request_index,
                assistant_index=assistant_index,
                assistant_variant=assistant_variant,
                assistant_input=user_question,
                assistant_output=ast_out,
                prompt_parameters=controller_prompts,
                dataset_name=dataset_name,
                target_model=controller_model,
                prompt_type='controller-output-eval',
                join_prompts=False
            )

            ctrl_out_out, ctrl_out_meta, ctrl_out_time = ray_run_inference(
                inference_address = inference_parameters['controller']['address'],
                inference_path = inference_parameters['controller']['path'],
                sent_request = controller_output_check_request
            )

            try:
                output_behavior = controller_extract_output(
                    output = ctrl_out_out
                )
            except Exception:
                output_behavior = {'reasoning': 'Malformed JSON returned by guardrail', 'irrelevant': 0, 'verbose': 0, 'out-of-scope': 0}

            record["controller-output-data"] = {
                "request": controller_output_check_request,
                "output": ctrl_out_out,
                "metrics": ctrl_out_meta,
                "latency-sec": ctrl_out_time,
                "behavior": output_behavior
            }

            if output_behavior.get('irrelevant') == 1 or output_behavior.get('verbose') == 1 or output_behavior.get('out-of-scope') == 1:
                reasons = []
                if output_behavior.get('irrelevant') == 1: reasons.append("IRRELEVANT")
                if output_behavior.get('verbose') == 1: reasons.append("VERBOSE")
                if output_behavior.get('out-of-scope') == 1: reasons.append("OUT_OF_SCOPE")

                record["status"] = "REFUSED_OUTPUT"
                record["refusal-reason"] = " | ".join(reasons)

        record["execution-time-sec"] = round(t.time() - execution_time_start, 5)
        run_records.append(record)
    
    process_end_time = t.time()
    process_total_time = round(process_end_time-process_time_start,5)
    print(f'Spent seconds on processing: {process_total_time}')
    print('') 
    return {
        "records": run_records,
        "stats": {
            "total-process-time-sec": process_total_time,
            "total-samples": len(run_records),
            "accepted-count": sum(1 for r in run_records if r["status"] == "ACCEPTED")
        }
    }

def assistant_print_answers(
    run_data: dict
):  
    records = run_data.get("records", [])
    print(f"START ANSWERS | Total Records: {len(records)}\n")

    for idx, record in enumerate(records, start=1):
        meta = record["metadata"]
        print(f"=== Record {idx}/{len(records)} ===")
        print(f"Status|{record['status']}")
        if record["refusal-reason"]:
            print(f"Refusal Reason|{record['refusal-reason']}")

        print(f"Dataset|{meta['dataset']}")
        print(f"Request|{meta['request-index'] + 1}")
        print(f"Question Type|{meta['question-type']}")
        print(f"Assistant Variant|{meta['assistant-variant']}")
        print(f"Assistant Index|{meta['assistant-index']}")
        print(f"Model|{meta['target-model']}")
        print(f"Execution Latency|{record['execution-time-sec']}s")
        print("----------")

        # 1. Assistant Prompts
        print("Assistant Prompts:")
        for msg in record["assistant-request"].get("messages", []):
            print(f"  Role: {msg.get('role')}")
            print(f"  Prompt:\n{msg.get('content')}\n")

        # 2. Controller Input Check (if ran)
        if record.get("controller-input-data"):
            ctrl_in = record["controller-input-data"]
            print("Controller Input Check Result:")
            print(f"  Output: {ctrl_in['output']}")
            print(f"  Behavior: {ctrl_in['behavior']}\n")

        # 3. Assistant Output
        print("Assistant Output:")
        print(record.get("assistant-data").get('output') or "None (Refused before generation)")
        print("----------")

        # 4. Controller Output Check (if ran)
        if record.get("controller-output-data"):
            ctrl_out = record["controller-output-data"]
            print("Controller Output Check Result:")
            print(f"  Output: {ctrl_out['output']}")
            print(f"  Behavior: {ctrl_out['behavior']}\n")

        print("=" * 40 + "\n")

def assistant_produce_answers(
    target_df: any,
    assistant_prompts: dict,
    dataset_name: str,
    assistant_model: str,
    type_column: str,
    data_ratio: dict,
    join_prompts: bool,
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    query_limit: int,
    fusion_limit: int,
    dense_model_name: str,
    dense_model: any,
    sparse_model_name: str,
    sparse_model: any,
    batch_size: int,
    relevance_threshold: float,
    request_keys: list,
    char_to_token_ratio: float,
    length_limit: int,
    inference_parameters: any,
    controller_model: str,
    controller_prompts: dict,
    summary_root_keys: dict,
    summary_target_keys: list,
    summary_relevant_key_columns: dict,
    summary_wanted_stats: list,
    summary_key_group_column: dict
):
    try:
        from ..assistant.use import assistant_create_requests, assistant_generate_answers, assistant_print_answers
        from ..evaluation.use import evaluation_nested_metrics
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    assistant_requests = assistant_create_requests(
        target_df = target_df,
        prompt_parameters = assistant_prompts,
        dataset_name = dataset_name,
        target_model = assistant_model,
        type_column = type_column,
        data_ratio = data_ratio,
        join_prompts = join_prompts,
        qdrant_client = qdrant_client,
        query_type = query_type, 
        collection_name = collection_name,
        query_limit = query_limit,
        fusion_limit = fusion_limit,
        dense_model_name = dense_model_name,
        dense_model = dense_model,
        sparse_model_name = sparse_model_name,
        sparse_model = sparse_model,
        batch_size = batch_size,
        relevance_threshold = relevance_threshold
    )

    assistant_run_data = assistant_generate_answers(
        dataset_inference_requests = assistant_requests[0],
        request_keys = request_keys,
        char_to_token_ratio = char_to_token_ratio,
        length_limit = length_limit,
        inference_parameters = inference_parameters,
        controller_model = controller_model,
        controller_prompts = controller_prompts,
        debug_prints = False
    ) 

    try:
        assistant_print_answers(
            run_data = assistant_run_data
        )
    except Exception as e:
        print(e)

    assistant_run_data['rag-metrics'] = assistant_requests[1]

    try:
        nested_stats = evaluation_nested_metrics(
            run_data = assistant_run_data,
            root_keys = summary_root_keys,
            target_keys = summary_target_keys,
            relevant_key_columns = summary_relevant_key_columns,
            wanted_stats = summary_wanted_stats,
            key_group_column = summary_key_group_column
        )


        assistant_run_data['stats'] = assistant_run_data['stats'] | nested_stats
    except Exception as e:
        print(e)

    return assistant_run_data
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
    
    root = ET.Element(wrapper_tag)
    for j, result in enumerate(query_results):
        for i, point in enumerate(result, 1):
            query_payload = point.payload

            chunk_attributes = {}
            chunk_attributes['rank'] = str(i)
            
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
            #collected_context.append(query_content)
            content_elem.text = str(f'{query_content.replace('\n','').replace('\r','')}')
        
    raw_xml = ET.tostring(root, encoding="utf-8")
    parsed_xml = minidom.parseString(raw_xml)
    
    # Pretty-print and strip the default <?xml version="1.0"?> declaration header
    formatted_xml = parsed_xml.toprettyxml(indent="")
    xml_lines = formatted_xml.splitlines()
    
    if xml_lines and xml_lines[0].startswith("<?xml"):
        xml_lines = xml_lines[1:]

    formatted_context = "\n".join(xml_lines)
    return formatted_context
            
def assistant_create_requests( 
    mlflow_client: any,
    qdrant_client: any,
    dataset_ids: list,
    prompts: dict,
    collection_name: str,
    query_type: str, 
    relevance_threshold: float,
    query_limit: int,
    fusion_limit: int,
    dense_model: any,
    sparse_model: any,
    batch_size: int
):
    try:
        import re
        from ..mlflow.use import mlflow_get_dataset, mlflow_get_prompt
        from ..rag.utility import rag_batch_query
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)
    
    request_index = 0
    prompt_variant_index = {}
    inference_requests = []
    for dataset_id in dataset_ids:
        dataset_df = mlflow_get_dataset(
            mlflow_client = mlflow_client,
            dataset_id = dataset_id
        )  

        for row in dataset_df.to_dict(orient = 'records'):
            for name, metadata in prompts.items():
                inputs_data = row['inputs']
                expectations_data = row['expectations']
                query_text = inputs_data['question']
                query_weights = expectations_data['weights']

                prompt_replacements = {
                    'query': query_text
                }
                
                if 'rag' in name:
                    text_query_batch = [query_text]
                    batch_query_results = rag_batch_query(
                        qdrant_client = qdrant_client,
                        query_type = query_type,
                        collection_name = collection_name,
                        text_query_batch = text_query_batch, 
                        relevant_weights_batch = query_weights,
                        relevance_threshold = relevance_threshold,
                        query_limit = query_limit,
                        fusion_limit = fusion_limit,
                        dense_model = dense_model,
                        sparse_model = sparse_model,
                        batch_size = batch_size
                    )
                    
                    prompt_replacements['content'] = assistant_format_context(
                        query_results = batch_query_results['results'],
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

                filled_prompt = mlflow_get_prompt(
                    mlflow_client = mlflow_client,
                    prompt_name = name,
                    prompt_version = metadata['version'],
                    prompt_replacements = prompt_replacements
                )

                prompt_variant = name.split('-')[1]
                if not prompt_variant in prompt_variant_index:
                    prompt_variant_index[prompt_variant] = 1

                for i in range(0, metadata['amount']):
                    filled_prompt['metadata'] = {
                        'dataset-id': dataset_id,
                        'part': expectations_data['part'],
                        'chapter': expectations_data['chapter'],
                        'idx': expectations_data['idx'],
                        'characters': expectations_data['characters'],
                        'relevance': expectations_data['relevance'],
                        'weights': expectations_data['weights'],
                        'prompt-variant': prompt_variant,
                        'request-index': request_index,
                        'variant-index': prompt_variant_index[prompt_variant]
                    }

                    for prompt in filled_prompt['prompt']:
                        key_name = f'{prompt['role']}-prompt-length'
                        filled_prompt['metadata'][key_name] = len(prompt['content'])
                    
                    prompt_variant_index[prompt_variant] += 1
                    inference_requests.append(filled_prompt)
                    request_index += 1

    return inference_requests

def assistant_send_answers(
    dataset_inference_requests: list,
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
    for inference_request in dataset_inference_requests:
        execution_time_start = t.time()
        
        dataset_name = inference_request['dataset-name']
        request_index = inference_request['request-index']
        question_type = inference_request['question-type']
        assistant_variant = inference_request['assistant-variant']
        assistant_index = inference_request['assistant-index']
        
        system_prompt_length = inference_request['system-prompt-length']
        user_prompt_length = inference_request['user-prompt-length']
        target_model = inference_request['target-model']
        used_context = system_prompt_length + user_prompt_length

        print('Assistant request:')
        print(f'Request|{request_index + 1}')
        print(f'Question type|{question_type}')
        print(f'Assistant variant|{assistant_variant}')

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
            "assistant-request": inference_request,
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
        if 'messages' in inference_request and inference_request['messages']:
            user_message_content = inference_request['messages'][-1].get('content', '')
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
            sent_request = inference_request
        )

        record["assistant-data"] = {
            "request": inference_request,
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
'''
def assistant_print_answers(
    run_data: dict
):  
    records = run_data.get("records", [])
    print(f"START ANSWERS | Total Records: {len(records)}\n")

    for idx, record in enumerate(records, start=1):
        meta = record.get("metadata")
        assistant_data = record.get("assistant-data")
        print(f"=== Record {idx}/{len(records)} ===")
        print(f"Status|{record['status']}")
        if record["refusal-reason"]:
            print(f"Refusal Reason|{record['refusal-reason']}")

        print(f"Dataset|{meta['dataset']}")
        print(f"Request|{meta['request-index'] + 1}")
        print(f"Question Type|{meta['question-type']}")
        print(f"Assistant Variant|{meta['assistant-variant']}")
        print(f"Assistant Index|{meta['assistant-index']}")
        if 0 < len(assistant_data):
            print(f"Model|{assistant_data.get('metrics').get('used-model')}")
        else:
            print(f"Model|None")
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
            used_model = ctrl_in['metrics']['used-model']
            print("Controller Input Check Result:")
            print(f"  Model: {used_model}")
            print(f"  Output: {ctrl_in['output']}")
            print(f"  Behavior: {ctrl_in['behavior']}\n")

        # 3. Assistant Output
        print("Assistant Output:")
        print(assistant_data.get('output') or "None (Refused before generation)")
        print("----------")

        # 4. Controller Output Check (if ran)
        if record.get("controller-output-data"):
            ctrl_out = record["controller-output-data"]
            used_model = ctrl_out['metrics']['used-model']
            print("Controller Output Check Result:")
            print(f"  Model: {used_model}")
            print(f"  Output: {ctrl_out['output']}")
            print(f"  Behavior: {ctrl_out['behavior']}\n")

        print("=" * 40 + "\n")
'''
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
            content_elem.text = str(f'{query_payload.get(content_key).replace('\n','').replace('\r','')}')
        collected_metrics.append({
            'batch-index': j,
            'batch-metrics': metrics
        })

    raw_xml = ET.tostring(root, encoding="utf-8")
    parsed_xml = minidom.parseString(raw_xml)
    
    # Pretty-print and strip the default <?xml version="1.0"?> declaration header
    formatted_xml = parsed_xml.toprettyxml(indent="")
    xml_lines = formatted_xml.splitlines()
    
    if xml_lines and xml_lines[0].startswith("<?xml"):
        xml_lines = xml_lines[1:]

    formatted_context = "\n".join(xml_lines)
    return formatted_context, collected_metrics
            
def assistant_create_requests( 
    target_df: any,
    prompt_parameters: any,
    dataset_name: str,
    target_model: str,
    data_ratio: any,
    join_prompts: bool,
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    query_limit: int,
    fusion_limit: int,
    dense_model: any,
    sparse_model: any,
    batch_size: int
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
    question_type_idx = {}
    for _, row in target_df.iterrows(): 
       
        replacer_dict = {
            'QUERY': row['question']
        }
        for data_type, wanted_amount in data_ratio.items():
            if not data_type in question_type_idx:
                question_type_idx[data_type] = 0 
            
            system_prompt = prompt_parameters[data_type]['system-prompt']
            user_template = prompt_parameters[data_type]['user-template']
            
            temperature = prompt_parameters[data_type]['temperature'][target_model]
            top_p = prompt_parameters[data_type]['top-p'][target_model]
            max_tokens = prompt_parameters[data_type]['max-tokens'][target_model]

            if 'rag' in data_type:
                text_query_batch = [row['question']]
                batch_query_results = search_monitored_batch_query(
                    qdrant_client = qdrant_client,
                    query_type = query_type, 
                    collection_name = collection_name,
                    text_query_batch = text_query_batch, 
                    relevant_weights_batch = [],
                    query_limit = query_limit,
                    fusion_limit = fusion_limit,
                    dense_model = dense_model,
                    sparse_model = sparse_model,
                    batch_size = batch_size
                )
                # idx is neededd for RAG ranking
                # Remembe to consider the general case
                formatted_context, batch_metrics = assistant_format_context(
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
                # It is most likely easiest to simply put the payload
                # We might be able to ranking here if calculate relevant
                # weights batch for factual and synthesis during the generation
                # and add them into the dataset
                rag_metrics.append({
                    'case-index': request_idx,
                    'question-type': data_type,
                    'query-batch': text_query_batch,
                    'batch-metrics': batch_metrics
                })
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
                    'question-type': data_type,
                    'question-index': question_type_idx[data_type],
                    'messages': sent_messages,
                    'system-prompt-length': system_prompt_length,
                    'user-prompt-length': user_prompt_length,
                    'target-model': target_model,
                    'temperature': temperature,
                    'top-p': top_p,
                    'max-tokens': max_tokens
                })
                question_type_idx[data_type] += 1
        request_idx += 1
    print(f'Amount of requests: {len(inference_requests)}')
    return inference_requests, rag_metrics

def assistant_generate_answers(
    dataset_inference_requests: list,
    request_keys: dict,
    length_limit: int,
    inference_parameters: any,
    controller_model: str,
    controller_prompts: any,
    request_categories: list,
    debug_prints: bool
) -> dict:
    try:
        import statistics
        import time as t
        from ..controller.use import controller_create_request
        from ..assistant.utility import assistant_run_inference
        from ..controller.utility import controller_extract_output
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)
    process_time_start = t.time()
    print('Getting answers')
    print(f'Request length limit {length_limit}')
    print('')
    run_data = {
        'requests': {
            'assistant': {
                'accept': [],
                'refuse': []
            },
            'controller': {
                'input': {
                    'accept': [],
                    'refuse': []
                },
                'output': {
                    'accept': [],
                    'refuse': []
                }
            }
        },
        'outputs': {
            'assistant': {
                'accept': [],
                'refuse': {
                    'guard': [],
                    'model': []
                }
            },
            'controller': {
                'input': {
                    'accept': [],
                    'refuse': []
                },
                'output': {
                    'accept': [],
                    'refuse': []
                }
            }
        },
        'metrics': {
            'assistant': {
                'accept': [],
                'refuse': []
            },
            'controller': {
                'input': {
                    'accept': [],
                    'refuse': []
                },
                'output': {
                    'accept': [],
                    'refuse': []
                }
            }
        },
        'request-times': {
            'assistant': {
                'accept': [],
                'refuse': []
            },
            'controller': {
                'input': {
                    'accept': [],
                    'refuse': []
                },
                'output': {
                    'accept': [],
                    'refuse': []
                }
            }
        },
        'prompt-lengths':{
            'system': [],
            'user': []
        },
        'execution-times': [],
        'stats': {}
    }

    # The end dataset also required input for double checking
    # There should be columns for messages
    for inference_requests in dataset_inference_requests:
        execution_time_start = t.time()
        assistant_request = {}
        dataset_name = inference_requests['dataset-name']
        case_index = inference_requests['case-index'] + 1
        question_type = inference_requests['question-type']
        question_index = inference_requests['question-index']
        category_type = request_categories[question_index]
        question_index = question_index + 1
        
        system_prompt_length = inference_requests['system-prompt-length']
        user_prompt_length = inference_requests['user-prompt-length']
        target_model = inference_requests['target-model']
        temperature = inference_requests['temperature']
        top_p = inference_requests['top-p']
        max_tokens = inference_requests['max-tokens']

        if user_prompt_length < length_limit:
            if 0 < system_prompt_length:
                run_data['prompt-lengths']['system'].append(system_prompt_length)
            if 0 < user_prompt_length:
                run_data['prompt-lengths']['user'].append(user_prompt_length)

            print('Assistant print:')
            print(f'Dataset|{dataset_name}')
            print(f'Case|{case_index}')
            print(f'Question type|{question_type}')
            print(f'Question index|{question_index}')
            print(f'Category|{category_type}')
            print(f'System prompt length|{system_prompt_length}')
            print(f'User prompt length|{user_prompt_length}')
            print(f'Model|{target_model}')
            print(f'Temperature|{temperature}')
            print(f'Top-p|{top_p}')
            print(f'Max tokens|{max_tokens}') 
            print('')

            for key in request_keys:
                assistant_request[key] = inference_requests[key]

            answer_metadata = {
                'dataset': dataset_name,
                'case-index': case_index,
                'question-type': question_type,
                'question-index': question_index,
                'category': category_type,
                'system-prompt-length': system_prompt_length,
                'user-prompt-length': user_prompt_length,
            }

            input_behavior = {
                'reasoning': '', 
                'secret-leak': 0, 
                'off-topic': 0
            }
            user_question = ''
            if 'pe-rag-bc-eval' in question_type:
                user_message_content = assistant_request['messages'][-1]['content']
                _, sep, after_tag = user_message_content.partition('### USER REQUEST:')
                user_question = after_tag.strip()
                # This only gets questions
                controller_input_check_request = controller_create_request(
                    case_index = case_index,
                    question_index = question_index,
                    assistant_input = user_question,
                    assistant_output = '',
                    prompt_parameters = controller_prompts,
                    dataset_name = dataset_name,
                    target_model = controller_model,
                    prompt_type = 'controller-input-eval',
                    join_prompts = False
                )
    
                print('Controller prints:')
                print(f'Question type|{controller_input_check_request['question-type']}')
                print(f'System prompt length|{controller_input_check_request['system-prompt-length']}')
                print(f'User prompt length|{controller_input_check_request['user-prompt-length']}')
                print(f'Model|{controller_model}')
                print(f'Temperature|{controller_input_check_request['temperature']}')
                print(f'Top-p|{controller_input_check_request['top-p']}')
                print(f'Max tokens|{controller_input_check_request['max-tokens']}') 
                print('')

                controller_inference_tuple = assistant_run_inference(
                    inference_address = inference_parameters['controller']['address'],
                    inference_path = inference_parameters['controller']['path'],
                    sent_request = controller_input_check_request
                )

                controller_output = controller_inference_tuple[0]
                input_behavior = controller_extract_output(
                    output = controller_output
                )

                print('Controller input check:')
                try:
                    print(f'Reasoning|{input_behavior['reasoning']}') 
                    print(f'Secret leak|{input_behavior['secret-leak']}') 
                    print(f'Off topic|{input_behavior['off-topic']}') 
                    print('')
                except Exception as e:
                    input_behavior = {
                        'reasoning': 'Malformed JSON returned by guardrail',  
                        'secret-leak': 0, 
                        'off-topic': 0
                    }
                    
                controller_merged_data = answer_metadata | controller_inference_tuple[1]
                if input_behavior['secret-leak'] == 1 or input_behavior['off-topic'] == 1:
                    run_data['outputs']['controller']['input']['refuse'].append(controller_output)
                    run_data['requests']['controller']['input']['refuse'].append(controller_input_check_request)
                    run_data['metrics']['controller']['input']['refuse'].append(controller_merged_data)
                    run_data['request-times']['controller']['input']['refuse'].append(controller_inference_tuple[2])
                else:
                    run_data['outputs']['controller']['input']['accept'].append(controller_output)
                    run_data['requests']['controller']['input']['accept'].append(controller_input_check_request)
                    run_data['metrics']['controller']['input']['accept'].append(controller_merged_data)
                    run_data['request-times']['controller']['input']['accept'].append(controller_inference_tuple[2])

            if input_behavior['secret-leak'] == 0 and input_behavior['off-topic'] == 0:
                assistant_inference_tuple = assistant_run_inference(
                    inference_address = inference_parameters['assistant']['address'],
                    inference_path = inference_parameters['assistant']['path'],
                    sent_request = assistant_request
                )
                
                assistant_merged_data = answer_metadata | assistant_inference_tuple[1]
                #run_data['outputs']['assistant']['response'].append(assistant_inference_tuple[0])
                if not 'pe-rag-bc-eval' in question_type:
                    run_data['requests']['assistant']['accept'].append(inference_requests)
                    run_data['outputs']['assistant']['accept'].append(assistant_inference_tuple[0])
                    run_data['metrics']['assistant']['accept'].append(assistant_merged_data)
                    run_data['request-times']['assistant']['accept'].append(assistant_inference_tuple[2])
                else:
                    assistant_output = assistant_inference_tuple[0]

                    controller_output_check_request = controller_create_request(
                        case_index = case_index,
                        question_index = question_index,
                        assistant_input = user_question,
                        assistant_output = assistant_output,
                        prompt_parameters = controller_prompts,
                        dataset_name = dataset_name,
                        target_model = controller_model,
                        prompt_type = 'controller-output-eval',
                        join_prompts = False
                    )

                    print('')
                    print(f'Question type|{controller_output_check_request['question-type']}')
                    print(f'System prompt length|{controller_output_check_request['system-prompt-length']}')
                    print(f'User prompt length|{controller_output_check_request['user-prompt-length']}')
                    print(f'Model|{controller_model}')
                    print(f'Temperature|{controller_output_check_request['temperature']}')
                    print(f'Top-p|{controller_output_check_request['top-p']}')
                    print(f'Max tokens|{controller_output_check_request['max-tokens']}') 
                    print('')

                    controller_inference_tuple = assistant_run_inference(
                        inference_address = inference_parameters['controller']['address'],
                        inference_path = inference_parameters['controller']['path'],
                        sent_request = controller_output_check_request
                    )
    
                    controller_output = controller_inference_tuple[0]
                    controller_merged_data = answer_metadata | controller_inference_tuple[1]
                    
                    output_behavior = controller_extract_output(
                        output = controller_output
                    )
    
                    print('Controller output check:')
                    try:
                        print(f'Reasoning|{output_behavior['reasoning']}') 
                        print(f'Irrelevant|{output_behavior['irrelevant']}') 
                        print(f'Verbose|{output_behavior['verbose']}') 
                        print(f'Out of scope|{output_behavior['out-of-scope']}') 
                    except Exception as e:
                        output_behavior ={
                            'reasoning': 'Malformed JSON returned by guardrail', 
                            'irrelevant': 0,
                            'verbose': 0,
                            'out-of-scope': 0
                        }

                    if output_behavior['irrelevant'] == 0 and output_behavior['verbose'] == 0 and output_behavior['out-of-scope'] == 0:
                        run_data['requests']['assistant']['accept'].append(inference_requests)
                        run_data['outputs']['assistant']['accept'].append(assistant_inference_tuple[0])
                        run_data['metrics']['assistant']['accept'].append(assistant_merged_data)
                        run_data['request-times']['assistant']['accept'].append(assistant_inference_tuple[2])

                        run_data['outputs']['controller']['output']['accept'].append(controller_output)
                        run_data['requests']['controller']['output']['accept'].append(controller_output_check_request)
                        run_data['metrics']['controller']['output']['accept'].append(controller_merged_data)
                        run_data['request-times']['controller']['output']['accept'].append(controller_inference_tuple[2])
                    else:
                        output_control_output = '[REFUSAL'
                        if output_behavior['irrelevant'] == 1:
                            output_control_output += ' - IRRELEVANT'
                        if output_behavior['verbose'] == 1:
                            output_control_output += ' - VERBOSE'
                        if output_behavior['out-of-scope'] == 1:
                            output_control_output += ' - OUT OF SCOPE'
                        output_control_output += ']'
                        run_data['requests']['assistant']['refuse'].append(inference_requests)
                        run_data['outputs']['assistant']['refuse']['guard'].append(output_control_output)
                        run_data['outputs']['assistant']['refuse']['model'].append(assistant_inference_tuple[0])
                        run_data['metrics']['assistant']['refuse'].append(assistant_merged_data)
                        run_data['request-times']['assistant']['refuse'].append(assistant_inference_tuple[2])

                        run_data['outputs']['controller']['output']['refuse'].append(controller_output)
                        run_data['requests']['controller']['output']['refuse'].append(controller_output_check_request)
                        run_data['metrics']['controller']['output']['refuse'].append(controller_merged_data)
                        run_data['request-times']['controller']['output']['refuse'].append(controller_inference_tuple[2])
            else:
                input_control_output = '[REFUSAL'
                if input_behavior['secret-leak'] == 1:
                    input_control_output += ' - SECRET LEAK'
                if input_behavior['off-topic'] == 1:
                    input_control_output += ' - OFF TOPIC'
                input_control_output += ']'

                run_data['requests']['assistant']['refuse'].append(inference_requests)
                run_data['outputs']['assistant']['refuse']['guard'].append(input_control_output)
                run_data['outputs']['assistant']['refuse']['model'].append('None')
                run_data['metrics']['assistant']['refuse'].append({})
                run_data['request-times']['assistant']['refuse'].append(0)
        execution_end_time = t.time()
        execution_total_time = round(execution_end_time-execution_time_start,5)
        run_data['execution-times'].append(execution_total_time)
        print(f'Spent seconds on execution: {execution_total_time}')
        print('')

    for key, value in run_data['prompt-lengths'].items():
        max_prompt_length = max(value)
        min_prompt_length = min(value)
        mean_prompt_length = statistics.mean(value)
        median_prompt_length = statistics.median(value)
        print(f'Prompt role|{key}')
        print(f'Max prompt length|{max_prompt_length}')
        print(f'Min prompt length|{min_prompt_length}')
        print(f'Mean prompt length|{mean_prompt_length}')
        print(f'Median prompt length|{median_prompt_length}')
        stat_key = f'{key}-prompt'
        run_data['stats'][stat_key] = {
            'max': max_prompt_length,
            'min': min_prompt_length,
            'mean': mean_prompt_length,
            'median': median_prompt_length
        }

    process_end_time = t.time()
    process_total_time = round(process_end_time-process_time_start,5)
    print(f'Spent seconds on processing: {process_total_time}')
    print('') 
    run_data['stats']['process-total-time'] = process_total_time
    return run_data

def assistant_print_answers(
    run_data: dict
):  
    cases = [
        'accept',
        'refuse'
    ]

    for case in cases:
        idx = 0
        controller_input_idx = 0
        controller_output_idx = 0
        assistant_refuse_idx = 0
        print('START ANSWERS')
        print(f'Case|{case}')
        run_data_amount = run_data['requests']['assistant'][case]
        print(f'Amount|{len(run_data_amount)}')
        for assistant_request in run_data_amount:
            assistant_metrics = run_data['metrics']['assistant'][case][idx]
            
            dataset_name = assistant_request['dataset-name']
            case_index = assistant_request['case-index']
            question_type = assistant_request['question-type']
            question_index = assistant_request['question-index']
            category_type = assistant_metrics['category']
            question_index = question_index  + 1
            system_prompt_length = assistant_request['system-prompt-length']
            user_prompt_length = assistant_request['user-prompt-length']
            target_model = assistant_request['target-model']
            temperature = assistant_request['temperature']
            top_p = assistant_request['top-p']
            max_tokens = assistant_request['max-tokens']

            print(f'Dataset|{dataset_name}')
            print(f'Case|{case_index}')
            print(f'Question type|{question_type}')
            print(f'Question index|{question_index}')
            print(f'Category|{category_type}')
            print(f'System prompt length|{system_prompt_length}')
            print(f'User prompt length|{user_prompt_length}')
            print(f'Model|{target_model}')
            print(f'Temperature|{temperature}')
            print(f'Top-p|{top_p}')
            print(f'Max tokens|{max_tokens}') 
            print('==========')
            # Show format and type
            print('Assistant prompts')
            messages = assistant_request['messages']
            for message in messages:
                prompt_role = message['role']
                prompt_content = message['content']
                print(f'Role|{prompt_role}')
                print('Prompt:')
                print(prompt_content)

            if 'bc-eval' in question_type:
                print('Controller input check prompts:')
                try:
                    messages = run_data['requests']['controller']['input'][case][controller_input_idx]['messages']
                    for message in messages:
                        prompt_role = message['role']
                        prompt_content = message['content']
                        print(f'Role|{prompt_role}')
                        print('Prompt:')
                        print(prompt_content) 

                    controller_input_check = run_data['outputs']['controller']['input'][case][controller_input_idx]

                    print('==========')
                    print('Controller input result:')
                    print(controller_input_check)
                    controller_input_idx += 1
                except Exception as e:
                    pass

            print('==========')
            print('Assistant output:')
            if case == 'refuse':
                print('Guard response:')
                assistant_output = run_data['outputs']['assistant'][case]
                #print(assistant_output)
                print(assistant_output['guard'][assistant_refuse_idx])
                print('Model response:')
                print(assistant_output['model'][assistant_refuse_idx])
                assistant_refuse_idx += 1
            else:
                assistant_output = run_data['outputs']['assistant'][case][idx]
                print(assistant_output)

            print('==========')
            if 'bc-eval' in question_type:
                print('Controller output check prompts:')
                try:
                    messages = run_data['requests']['controller']['output'][case][controller_output_idx]['messages']
                    for message in messages:
                        prompt_role = message['role']
                        prompt_content = message['content']
                        print(f'Role|{prompt_role}')
                        print('Prompt:')
                        print(prompt_content) 

                    controller_output_check = run_data['outputs']['controller']['output'][case][controller_output_idx]
                    print('==========')
                    print('Controller output result:')
                    print(controller_output_check)
                    controller_output_idx += 1
                except Exception as e:
                    pass
            print('')
            idx += 1

def assistant_produce_answers(
    target_df: any,
    assistant_prompts: dict,
    dataset_name: str,
    assistant_model: str,
    data_ratio: dict,
    join_prompts: bool,
    qdrant_client: any,
    query_type: str,
    collection_name: str,
    query_limit: int,
    fusion_limit: int,
    dense_model: any,
    sparse_model: any,
    batch_size: int,
    request_keys: list,
    length_limit: int,
    inference_parameters: any,
    controller_model: str,
    controller_prompts: dict,
    category_column: str
):
    try:
        from ..assistant.use import assistant_create_requests, assistant_generate_answers, assistant_print_answers
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    request_tuple = assistant_create_requests(
        target_df = target_df,
        prompt_parameters = assistant_prompts,
        dataset_name = dataset_name,
        target_model = assistant_model,
        data_ratio = data_ratio,
        join_prompts = join_prompts,
        qdrant_client = qdrant_client,
        query_type = query_type, 
        collection_name = collection_name,
        query_limit = query_limit,
        fusion_limit = fusion_limit,
        dense_model = dense_model,
        sparse_model = sparse_model,
        batch_size = batch_size
    )

    run_data = assistant_generate_answers(
        dataset_inference_requests = request_tuple[0],
        request_keys = request_keys,
        length_limit = length_limit,
        inference_parameters = inference_parameters,
        controller_model = controller_model,
        controller_prompts = controller_prompts,
        request_categories = target_df[category_column],
        debug_prints = False
    ) 
    try:
        assistant_print_answers(
            run_data = run_data
        )
    except Exception as e:
        pass

    run_data['rag-metrics'] = request_tuple[1]
    
    return run_data
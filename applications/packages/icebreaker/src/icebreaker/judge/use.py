def judge_create_requests(
    rag_dataset: any,
    truth_dataset: any,
    run_data: any,
    prompt_parameters: any,
    dataset_name: str,
    target_model: str,
    prompt_type: str,
    question_column: str,
    answer_column: str,
    join_prompts: bool
) -> list:
    try:
        import re
    except ImportError as e:
        raise ImportError("judge/use failed to import", e)
 
    print('Creating judge requests')
    inference_requests = []

    run_data_records = run_data['records']
    judge_idx = 0
    for record in run_data_records:
        assistant_data = record['assistant-data']

        if 0 < len(assistant_data):
            assistant_variant = assistant_data['request']['assistant-variant']
            judged_model_metrics = assistant_data['metrics']
            question_type = assistant_data['request']['question-type']
            request_idx = assistant_data['request']['request-index']
            output_text = assistant_data['output'] 
            
            target_text = truth_dataset[answer_column][request_idx]
            query_text = truth_dataset[question_column][request_idx]

            replacer_dict = {
                'TARGET': target_text,
                'QUERY': query_text,
                'OUTPUT': output_text
            }

            if 'synthetic' in prompt_type:
                chunk_idx = truth_dataset['chunk-idx'][request_idx]
                replacer_dict['CONTENT'] = rag_dataset['content'][chunk_idx]

            temperature = prompt_parameters[prompt_type]['temperature'][target_model]
            top_p = prompt_parameters[prompt_type]['top-p'][target_model]
            max_tokens = prompt_parameters[prompt_type]['max-tokens'][target_model]

            system_prompt = prompt_parameters[prompt_type]['system-prompt']
            user_template = prompt_parameters[prompt_type]['user-template']
            
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
            
            used_question_type = f'{assistant_variant}-{question_type}-{prompt_type}'
            inference_requests.append({
                'dataset-name': dataset_name,
                'request-index': request_idx,
                'question-type': used_question_type,
                'judge-index': judge_idx,
                'messages': sent_messages,
                'system-prompt-length': system_prompt_length,
                'user-prompt-length': user_prompt_length,
                'judged-model-metrics': judged_model_metrics,
                'target-model': target_model,
                'temperature': temperature,
                'top-p': top_p,
                'max-tokens': max_tokens
            })
        judge_idx += 1
    print(f'Amount of requests: {len(inference_requests)}')
    return inference_requests

def judge_generate_answers(
    dataset_inference_requests: list,
    char_to_token_ratio: float,
    length_limit: int,
    inference_parameters: any,
    debug_prints: bool
) -> dict:
    try:
        import time as t
        from ..ray.utility import ray_run_inference
        from ..judge.utility import judge_extract_output
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)
    
    process_time_start = t.time()
    print('Getting answers')
    token_limit = char_to_token_ratio * length_limit
    print(f'Request token limit {token_limit}\n')
    print('')
    
    run_records = []
    for inference_request in dataset_inference_requests:
        execution_time_start = t.time()

        dataset_name = inference_request['dataset-name']
        request_index = inference_request['request-index']
        question_type = inference_request['question-type']
        judge_index = inference_request['judge-index']
        
        system_prompt_length = inference_request['system-prompt-length']
        user_prompt_length = inference_request['user-prompt-length']
        judged_model_metrics = inference_request['judged-model-metrics']
        target_model = inference_request['target-model']
        used_context = system_prompt_length + user_prompt_length

        print('Assistant request:')
        print(f'Request|{request_index + 1}')
        print(f'Question type|{question_type}')
        print(f'Context|{used_context}')

        record = {
            "metadata": {
                "dataset": dataset_name,
                "request-index": request_index,
                "question-type": question_type,
                'judge-index': judge_index,
                "system-prompt-length": system_prompt_length,
                "user-prompt-length": user_prompt_length,
                "judged-model-metrics": judged_model_metrics,
                "target-model": target_model
            },
            "status": "ACCEPTED", # ACCEPTED, REFUSED_CONTEXT
            "refusal-reason": None,
            "judge-data": {},
            "judge-request": inference_request,
            "execution-time-sec": 0.0
        }

        if token_limit <= used_context:
            record["status"] = "REFUSED_CONTEXT"
            record["refusal-reason"] = "CONTEXT_LIMIT_REACHED"
            record["execution-time-sec"] = round(t.time() - execution_time_start, 5)
            run_records.append(record)
            continue
        
        jdg_out, jdg_meta, jdg_time = ray_run_inference(
            inference_address = inference_parameters['judge']['address'],
            inference_path = inference_parameters['judge']['path'],
            sent_request = inference_request
        )

        jdg_score = judge_extract_output(output = jdg_out)

        record["judge-data"] = {
            "request": inference_request,
            "output": jdg_out,
            "score": jdg_score,
            "metrics": jdg_meta,
            "latency-sec": jdg_time
        }

        print("--- Judge Scores ---")
        try:
            print(f"Reasoning  : {jdg_score.get('reasoning', 'N/A')}")
            print(f"Correctness: {jdg_score.get('correctness', 'N/A')}")
            if "synth" in question_type:
                print(f"Faithfulness: {jdg_score.get('faithfulness', 'N/A')}")
            print(f"Relevance  : {jdg_score.get('relevance', 'N/A')}")
        except Exception as e:
            pass

        record["execution-time-sec"] = round(t.time() - execution_time_start, 5)
        run_records.append(record)

    total_process_time = round(t.time() - process_time_start, 5)
    print(f'Spent seconds on processing: {total_process_time}')
    print('') 

    return {
        "records": run_records,
        "stats": {
            "total-process-time-sec": total_process_time,
            "total-samples-evaluated": len(run_records)
        }
    }

def judge_print_answers(
    run_data: dict
):
    records = run_data.get('records', [])
    
    print(f"START JUDGE ANSWERS | Total records: {len(records)}")

    for idx, record in enumerate(records, start=1):
        # judge model
        metadata = record.get('metadata', {})
        judged_model_metrics = metadata.get('judged-model-metrics', {})
        judge_data = record.get('judge-data', {})
        judge_metrics = judge_data.get('metrics')
        
        judge_req = judge_data.get('request', {})
        score = judge_data.get('score')

        print(f"=== Sample {idx}/{len(records)} ===")
        print(f"Status | {record.get('status', 'unknown')}")
        if record.get('error'):
            print(f"Error | {record['error']}")

        print(f"Dataset | {metadata.get('dataset')}")
        print(f"Judged model | {judged_model_metrics.get('used-model')}")
        print(f"Request | {metadata.get('request-index')}")
        print(f"Question Type | {metadata.get('question-type')}")
        print(f"Question Index | {metadata.get('question-index', 0) + 1}")
        print(f"System Prompt Length | {metadata.get('system-prompt-length')}")
        print(f"User Prompt Length | {metadata.get('user-prompt-length')}")
        print(f"Judge model | {judge_metrics.get('used-model')}")
        print(f"Inference Latency | {record.get('execution-time-sec', 0.0)}s")
        print('==========')

        # Prompts
        print('Judge Prompts:')
        messages = judge_req.get('messages', [])
        if messages:
            for message in messages:
                print(f"  Role | {message.get('role')}")
                print('  Prompt:')
                print(f"    {message.get('content')}\n")
        else:
            print('  No message list available.')

        print('==========')
        print('Raw Judge Output:')
        print(judge_data.get('output') or 'N/A')

        print('==========')
        print('Parsed Scores:')
        if score:
            for key, val in score.items():
                print(f"  {key}: {val}")
        else:
            print('  No scores available.')

        print('=' * 40 + '\n')

def judge_produce_answers(
    rag_dataset: any,
    truth_dataset: any,
    assistant_run_data: any,
    judge_prompts: any,
    dataset_name: str,
    target_model: str,
    prompt_type: str,
    question_column: str,
    answer_column: str,
    join_prompts: bool,
    char_to_token_ratio: float,
    length_limit: int,
    inference_parameters: any,
    summary_root_keys: dict,
    summary_target_keys: list,
    summary_relevant_key_columns: dict,
    summary_wanted_stats: list,
    summary_key_group_column: dict
):
    try:
        from ..judge.use import judge_create_requests, judge_generate_answers, judge_print_answers
        from ..evaluation.use import evaluation_nested_metrics
    except ImportError as e:
        raise ImportError("assistant/use failed to import", e)

    judge_requests = judge_create_requests(
        rag_dataset = rag_dataset,
        truth_dataset = truth_dataset,
        run_data = assistant_run_data,
        prompt_parameters = judge_prompts,
        dataset_name = dataset_name,
        target_model = target_model,
        prompt_type = prompt_type,
        question_column = question_column,
        answer_column = answer_column,
        join_prompts = join_prompts
    )

    judge_run_data = judge_generate_answers(
        dataset_inference_requests = judge_requests,
        char_to_token_ratio = char_to_token_ratio,
        length_limit = length_limit,
        inference_parameters = inference_parameters,
        debug_prints = False
    )
    
    try:
        judge_print_answers(
            run_data = judge_run_data 
        )
    except Exception as e:
        print('print')
        print(e)

    try:
        nested_stats = evaluation_nested_metrics(
            run_data = judge_run_data,
            root_keys = summary_root_keys,
            target_keys = summary_target_keys,
            relevant_key_columns = summary_relevant_key_columns,
            wanted_stats = summary_wanted_stats,
            key_group_column = summary_key_group_column
        )
        
        judge_run_data['stats'] = judge_run_data['stats'] | nested_stats
    except Exception as e:
        print('stats')
        print(e)

    return judge_run_data 
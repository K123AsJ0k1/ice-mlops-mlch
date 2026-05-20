
def notebook_parse_file(
    repository_path: str,
    file_path: str
):
    try:
        import nbformat
        from .markdown_parse import markdown_parse_content
    except ImportError as e:
        raise ImportError("Failed to import", e)

    with open(file_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    parsed_material = []

    markdown_content = ""
    for cell in nb.cells:
        if cell.cell_type == 'markdown':
            markdown_content += cell.source + "\n\n"
        elif cell.cell_type == 'code':
            block_type = '```python'
            cell_code = cell.source
            if '!' in cell_code:
                block_type = '```bash'
            if '%' in cell_code:
                block_type = '```ipython'
            
            markdown_content += f'{block_type}\n{cell_code}\n```\n\n'
            
            output_texts = []
            for output in cell.get('outputs', []):
                if output.output_type == 'stream':
                    output_texts.append("".join(output.text))
                if output.output_type in ['execute_result', 'display_data']:
                    if 'text/plain' in output.data:
                        output_texts.append("".join(output.data['text/plain']))
            
            if 0 < len(output_texts):
                block_type = '```output'
                output_text = '\ņ'.join(output_texts)
                markdown_content += f'{block_type}\n'
                markdown_content += f'{output_text}'
                
                # There are some cases that have their own\n
                if output_text[-1:] == '\n':
                    markdown_content += f'```\n\n'
                else:
                    markdown_content += f'\n```\n\n'
                    
    parsed_material = markdown_parse_content(
        repository_path = repository_path,
        file_path = file_path,
        content = markdown_content
    )

    return parsed_material

def langchain_create_code_chunks(
    language: any,
    chunk_size: int,
    chunk_overlap: int,
    code: any
) -> any:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as e:
        raise ImportError("langchain/use failed to import", e)

    splitter = RecursiveCharacterTextSplitter.from_language(
        language = language,
        chunk_size = chunk_size, 
        chunk_overlap = chunk_overlap
    )

    code_chunks = splitter.create_documents([code])
    code_chunks = [doc.page_content for doc in code_chunks]
    return code_chunks

def langchain_create_text_chunks(
    chunk_size: int,
    chunk_overlap: int,
    text: any
) -> any:
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as e:
        raise ImportError("langchain/use failed to import", e)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size, 
        chunk_overlap = chunk_overlap,
        length_function = len,
        is_separator_regex = False
    )

    text_chunks = splitter.create_documents([text])
    text_chunks = [doc.page_content for doc in text_chunks]
    return text_chunks

def langchain_create_chunks(
    data_parameters: any,
    database: str,
    collection: str,
    id: str,
    type: str,
    data: any
):
    try:
        from langchain_text_splitters import Language
        from ..langchain.use import langchain_create_code_chunks, langchain_create_text_chunks
    except ImportError as e:
        raise ImportError("langchain/use failed to import", e)

    chunks = []
    try:
        created_chunks = []
        if type == 'python':
            used_configuration = data_parameters[type]
            created_chunks = langchain_create_code_chunks(
                language = Language.PYTHON,
                chunk_size = used_configuration['chunk-size'],
                chunk_overlap = used_configuration['chunk-overlap'],
                code = data
            )
        if type == 'text' or type == 'yaml' or type == 'markdown':
            used_configuration = data_parameters[type]
            created_chunks = langchain_create_text_chunks(
                chunk_size = used_configuration['chunk-size'],
                chunk_overlap = used_configuration['chunk-overlap'],
                text = data
            )
            
        for chunk in created_chunks:
            if chunk.strip() and 2 < len(chunk):
                chunks.append(chunk)
    except Exception as e:
        print(database,collection,id,e)
    
    return chunks
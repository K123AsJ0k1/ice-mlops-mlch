import ray

@ray.remote(
    num_cpus = 1,
    memory = 0.2 * 1024 * 1024 * 1024
)
class Detector:
    def __init__(
        self,
        swift_parameters: any,
        model_parameters: any
    ):
        import tempfile
        import fasttext
        actor_swift_client = swift_setup_client(
            swift_parameters = swift_parameters
        )

        object_content = swift_get_object_content(
            swift_client = actor_swift_client,
            bucket_name = model_parameters['bucket-name'],
            object_path = model_parameters['object-path']
        ) 

        model_data = object_content['data']
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            temp_file.write(model_data)
            temp_file.flush()
            # The model is loaded directly into this Actor's private RAM
            self.model = fasttext.load_model(temp_file.name)
        
        from icebreaker.fast_text.use import fasttext_get_stats
        self.get_stats = fasttext_get_stats

    def batch_fasttext_stats(
        self,
        worker_index: int,
        actor_index: int,
        batch_index: int,
        used_key: str,
        text_input: list,
        analysis_parameters: any
    ) -> any:
        
        language_stats = self.get_stats(
            model = self.model,
            texts = text_input,
            default_value = analysis_parameters['language-default'],
            default_threshold = analysis_parameters['language-threshold'],
            label_replacer = analysis_parameters['language-replacer']
        )

        result = {
            'worker': worker_index,
            'actor': actor_index,
            'batch': batch_index,
            'key': used_key,
            'language-stats': language_stats
        }
        return result

        
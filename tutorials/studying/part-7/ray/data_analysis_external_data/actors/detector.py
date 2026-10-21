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
        from magika import Magika, PredictionMode
        from icebreaker.swift.setup import swift_setup_client
        from icebreaker.swift.use import swift_get_object_content

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
            self.ft_model = fasttext.load_model(temp_file.name)

        self.mk_model = Magika(prediction_mode = PredictionMode.MEDIUM_CONFIDENCE)
        
    def batch_get_stats(
        self,
        worker_index: int,
        actor_index: int,
        batch_index: int,
        used_key: str,
        language_text_input: list,
        format_text_input: list,
        analysis_parameters: any
    ) -> any:
        from icebreaker.fast_text.use import fasttext_get_data
        from icebreaker.mgka.use import magika_get_data

        result = {
            'worker': worker_index,
            'actor': actor_index,
            'batch': batch_index,
            'key': used_key,
        }

        result['language-data'] = fasttext_get_data( 
            model = self.ft_model,
            texts = language_text_input,
            default_label = analysis_parameters['language-default-label'],
            confidence_threshold = analysis_parameters['language-confidence-threshold'],
            label_replacer = analysis_parameters['language-label-replacer'],
            stat_mode = False
        )

        result['format-data'] = magika_get_data(
            model = self.mk_model,
            texts = format_text_input,
            default_label = analysis_parameters['format-default-label'],
            confidence_threshold = analysis_parameters['format-confidence-threshold'],
            label_replacer = analysis_parameters['format-label-replacer'],
            stat_mode = False
        ) 
        
        return result
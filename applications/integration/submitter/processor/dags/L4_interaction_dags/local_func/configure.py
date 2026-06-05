 
def configure_cloud_interaction(
    swift_parameters: str, 
    storage_parameters: str,
    process_parameters: str
):
    #try:
        #from interaction_dags.sub_func.configure import configure_cloud_interaction
    #except ImportError as e:
    #    raise ImportError("interaction-dags/configure failed to import", e)
    # This is single target, dags can make it multi target
    # This needs to use the provided controller env and input yaml
    # It then needs to use those details to replace files
    print('Configuration cloud interaction')

    #print(process_parameters)

    return None
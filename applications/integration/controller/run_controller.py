
# Make run with python3 run_controller.py --input ()/controller-input.yaml
if __name__ == "__main__":
    from setup_controller import setup_controller
    
    import argparse

    parser = argparse.ArgumentParser(description="Controller")
    
    parser.add_argument("--input", required = True, help="The absolute path to the controller input YAML")
    
    args = parser.parse_args()

    completion_state = setup_controller(
        input_path = args.input
    )
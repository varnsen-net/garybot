import os

# paths
_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
_REQUIRED_DIRS = ['user-logs', 'odds']


def startup(data_path:str, required_dirs:str) -> None:
    """Create required directories if they don't exist."""
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    for d in required_dirs:
        path = os.path.join(data_path, d)
        if not os.path.exists(path):
            os.mkdir(path)
    return


startup(_DATA_PATH, _REQUIRED_DIRS)

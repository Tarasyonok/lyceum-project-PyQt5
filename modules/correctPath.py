import os

def correct_path(path):
    if os.name == 'nt':
        return path
    else:
        return path.replace('/', '\\')
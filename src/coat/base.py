import os
from fabric.state import env

def get_local_base_dir():
    return os.path.dirname(os.path.abspath(env.real_fabfile))

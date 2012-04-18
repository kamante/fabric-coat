from __future__ import with_statement

import os
import re
import tempfile
import shutil

from datetime import datetime

from fabric.api import run, local, get, cd, lcd, put
from fabric.state import env
from fabric.operations import require
from fabric.contrib.console import confirm

from .base import get_local_base_dir, backup_create_local


__all__ = ("update_env", "deploy")


def update_env(*args, **kwargs):
    env.local_path = "public_html"
    env.update(kwargs)

    if 'local_base_dir' not in env:
        env.local_base_dir = get_local_base_dir()


def deploy():
    require('base_dir', provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    deploy_archive_dir = tempfile.mkdtemp()

    with lcd(env.local_base_dir):
        local('git archive master %s | tar -x -f- -C %s' % (env.local_path, deploy_archive_dir))

    if 'settings_file' in env:
        command = 'rsync -a --exclude config.php  %s/%s/* %s@%s:%s/%s'
    else:
        command = 'rsync -a %s/%s/* %s@%s:%s/%s'

    local(command %
          (deploy_archive_dir, env.local_path, env.user, env.host,
           env.base_dir, env.remote_path))

    with cd(os.path.join(env.base_dir, env.remote_path)):
        if env.settings_file:
            run('cp %s config.php' % env.settings_file)

    shutil.rmtree(deploy_archive_dir)

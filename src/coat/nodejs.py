from __future__ import with_statement

import os
import re
import tempfile
import time
import shutil

from datetime import datetime

from fabric.api import run, local, get, cd, lcd, put
from fabric.state import env
from fabric.operations import require
from fabric.contrib.console import confirm


__all__ = ("deploy",)

def deploy(revision="master"):
    require('base_dir', provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    deploy_archive_dir = tempfile.mkdtemp()

    with lcd(env.local_base_dir):
        local('git archive %s %s | tar -x -f- -C %s' % (revision, env.local_nodejs_path, deploy_archive_dir))

    local('rsync -avz -e "ssh -p %s" %s/%s* %s@%s:%s/versions/current/%s' %
          (env.port, deploy_archive_dir, env.local_nodejs_path, env.user, env.host,
           env.base_dir, env.nodejs_path))

    with cd(os.path.join(env.base_dir, 'versions', 'current', env.nodejs_path, env.local_nodejs_path)):
        run('npm install')

    shutil.rmtree(deploy_archive_dir)

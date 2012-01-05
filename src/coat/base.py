import os
import time
import shutil

from fabric.state import env
from fabric.api import local


def get_local_base_dir():
    return os.path.dirname(os.path.abspath(env.real_fabfile))


def backup_prune():
    if not env.backup_path:
        return

    backup_path = os.path.join(env.local_base_dir, env.backup_path)

    if not os.path.exists(backup_path):
        return

    wanted = []

    for entry in os.listdir(backup_path):
        if entry.startswith("."):
            continue

        absentry = os.path.join(backup_path, entry)

        if time.time() - os.path.getctime(absentry) > 43200: # XXX: Make expiry configurable
            wanted.append(absentry)

    for entry in wanted:
        shutil.rmtree(entry)


def backup_create_local(local_source):
    backup_prune()

    backup_target = os.path.join(env.local_base_dir,
                                 env.backup_path,
                                 env.backup_prefix)

    if os.path.isdir(local_source):
        backup_target = os.path.join(backup_target, local_source)

    local("mkdir -p %s" % backup_target)

    local("rsync -a --link-dest=%s "
            "%s "
            "%s" % (local_source, local_source, backup_target))

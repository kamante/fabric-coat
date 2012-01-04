from __future__ import with_statement
import os
import re
import tempfile
import shutil

from fabric.api import run, local, get, cd, lcd, settings, hide
from fabric.state import env
from fabric.operations import require

from .base import get_local_base_dir


__all__ = ("update_env", "download_uploads_from_remote",
           "download_database_from_remote", "update_database_from_remote",
           "deploy")


def update_env(*args, **kwargs):
    env.wordpress_path = "public_html"

    env.update(kwargs)

    if 'local_base_dir' not in env:
        env.local_base_dir = get_local_base_dir()


def parse_config_from_file(settings_file):
    lines = open(settings_file).read()

    define_re = re.compile(r"""define\(["'](?P<key>[^'"]+)["'],\s*["'](?P<value>[^'"]+)["']\)""", re.S | re.M)

    return dict(define_re.findall(lines))


def read_config():
    """
    Returns a dict of the current local and remote wordpress settings.
    """
    wordpress_path = os.path.join(env.local_base_dir, env.local_wordpress_path)

    return {
        'local': parse_config_from_file(os.path.join(wordpress_path, "wp-config.php")),
        'remote': parse_config_from_file(os.path.join(wordpress_path, env.settings_file))
    }


def download_uploads_from_remote():
    require("base_dir", provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    wp_config = read_config()

    with lcd(os.path.join(env.local_base_dir, env.local_wordpress_path)):
        local('rsync -a %s@%s:%s/%s/wp-content/uploads/ wp-content/uploads/' % (env.user, env.host, env.base_dir, env.wordpress_path))


def download_database_from_remote():
    require("base_dir", provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    wp_config = read_config()

    run("mysqldump -u%(DB_USER)s -p%(DB_PASSWORD)s -h%(DB_HOST)s --add-drop-table %(DB_NAME)s > /tmp/%(DB_USER)s.sql" % wp_config['remote'])
    get("/tmp/%(DB_USER)s.sql" % wp_config['remote'], os.path.join(env.local_base_path, env.local_wordpress_path, "%(DB_USER)s.sql" % wp_config['remote']))
    run("rm -f /tmp/%(DB_USER)s.sql" % wp_config['remote'])


def update_database_from_remote():
    require("base_dir", provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    wp_config = read_config()
    dump_file, _ = tempfile.mkstemp()

    run("mysqldump -u%(DB_USER)s -p%(DB_PASSWORD)s -h%(DB_HOST)s --add-drop-table %(DB_NAME)s > /tmp/%(DB_USER)s.sql" % wp_config['remote'])
    get("/tmp/%(DB_USER)s.sql" % wp_config['remote'], "%(DB_USER)s.sql" % wp_config['remote'])
    run("rm -f /tmp/%(DB_USER)s.sql" % wp_config['remote'])

    wp_config['local']['dump_file'] = dump_file

    local('mysql -u%(DB_USER)s -p%(DB_PASSWORD)s -h%(DB_HOST)s %(DB_NAME)s < %(dump_file)s' % wp_config['local'])

    os.unlink(dump_file)


def deploy():
    require('base_dir', provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    deploy_archive_dir = tempfile.mkdtemp()

    with lcd(env.local_base_dir):
        local('git archive master %s | tar -x -f- -C %s' % (env.local_wordpress_path, deploy_archive_dir))

    local('rsync -a --exclude wp-config.php --exclude wp-content/uploads/* %s/%s/* %s@%s:%s/%s' %
          (deploy_archive_dir, env.local_wordpress_path, env.user, env.host,
           env.base_dir, env.wordpress_path))

    with cd(os.path.join(env.base_dir, env.wordpress_path)):
        if env.settings_file:
            run('cp %s wp-config.php' % env.settings_file)

    shutil.rmtree(deploy_archive_dir)

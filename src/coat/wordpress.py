from __future__ import with_statement
import os
import re
import tempfile
import shutil

from fabric.api import run, local, get, cd, lcd, settings, hide
from fabric.state import env
from fabric.operations import require

#env.local_base_dir = os.path.dirname(os.path.abspath(__file__))

def get_wordpress_settings(settings_file):
    lines = open(os.path.join(env.local_base_dir, 'php', 'public_html', settings_file)).read()

    define_re = re.compile(r"""define\(["'](?P<key>[^'"]+)["'],\s*["'](?P<value>[^'"]+)["']\)""", re.S | re.M)

    return dict(define_re.findall(lines))


def update_from_remote():
    require('base_dir', provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    wp_settings = get_wordpress_settings(env.settings_file)
    local_wp_settings = get_wordpress_settings(os.path.join(env.local_base_dir, 'php', 'public_html', 'wp-config.php'))

    with lcd(os.path.join(env.local_base_dir, 'php', 'public_html')):
        local('rsync -a %s@%s:%s/public_html/wp-content/uploads/ wp-content/uploads/' % (env.user, env.host, env.base_dir))

    run('mysqldump -u%(DB_USER)s -p%(DB_PASSWORD)s -h%(DB_HOST)s --add-drop-table %(DB_NAME)s > /tmp/%(DB_USER)s.sql' % wp_settings)
    get('/tmp/%(DB_USER)s.sql' % wp_settings, '/tmp/%(path)s')
    run('rm -f /tmp/%(DB_USER)s.sql' % wp_settings)
    local_wp_settings['remote_file'] = '/tmp/%(DB_USER)s' % wp_settings

    local('mysql -u%(DB_USER)s -p%(DB_PASSWORD)s -h%(DB_HOST)s %(DB_NAME)s < %(remote_file)s.sql' % local_wp_settings)
    local('rm -f /tmp/%(DB_USER)s.sql' % wp_settings)


def deploy():
    require('base_dir', provided_by=("env_test", "env_live"),
            used_for='defining the deploy environment')

    deploy_archive_dir = tempfile.mkdtemp()

    with lcd(env.local_base_dir):
        local('git archive master php | tar -x -f- -C %s' % (deploy_archive_dir))

    local('rsync -a --exclude wp-config.php %s/php/* %s@%s:%s/' % (deploy_archive_dir, env.user, env.host, env.base_dir))

    if env.settings_file:
        with cd(os.path.join(env.base_dir, 'public_html')):
            run('cp %s wp-config.php' % env.settings_file)

            with settings(warn_only=True):
                with hide('stderr', 'stdout'):
                    run('chmod -R 777 wp-content/uploads/')
                    run('chmod -R 777 wp-content/themes/')

    shutil.rmtree(deploy_archive_dir)

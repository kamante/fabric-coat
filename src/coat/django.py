from __future__ import with_statement

import tempfile
import shutil

from fabric.api import run, local, cd, settings, lcd, prefix, hide
from fabric.operations import require
from fabric.state import env

from .base import get_local_base_dir


__all__ = ("update_env", "bootstrap", "deploy")


def update_env(*args, **kwargs):
    env.update_env = True
    env.migrate = True
    env.syncdb = True

    env.update(kwargs)

    env.versions_dir = env.base_dir + "/versions"

    if 'wsgi_file' in env:
        env.wsgi_file = env.django_appname + ".wsgi"

    if 'local_base_dir' not in env:
        env.local_base_dir = get_local_base_dir()


def copy_revision(current_revision, revision):
    # test remote for the revision and skip re-copying already
    # existing revisions
    with settings(hide("stdout", "stderr", "warnings"), warn_only=True):
        exists = run("test -d %s/%s && echo 1" % (env.versions_dir, revision))

    if exists == "1":
        return

    # create a local temp directory and export a version of revision there
    # and move files around
    archive_dir = tempfile.mkdtemp()
    with lcd(env.local_base_dir):
        local("git archive %s django static | tar -x -C %s" % (revision, archive_dir))

    if env.settings_file:
        with lcd("%s/django/%s" % (archive_dir, env.django_appname)):
            local("cp %s localsettings.py" % env.settings_file)

    # copy all of local onto remote using rsync, use hard links to save
    # space for unmodified files
    rsync_cmd = "%s/* %s@%s:%s/%s/" % (archive_dir, env.user, env.host, env.versions_dir, revision)
    if current_revision:
        with cd(env.versions_dir):
            run("rsync -a --link-dest=../%(cur)s/ %(cur)s/ %(new)s" %
                {'cur': current_revision, 'new': revision})

        local("rsync -a -c --delete %s" % (rsync_cmd))
    else:
        local("rsync -a %s" % rsync_cmd)

    shutil.rmtree(archive_dir)


def bootstrap():
    require("base_dir", "versions_dir", provided_by=("env_test", "env_live"),
            used_for="defining the deploy environment")

    run("test -d %(base_dir)s || mkdir -p %(base_dir)s" % {"base_dir": env.base_dir})
    run("test -d %(base_dir)s/env || virtualenv --no-site-packages %(base_dir)s/env" % {"base_dir": env.base_dir})
    run("test -d %(versions_dir)s || mkdir -p %(versions_dir)s" % {"versions_dir": env.versions_dir})


def activate_revision(revision):
    require("base_dir", "versions_dir", provided_by=("env_test", "env_live"),
            used_for="defining the deploy environment")

    with cd("%s/%s" % (env.versions_dir, revision)):
        with prefix("source %s/env/bin/activate" % env.base_dir):
            if env.update_env:
                run("pip -q install -r django/requirements.txt")

            if env.syncdb:
                run("python django/%s/manage.py syncdb --noinput" % env.django_appname)

            if env.migrate:
                run("python django/%s/manage.py migrate" % env.django_appname)

    with cd(env.versions_dir):
        with settings(hide("warnings", "stderr"), warn_only=True):
            run("test -L current && rm current")

        run("ln -s %s current" % revision)

    with cd(env.base_dir):
        if env.wsgi_file:
            run("touch %s" % env.wsgi_file)


def version_resolve_current():
    revision = None
    with cd(env.versions_dir):
        with settings(hide("stderr", "running", "stdout", "warnings"), warn_only=True):
            revision = run("readlink current")
    return revision.rstrip("/") or None


def deploy(revision="HEAD"):
    require("base_dir", "versions_dir", provided_by=("env_test", "env_live"),
            used_for="defining the deploy environment")

    # resolve the incoming treeish hashref to an actual git revlog
    with cd(env.local_base_dir):
        with hide("running"):
            revision = local("git log -1 --format=%%h %s" % revision, capture=True)

    # resolve the last delpoyed revision - will be None if first deployment
    current_revision = version_resolve_current()

    # create an archive of the revision, extract it on the remote
    # server, and rsync the difference - will be skipped if revision
    # already exists on remote
    copy_revision(current_revision, revision)

    # activate the new version - this might break migrations as
    # auto detecting the difference would be hard
    activate_revision(revision)

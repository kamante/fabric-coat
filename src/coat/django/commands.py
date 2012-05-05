from __future__ import with_statement

import os
import shutil
import glob

from fabric.api import run, local, cd, settings, prefix, hide
from fabric.operations import require
from fabric.state import env

from coat.utils import remote_resolve_current_revision, \
        local_resolve_revision, workdir_prepare

from coat.django.utils import find_manage, find_django_appname
from coat.django import signals


def copy_revision_to_remote(workdir, remote_revision, deploy_revision):
    # test remote for the revision and skip re-copying already
    # existing revisions
    with settings(hide("stdout", "stderr", "warnings"), warn_only=True):
        exists = run("test -d %s/%s && echo 1" %
                     (env.django_settings.versions_dir,
                      deploy_revision))

    if exists == "1":
        return

    # copy all of local onto remote using rsync, use hard links to save
    # space for unmodified files
    rsync_cmd = ("%s/* %s@%s:%s/%s/" %
                 (workdir, env.user, env.host,
                  env.django_settings.versions_dir,
                  deploy_revision))

    signals.pre_workdir_copy_to_remote.send(
        deploy_revision=deploy_revision,
        remote_revision=remote_revision,
        workdir=workdir,
    )

    if remote_revision:
        with cd(env.django_settings.versions_dir):
            run("rsync -a --link-dest=../%(cur)s/ %(cur)s/ %(new)s" %
                {'cur': remote_revision, 'new': deploy_revision})

        local("rsync -a -c --delete %s" % (rsync_cmd))
    else:
        local("rsync -a %s" % rsync_cmd)

    signals.post_workdir_copy_to_remote.send(
        deploy_revision=deploy_revision,
        remote_revision=remote_revision,
        workdir=workdir,
    )


def remote_activate_revision(workdir, remote_revision, deploy_revision):
    django_appname = find_django_appname(workdir)

    remote_base_dir = "%s/../" % env.django_appname.versions_dir
    remote_versions_dir = env.django_settings.versions_dir

    signals.pre_remote_run_commands.send()

    with cd("%s/%s" % (remote_versions_dir, deploy_revision)):
        with prefix("source /env/bin/activate" % remote_base_dir):
            for command in env.virtualenv_settings.commands:
                run(command)

            with prefix("django/%s/manage.py " % django_appname):
                for command in env.django_settings.management_commands:
                    run(command)

    signals.post_remote_run_commands.send()

    signals.pre_remote_activate_revision.send()

    with cd(remote_versions_dir):
        with settings(hide("warnings", "stderr"), warn_only=True):
            run("test -L current && rm current")

        run("ln -s %s current" % deploy_revision)

    signals.post_remote_activate_revision.send()


def remote_reload():
    signals.pre_remote_reload.send()

    with cd(env.base_dir):
        if env.wsgi_file:
            run("touch %s" % env.wsgi_file)

    signals.post_remote_reload.send()


def workdir_django_prepare(workdir):
    django_basedir = os.path.dirname(find_manage(workdir))

    shutil.copy(
        os.path.join(django_basedir, env.django_settings.settings_file),
        os.path.join(django_basedir, "localsettings.py")
    )

    map(os.unlink, glob.glob("%s/localsettings_*.py" % django_basedir))


def deploy(revision="HEAD"):
    require("django_settings", provided_by=("env_test", "env_live"))

    env.django_settings.validate_or_abort()

    env.remote_revision = remote_resolve_current_revision()
    env.deploy_revision = local_resolve_revision(revision)

    env.deploy_workdir = workdir_prepare(revision, folders=("django", ))

    workdir_django_prepare(env.deploy_workdir)

    copy_revision_to_remote(env.deploy_workdir, env.deploy_version)
    remote_activate_revision(env.deploy_revision)

    remote_reload()

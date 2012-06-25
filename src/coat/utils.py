import os
import atexit
import shutil
import tempfile

from fabric.state import env
from fabric.api import lcd, local, hide, settings, cd, run
from fabric.contrib import files as fabric_files
from coat import signals


def get_project_root_directory():
    """
    Returns the dirname of the fabfile.
    """
    return os.path.dirname(os.path.abspath(env.real_fabfile))


def workdir_prepare_checkout(revision, folders):
    """
    Returns an absolute path to a directory containing a git checkout of the
    given treeish revision.

    Registers a hook with atexit to delete the returned directory.

    Dispatches signals to pre_workdir_checkout and post_workdir_checkout.
    """
    signals.pre_workdir_prepare_checkout.send(
        sender=workdir_prepare_checkout,
        revision=revision,
    )

    workdir = tempfile.mkdtemp()

    atexit.register(shutil.rmtree, workdir, True)

    with lcd(get_project_root_directory()):
        local("git archive %s %s | tar -x -C %s" %
              (revision, " ".join(folders), workdir))

        signals.post_workdir_prepare_checkout.send(
            sender=workdir_prepare_checkout,
            revision=revision,
            workdir=workdir,
        )

    return workdir


def local_resolve_revision(revision):
    """
    Returns a partial sha1 from a treeish revision.
    """
    with lcd(get_project_root_directory()):
        with hide("running"):
            revision = local("git log -1 --format=%%h %s" % revision,
                             capture=True)

    return revision


def remote_resolve_current_revision():
    """
    Returns the locally resolved currently active remote revision.
    """
    revision = None

    with settings(hide("stderr", "running", "stdout", "warnings"),
                  warn_only=True):

        # make sure version_dir exists
        if not fabric_files.exists(env.django_settings.versions_dir):
            run("mkdir -p %(versions_dir)s" % env.django_settings)

        # try to resolve current symlink
        with cd(env.django_settings.versions_dir):
            if fabric_files.exists("current"):
                revision = run("readlink current")

                if not revision.failed:
                    revision = revision.rstrip("/")

    if revision:
        return local_resolve_revision(revision)
import os
import atexit
import shutil
import tempfile

from fabric.state import env
from fabric.api import lcd, local, hide, settings, cd, run
from coat.signals import pre_workdir_checkout, post_workdir_checkout


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
    pre_workdir_checkout.dispatch(revision=revision)

    workdir = tempfile.mkdtemp()

    atexit.register(shutil.rmtree, workdir, True)

    with lcd(get_project_root_directory()):
        local("git archive %s %s | tar -x -C %s" %
              (revision, " ".join(folders), workdir))

        post_workdir_checkout.dispatch(revision=revision, workdir=workdir)

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
    with cd(env.django_settings.versions_dir):
        with settings(hide("stderr", "running", "stdout", "warnings"),
                      warn_only=True):
            revision = run("readlink current")
    revision = revision.rstrip("/") or None

    if revision:
        return local_resolve_revision(revision)

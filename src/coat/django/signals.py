from django.dispatch import Signal


pre_workdir_copy_to_remote = Signal(
    providing_args=["deploy_revision", "remote_revision", "workdir"]
)
post_workdir_copy_to_remote = Signal(
    providing_args=["deploy_revision", "remote_revision", "workdir"]
)


pre_remote_run_commands = Signal()
post_remote_run_commands = Signal()


pre_remote_activate_revision = Signal()
post_remote_activate_revision = Signal()


pre_remote_reload = Signal()
post_remote_reload = Signal()


pre_remote_init_virtualenv = Signal()
post_remote_init_virtualenv = Signal()

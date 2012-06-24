from django.dispatch import Signal


pre_workdir_prepare_checkout = Signal(providing_args=["revision"])
post_workdir_prepare_checkout = Signal(providing_args=["revision", "workdir"])

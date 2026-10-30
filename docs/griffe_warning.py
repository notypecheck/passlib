import logging  # noqa: INP001

from properdocs.config.defaults import ProperDocsConfig


def on_config(config: ProperDocsConfig) -> None:
    # Silencing "Parameter ... does not appear in the function signature" from passlib's docstrings
    logging.getLogger("mkdocs.plugins.griffe").setLevel(logging.ERROR)

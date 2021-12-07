# coding: utf-8

from __future__ import annotations
import sys
import argparse
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pprint import pformat as pritty_format
from bookworm import typehints as t
from bookworm import app
from bookworm.runtime import CURRENT_PACKAGING_MODE, PackagingMode
from bookworm.logger import logger, configure_logger


log = logger.getChild(__name__)


class NoSubcommand(Exception):
    """Raise when there is no command line arguments."""


cmd_args_parser = argparse.ArgumentParser()
cmd_args_parser.add_argument("--debug", action="store_true", required=False)
subparsers = cmd_args_parser .add_subparsers(dest="subparser_name")


class BaseSubcommandHandler(ABC):
    subcommand_name: t.ClassVar[str]

    @classmethod
    @abstractmethod
    def add_arguments(cls, subparser: ArgumentParser):
        """Add required commands to this parser."""

    @classmethod
    @abstractmethod
    def handle_commandline_args(cls, args) -> t.Optional[int]:
        """Do the actual handling of the commandline arguments."""


class DefaultCommandlineArgumentNamespace:
    debug = CURRENT_PACKAGING_MODE is PackagingMode.Source
    subcommand_cls = None

    def __repr__(self):
        return str(vars(self))


def register_subcommand(subcommand_cls: BaseSubcommand):
    subparser = subparsers.add_parser(subcommand_cls.subcommand_name, help="Sub command.")
    subcommand_cls.add_arguments(subparser)
    subparser.set_defaults(subcommand_cls=subcommand_cls)
    return subcommand_cls


def handle_app_commandline_args():
    default_namespace = DefaultCommandlineArgumentNamespace()
    app.args = args = cmd_args_parser.parse_args(namespace=default_namespace)
    if args.subcommand_cls is not None:
        configure_logger(log_file_suffix="commandline")
        log.info("The application is running in command line mode.")
        log.info(f"Received command line arguments:\n{pritty_format(args)}")
        log.debug(f"Executing sub command: {args.subparser_name}")
        return args.subcommand_cls.handle_commandline_args(args)

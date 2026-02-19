import json
import argparse

from typing import Sequence, NamedTuple

from .metric_types import MetricsConfig, ValidMetrics
from .metric import valid_metric_types

from .utils import MINUTE

class MainArgs(NamedTuple):
    config: MetricsConfig
    interval: int
    period: int

class TestArgs(NamedTuple):
    metrics: list[ValidMetrics]

def register_run_subcommand(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-c",
        "--config",
        "--config-file",
        required=True,
        help="The configuration json file containing the metric declarations",
        dest="config"
    )
    parser.add_argument(
        "-p",
        "--period",
        default=1,
        type=int,
        help="The default number of intervals before monitoring state changes are checked. Can be overriden for each metric",
        dest="period"
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=MINUTE,
        help="The interval in which metric information is recorded, in seconds. Be nice to the CPU :)",
        dest="interval"
    )

def register_test_subcommand(parser: argparse.ArgumentParser):
    parser.add_argument(
        "metrics",
        choices=valid_metric_types,
        nargs="+"
    )

def build_parser():
    parser = argparse.ArgumentParser(
        prog="System Monitor"
    )
    sub_parsers = parser.add_subparsers(dest="subcommand")
    run_command_parser = sub_parsers.add_parser("monitor")
    register_run_subcommand(run_command_parser)
    test_command_parser = sub_parsers.add_parser("test-metric", aliases=["test"])
    register_test_subcommand(test_command_parser)
    return parser

def read_config_file(file: str) -> MetricsConfig:
    with open(file, "r") as config_file:
        return json.load(config_file)
    raise RuntimeError(f"Unable to read config file: {file}")

def validate_args(args: Sequence[str], parser: argparse.ArgumentParser | None = None) -> TestArgs | MainArgs:
    resolved_parser = build_parser() if parser is None else parser
    parsed = resolved_parser.parse_args(args)
    match parsed.subcommand:
        case "monitor":
            config = read_config_file(parsed.config)
            return MainArgs(config=config, interval=parsed.interval, period=parsed.period)
        case "test" | "test-metric":
            return TestArgs(metrics=parsed.metrics)
    raise TypeError(f"Invalid command invocation: {args}")
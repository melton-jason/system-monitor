import json
import argparse

from typing import Sequence, NamedTuple

from .metric_types import MetricsConfig

from .utils import MINUTE

class Args(NamedTuple):
    config: MetricsConfig
    interval: int
    period: int


def build_parser():
    parser = argparse.ArgumentParser(
        prog="System Monitor"
    )
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
        default=2,
        type=int,
        help="The default number of intervals before monitoring state changes are checked. Can be overriden for each metric",
        dest="period"
    )
    parser.add_argument(
        "-i",
        "--interval",
        type=int,
        default=2.5 * MINUTE,
        help="The interval in which metric information is recorded, in seconds. Be nice to the CPU :)",
        dest="interval"
    )
    return parser

def read_config_file(file: str) -> MetricsConfig:
    with open(file, "r") as config_file:
        return json.load(config_file)
    raise RuntimeError(f"Unable to read config file: {file}")

def validate_args(args: Sequence[str], parser: argparse.ArgumentParser | None = None) -> Args:
    resolved_parser = build_parser() if parser is None else parser
    parsed = resolved_parser.parse_args(args)
    config = read_config_file(parsed.config)
    return Args(config=config, interval=parsed.interval, period=parsed.period)
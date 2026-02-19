import sys
import time

from typing import Sequence


from .subscribers import listeners
from .cli import TestArgs, MainArgs, validate_args
from .metric import parse_metrics, Metric, metric_calculator
from .metric_types import Message

def notify_subscribers(msg: Message):
    for listener in listeners:
        listener(msg)

def event_loop(metrics: list[Metric]):
    for metric in metrics:
        state_changed, current_time_str = metric.update()
        if state_changed:
            notify_subscribers(metric.to_message(current_time_str))

def run_system_monitor(parsed_args: MainArgs):
    metrics = parse_metrics(parsed_args.config, parsed_args.period)
    while True:
        event_loop(metrics)
        time.sleep(parsed_args.interval)

def run_metric_test(parsed_args: TestArgs):
    functs = [metric_calculator[metric] for metric in parsed_args.metrics]
    while True:
        try:
            print(tuple(func() for func in functs))
            time.sleep(1)
        except KeyboardInterrupt:
            print("Recieved Keyboard Interrupt, exiting...")
            sys.exit(0)

def main(args: Sequence[str]):
    parsed_args = validate_args(args)
    if isinstance(parsed_args, MainArgs):
        run_system_monitor(parsed_args)
    elif isinstance(parsed_args, TestArgs):
        run_metric_test(parsed_args)

if __name__ == "__main__":
    main(sys.argv[1:])

import sys
import time

from typing import Sequence


from .subscribers import listeners
from .cli import validate_args
from .metric import parse_metrics, Metric
from .metric_types import Message

def notify_subscribers(msg: Message):
    for listener in listeners:
        listener(msg)

def event_loop(metrics: list[Metric]):
    for metric in metrics:
        print(f"Checking metric: {metric}")
        state_changed, current_time_str = metric.update()
        print(f"{state_changed}, {current_time_str}, {metric.tracked_values._values}")
        if state_changed:
            notify_subscribers(metric.to_message(current_time_str))

def main(args: Sequence[str]):
    parsed_args = validate_args(args)
    metrics = parse_metrics(parsed_args.config, parsed_args.period)
    while True:
        event_loop(metrics)
        time.sleep(parsed_args.interval)

if __name__ == "__main__":
    main(sys.argv[1:])

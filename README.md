# System Monitor
System Monitor is an OS-agnostic system monitoring tool that tracks metrics on a particular system and, when one or more the tracked metrics surpass some threshhold, constructs and sends messages to configured subscribers that can consume the messages as they wish[^1].

## Installation
1. Initialize a new python virtual environment
  - See https://docs.python.org/3/library/venv.html#creating-virtual-environments
```bash
python -m venv my_venv
```
2. Install the required dependencies
```bash
my_venv/bin/pip install -r requirements.txt
```
3. Set up a metric configuration file
4. Run System Monitor
```bash
my_venv/bin/python -m system_monitor.main --config-file my_metrics.json
```

## Example Use Case
Say we want to write to some `high_memory_report.csv` log file when the total RAM usage of our system exceeds 80%.

### Setting up a metric

With System Monitor, the above would be defined by the following JSON:
```json
[
    {
        "name": "My Memory Alarm",
        "description": "Memory use has been high!",
        "severity": "ALARM",
        "metric": "memory_percent",
        "threshhold": {
            "function": "greater_than_or_equal_to",
            "value": 80
        }
    }
]
```
The key parts of the JSON is the `metric` key- which System Monitor will use to identify that we want to monitor the percentage of available memory (in this case the metric is `memory_percent`)- and the `threshhold` dictonary, which System Monitor will use to determine _how_ we want to track our metric, `memory_percent`, and when to generate a message.

The rest of the information is metadata that will be passed to consumers (subscribers) of the messages.

### Choosing a monitoring frequency

With the metric in place, we need to determine how often we would like System Monitor to take snapshots of our metrics, and how often we would like to check for state changes.

System Monitor uses two customizable metrics to control this behavior: 
- Interval: the time in seconds that System Monitor will wait before recording metric information
- Period: the number of intervals that must occur before System Monitor will check for a state change and send messages to subscribers

For example, an interval of 30 seconds means System Monitor will check and record the system's RAM percentage every 30 seconds. An accompanying period of 2 means that two intervals must have passed before the recorded metrics are checked against our metric configuration and a state change is sent to our subscribers.

This means that a minimum of 30 * 2 seconds must have passed before any high RAM usage is sent to subscibers. With our example use case and metric, this means that a subscriber will be notified if the RAM usage is currently at or exceeding 80% during either of the two prior metric snapshots.

For our use case, a higher period is not very useful. A higher period will be useful for more complicated metrics that utilize applying functions on the group of recorded snapshots to determine whether an alarm should be raised, such as the AVG and Datapoints aggregators.

Essentially, decreasing the interval results in more fine-grained metrics being captured, and increasing the period results in a more representative view of the usage of system resources.

To configure the global interval and period, provide the `interval` and `period` options when starting System Monitor:
```bash
venv/bin/python -m system_monitor.main --config-file my_config.json --interval 30 --period 1
```
If unspecified, the default interval is 60 seconds and the default period is 1.

Period can also be overriden and configured on a per-metric basis. 

### Setting up a subscriber
The last step in setting up System Monitor is to add a subscriber that will do something with the messages it generates.

On startup, System Monitor will read the files in the [subscribers](https://github.com/melton-jason/system-monitor/tree/main/system_monitor/subscribers) folder, looking for Python files that have defined a `handle_message(Message)` function.
When a metric should be triggered, each of the subscribers' `handle_message` functions are called with a JSON object representing the message. 

You can use the provided example subscriber as a base:

https://github.com/melton-jason/system-monitor/blob/201e54f5fa6442a467b259c46b4f34d30ef867ae/system_monitor/subscribers/example.py#L1-L4

Let's say we want to write our CSV to `~/logs/monitoring/high_memory_report.csv`, and we want to record the name, description, and time the alert was triggered.

Our subscriber might look something like the following:
```py
import os
from csv import DictWriter
from system_monitor.metric_types import Message

csv_out = "~/logs/monitoring/high_memory_report.csv"
field_names = ["alarmName", "alarmDescription", "time"]

def handle_message(msg: Message):
    row = {
        "alarmName": msg["name"],
        "alarmDescription": msg["description"],
        "time": msg["time"]
    }
    if not os.path.exists(csv_out):
        with open(csv_out, "w") as file:
            writer = DictWriter(file, fieldnames=field_names)
            writer.writeheader()
            writer.writerow(row)
            return
    with open(csv_out, "a") as file:
        writer = DictWriter(file, fieldnames=field_names)
        writer.writerow(row)
```

# TODO: 
- Add configuration docs
- Modularlize the metric definitions, allowing custom metric and metric functions to be defined (e.g., plugins)
- Add support for different types of subscribers
- Use [jsonschema](https://python-jsonschema.readthedocs.io/en/stable/) to validate metric definitions

[^1]: This general structure follows the [Observer](https://en.wikipedia.org/wiki/Observer_pattern) design pattern
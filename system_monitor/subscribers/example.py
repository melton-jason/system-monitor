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
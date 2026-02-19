from typing import TypedDict, Literal, NotRequired, Dict

MetricType = Literal["cpu", "memory", "swap", "disk"]
ValidMetrics = Literal[
    "cpu_utilization",
    "memory_used", "memory_available", "memory_percent",
    "swap_used", "swap_available", "swap_percent",
    "disk_used", "disk_available", "disk_percent"
]
MessageSeverity = Literal["INFO", "WARNING", "ALARM", "CRITICAL"]
MessageState = Literal["OK", "TRIGGERED"]
AggregatedFunction = Literal["AVG", "MIN", "MAX"]
ThreshHoldFunctions = Literal["greater_than", "greater_than_or_equal_to", "less_than", "less_than_or_equal_to"]

class DataPointAggregator(TypedDict):
    datapoints: int

class FunctionAggregator(TypedDict):
    function: AggregatedFunction

Aggregator = DataPointAggregator | FunctionAggregator

class ThresholdInfo(TypedDict):
    function: ThreshHoldFunctions
    value: int | str
    evaluateBy: NotRequired[Aggregator]

class Message(TypedDict):
    name: str
    description: str
    time: str
    state: MessageState
    metric: str
    severity: MessageSeverity
    threshold: ThresholdInfo

class MetricConfig(TypedDict):
    name: str
    description: str
    severity: MessageSeverity
    period: NotRequired[int]
    threshhold: ThresholdInfo

class DiskMetricConfig(MetricConfig):
    path: NotRequired[str]

MetricsConfig = Dict[ValidMetrics, list[DiskMetricConfig]]

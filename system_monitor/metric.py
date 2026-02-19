import psutil

from typing import Callable, Any, Literal, get_args
from datetime import datetime

from .metric_types import MetricConfig, DiskMetricConfig, MessageSeverity, ThreshHoldFunctions, AggregatedFunction, ThresholdInfo, Aggregator, DataPointAggregator, MetricsConfig, Message, MessageState
from .utils import parse_byte_string

DEFAULT_AGGREGATOR: DataPointAggregator = {
    "datapoints": 1
}

valid_threshhold_functions = get_args(ThreshHoldFunctions)
valid_aggregated_functions = get_args(AggregatedFunction)

metric_calculator = {
    "cpu_utilization": lambda: psutil.cpu_percent(interval=1),
    "memory_used": lambda: psutil.virtual_memory().used,
    "memory_available": lambda: psutil.virtual_memory().available,
    "memory_percent": lambda: psutil.virtual_memory().percent,
    "swap_used": lambda: psutil.swap_memory().used,
    "swap_available": lambda: psutil.swap_memory().free,
    "swap_percent": lambda: psutil.swap_memory().percent,

    "disk_used": lambda path: psutil.disk_usage(path).used,
    "disk_available": lambda path: psutil.disk_usage(path).free,
    "disk_percent": lambda path: psutil.disk_usage(path).percent,
}

PointEvaluator = Callable[[Any], bool]
Points = list[Any]

threshhold_calculator: dict[ThreshHoldFunctions, Callable[[Any], PointEvaluator]] = {
    "greater_than_or_equal_to": lambda threshhold: lambda value: value >= threshhold,
    "greater_than": lambda threshhold: lambda value: value > threshhold,
    "less_than": lambda threshhold: lambda value: value < threshhold,
    "less_than_or_equal_to": lambda threshhold: lambda value: value <= threshhold,
}

aggregator_func_calculator: dict[AggregatedFunction, Callable[[PointEvaluator], Callable[[Points], bool]]] = {
    "AVG": lambda eval: lambda points: eval(sum(points) / len(points)),
    "MAX": lambda eval: lambda points: eval(max(points)),
    "MIN": lambda eval: lambda points: eval(min(points)),
}


def datapoints_calculator(dp: DataPointAggregator, eval: PointEvaluator):
    point_threshhold = dp["datapoints"]

    def check_state(points: Points) -> bool:
        samples_in_alarm = 0
        for point in points:
            if eval(point):
                samples_in_alarm += 1

            if samples_in_alarm >= point_threshhold:
                return True
        return False
    return check_state


def resolve_aggregator(ag: Aggregator) -> Literal["points", "function"]:
    datapoints = ag.get('datapoints')
    if datapoints is not None:
        assert isinstance(datapoints, int), f"Unknown type of datapoints {datapoints.__class__}. Expected int"
        return 'points'
    ag_function = ag.get("function")
    if ag_function is not None:
        assert ag_function in valid_aggregated_functions, f"Unknown aggregator function {ag_function}. Expected one of {valid_aggregated_functions}"
        return 'function'
    raise ValueError(f"Unknown aggregator: {ag}")


def aggregator_calculator(evaluator: PointEvaluator, ag: Aggregator) -> Callable[[Points], bool]:
    aggregator = resolve_aggregator(ag)
    match aggregator:
        case 'function':
            return aggregator_func_calculator[ag["function"]](evaluator)
        case 'points':
            return datapoints_calculator(ag, evaluator)


class MetricValues[T]:
    def __init__(self, max_length: int) -> None:
        self._values: list[tuple[str, T]] = []
        self.max_length = max_length

    def values(self):
        return [tup[1] for tup in self._values]

    def peek(self) -> tuple[str, T] | None:
        if len(self._values) <= 0:
            return None
        return self._values[0]

    def push(self, value: T):
        current_time = datetime.now().isoformat()
        self._values.insert(0, (current_time, value))
        cur_len = len(self._values)
        if cur_len >= self.max_length:
            self._values = list(self._values[:self.max_length])

class ThreshHold:
    def __init__(self, *, function: ThreshHoldFunctions, value: Any, aggregator: Aggregator) -> None:
        self.value = value
        self.function = function
        self._sample_in_alarm = threshhold_calculator[function](value)
        self.check_points = aggregator_calculator(
            self._sample_in_alarm, aggregator)

    @classmethod
    def from_json(cls, json: ThresholdInfo):
        cls._json = json
        if isinstance(json["value"], str):
            value = parse_byte_string(json["value"])
        else:
            value = json["value"]
        return cls(
            function=json["function"],
            value=value,
            aggregator=json.get("evaluateBy") or DEFAULT_AGGREGATOR
        )

def validate_threshhold(thresh: ThresholdInfo, period: int):
    if thresh["function"] not in valid_threshhold_functions:
        raise ValueError(f"Invalid threshhold function {thresh['function']}, expected one of {valid_threshhold_functions}")
    
    aggregator = thresh.get("evaluateBy")
    if aggregator is not None:
        ag_type = resolve_aggregator(aggregator)
        if ag_type == 'points':
            assert aggregator["datapoints"] <= period, f"Provided datapoint of {aggregator['datapoints']} must be <= period of {period}"

def validate_metric_config(config: DiskMetricConfig, period: int):
    validate_threshhold(config["threshhold"], period)

class Metric:
    def __init__(self, *,
                 internal_name: str,
                 name: str,
                 description: str = "",
                 severity: MessageSeverity,
                 threshhold: ThreshHold,
                 period: int) -> None:
        self._internal_name = internal_name
        self.name = name
        self.description = description
        self.severity = severity
        self.period = period
        self.threshhold: ThreshHold = threshhold
        self.tracked_values = MetricValues(period)
        self.metric_calculator = metric_calculator[internal_name]
        self._current_interval = 0
        self._current_state: MessageState = "OK"

    def capture_metric(self):
        return self.metric_calculator()

    def to_message(self, time_str: str) -> Message:
        return {
            "name": self.name,
            "description": self.description,
            "metric": self._internal_name,
            "severity": self.severity,
            "state": self._current_state,
            "threshold": self.threshhold._json,
            "time": time_str
        }

    def update(self):
        captured_metric = self.capture_metric()
        self.tracked_values.push(captured_metric)
        self._current_interval += 1
        current_value = self.tracked_values.peek() or ('', '')
        if self._current_interval == self.period:
            self._current_interval = 0
            in_alarm = self.check_alarm()
            state_changed = (in_alarm and self._current_state == 'OK') or (not in_alarm and self._current_state == 'TRIGGERED')
            if in_alarm:
                self._current_state = 'TRIGGERED'
            else: 
                self._current_state = 'OK'
            return state_changed, current_value[0]
        return False, current_value[0]
    
    def check_alarm(self):
        return self.threshhold.check_points(self.tracked_values.values())
    
    @classmethod
    def from_json(cls, name: str, inherited_period: int, json: MetricConfig):
        resolved_period = json.get("period") or inherited_period
        validate_metric_config(json, resolved_period)
        return cls(
            internal_name=name,
            name=json["name"],
            description=json["description"],
            severity=json["severity"],
            threshhold=ThreshHold.from_json(json["threshhold"]),
            period=resolved_period
        )

class DiskMetric(Metric):
    def __init__(self, *, 
                 internal_name: str,
                 name: str,
                 description: str = "",
                 severity: MessageSeverity,
                 threshhold: ThreshHold,
                 period: int,
                 path: str | None  = "/") -> None:
        super().__init__(internal_name=internal_name, name=name, description=description,
                         severity=severity, threshhold=threshhold, period=period)
        self.path = "/" if path is None else path

    def capture_metric(self):
        return self.metric_calculator(self.path)
    
    @classmethod
    def from_json(cls, name: str, inherited_period: int, json: DiskMetricConfig):
        resolved_period = json.get("period") or inherited_period
        validate_metric_config(json, resolved_period)
        return cls(
            internal_name=name,
            name=json["name"],
            description=json["description"],
            severity=json["severity"],
            threshhold=ThreshHold.from_json(json["threshhold"]),
            period=resolved_period,
            path=json.get('path')
        )

def parse_metrics(cfg: MetricsConfig, period: int) -> list[Metric]:
    result = []
    for metric_name, metric_json in cfg.items():
        for raw_metric in metric_json:
            if metric_name.startswith("disk"):
                metric = DiskMetric.from_json(metric_name, period, raw_metric)
            else: 
                metric = Metric.from_json(metric_name, period, raw_metric)
            result.append(metric)
    return result

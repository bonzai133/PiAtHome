import logging
import json
from .counter import Counter

import os
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = "True"

from prometheus_client import start_http_server, Gauge
from prometheus_client import REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR

REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
# REGISTRY.unregister(PROCESS_COLLECTOR)


class TeleinfoMetrics():
    def __init__(self, config, enable) -> None:
        self.enable = enable

        metrics = json.loads(config['metrics'])

        self.gauges = {}
        if enable is True:
            for (k, prop) in metrics.items():
                self.gauges[k] = Gauge(prop[0], prop[1], ['counter_id', 'counter_name'])

    def update(self, counter: Counter):
        if self.enable is False:
            return

        for (mapkey, g) in self.gauges.items():
            value = counter.get_data_value(mapkey)
            if value is not None:
                g.labels(counter.key, counter.name).set(value)


def register(args, config):
    enable = False
    # Start Prometheus serveur and register gauges in service mode only
    if args.service is True and args.metrics_port != 0:
        logging.info("Starting Prometheus exporter")
        enable = True
        start_http_server(8000)

    # Create metrics
    teleinfoMetrics = TeleinfoMetrics(config, enable)

    return teleinfoMetrics

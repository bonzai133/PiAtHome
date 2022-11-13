import time

# Disable _created metrics
import os
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = "True"

from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily, Counter, REGISTRY

# Disable Python metrics
import prometheus_client
prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)


class CustomCollector(object):
    def collect(self):
        yield GaugeMetricFamily('my_gauge', 'Help text', value=7)
        c = CounterMetricFamily('my_counter_total', 'Help text', labels=['foo'])
        c.add_metric(['bar'], 1.7)
        c.add_metric(['baz'], 3.8)
        yield c

        l = CounterMetricFamily('my_loop', 'Help text')
        l.add_metric([], 28)
        yield l


if __name__ == '__main__':
    # Start up the server to expose the metrics.
    prometheus_client.start_http_server(8000)
    
    REGISTRY.register(CustomCollector())

    while(True):
        time.sleep(30)


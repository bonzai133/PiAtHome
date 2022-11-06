
# Disable _created metrics
import os
os.environ['PROMETHEUS_DISABLE_CREATED_SERIES'] = "True"

import random
import time

# Disable Python metrics
import prometheus_client
prometheus_client.REGISTRY.unregister(prometheus_client.GC_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PLATFORM_COLLECTOR)
prometheus_client.REGISTRY.unregister(prometheus_client.PROCESS_COLLECTOR)



# Create a metric to track time spent and requests made.
REQUEST_TIME = prometheus_client.Summary('request_processing_seconds', 'Time spent processing request')
RANDOM_VALUE = prometheus_client.Gauge('my_random', 'The current random value')
LOOP_COUNTER = prometheus_client.Counter('process_loop_number', 'Number of loop done')

# Decorate function with metric.
@REQUEST_TIME.time()
def process_request(t):
    """A dummy function that takes some time."""
    LOOP_COUNTER.inc()

    RANDOM_VALUE.set(t)
    time.sleep(t)

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    prometheus_client.start_http_server(8000)
    # Generate some requests.
    while True:
        process_request(random.random())

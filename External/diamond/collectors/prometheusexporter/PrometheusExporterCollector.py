#!/usr/bin/env python
"""
PrometheusExporterCollector.py

A Diamond collector that scrapes metrics from Prometheus exporters and publishes them to Diamond.
This collector supports multiple exporters with configurable metric mappings.

Each exporter is configured as a separate section in the Diamond config file:
[EXPORTER_NAME]
exporter_url = https://example.com/metrics
metric_from_exporter = diamond_metric_name
another_metric = another_diamond_name

The collector only processes counter and gauge metrics, and uses exact-match mapping.
For each exporter, a health metric is published: <exporter_name>_health (1=success, 0=failure)
"""
from __future__ import print_function

import re

try:
    import requests
except ImportError:
    requests = None

try:
    from diamond.collector import Collector
    from diamond.metric import Metric
except Exception:  # pragma: no cover
    Collector = object
    Metric = None


def parse_prometheus_metrics(text):
    """Parse Prometheus text format and return metrics.
    
    Returns dict of {metric_name_with_labels: (value, metric_type)}
    Only includes counter and gauge types.
    """
    metrics = {}
    current_type = {}
    
    for line in text.split('\n'):
        line = line.strip()
        if not line or line.startswith('# HELP'):
            continue
            
        if line.startswith('# TYPE'):
            # Parse: # TYPE metric_name counter
            parts = line.split()
            if len(parts) >= 4:
                metric_name = parts[2]
                metric_type = parts[3]
                if metric_type in ('counter', 'gauge'):
                    current_type[metric_name] = metric_type
            continue
        
        # Skip comments
        if line.startswith('#'):
            continue
        
        # Parse metric line: metric_name{labels} value
        # or: metric_name value
        match = re.match(r'^([a-zA-Z_:][a-zA-Z0-9_:]*(?:\{[^}]*\})?)(?:\s+)([0-9.e+-]+|NaN)', line)
        if match:
            metric_full = match.group(1)
            value_str = match.group(2)
            
            # Extract base metric name (without labels)
            if '{' in metric_full:
                base_name = metric_full[:metric_full.index('{')]
            else:
                base_name = metric_full
            
            # Only include if it's a counter or gauge
            if base_name in current_type:
                try:
                    value = float(value_str)
                    metrics[metric_full] = (value, current_type[base_name])
                except ValueError:
                    pass
    
    return metrics


class PrometheusExporterCollector(Collector):
    """Diamond collector for Prometheus exporter metrics"""

    def get_default_config_help(self):
        help_str = super(PrometheusExporterCollector, self).get_default_config_help()
        help_str.update({
            'exporters': 'Comma-separated list of exporter names (matching config sections)',
            'interval': 'Polling interval in seconds',
            'timeout': 'HTTP request timeout in seconds',
        })
        return help_str

    def get_default_config(self):
        config = super(PrometheusExporterCollector, self).get_default_config()
        config.update({
            'path': 'prometheus',
            'exporters': '',
            'interval': 60,
            'timeout': 10,
        })
        return config

    def collect(self):
        if requests is None:
            self.log.error('requests library not available')
            return
        
        exporters_str = self.config.get('exporters', '')
        if not exporters_str:
            self.log.warning('No exporters configured')
            return
        
        timeout = int(self.config.get('timeout', 10))
        
        # Process each configured exporter
        for exporter_name in [e.strip() for e in exporters_str.split(',') if e.strip()]:
            if exporter_name in self.config:
                self._collect_exporter(exporter_name, timeout)
            else:
                self.log.error('No exporter configured for {}'.format(exporter_name))
    
    def _collect_exporter(self, exporter_name, timeout):
        """Collect metrics from a single exporter"""
        # Get exporter-specific config
        exporter_url = self.config[exporter_name].get('exporter_url')
        
        if not exporter_url:
            self.log.error('No exporter_url configured for {}'.format(exporter_name))
            self.publish('{}_health'.format(exporter_name), 0)
            return
        
        # Fetch metrics from exporter
        try:
            response = requests.get(exporter_url, timeout=timeout)
            response.raise_for_status()
            metrics_text = response.text
        except Exception as e:
            self.log.error('Failed to fetch metrics from {} ({}): {}'.format(
                exporter_name, exporter_url, e))
            self.publish('{}_health'.format(exporter_name), 0)
            return
        
        # Parse Prometheus metrics
        try:
            parsed_metrics = parse_prometheus_metrics(metrics_text)
        except Exception as e:
            self.log.error('Failed to parse metrics from {}: {}'.format(exporter_name, e))
            self.publish('{}_health'.format(exporter_name), 0)
            return
        
        # Get metric mappings for this exporter
        # Look for config keys like: in <exporter_name> section
        mappings = {}
        for key in self.config[exporter_name].keys():
            if key != 'exporter_url':
                # Extract the metric name from config key
                prom_metric = key
                diamond_metric = self.config[exporter_name].get(key)
                if diamond_metric:
                    mappings[prom_metric] = diamond_metric
        
        # Publish mapped metrics
        published_count = 0
        for prom_metric, diamond_metric in mappings.items():
            if prom_metric in parsed_metrics:
                value, metric_type = parsed_metrics[prom_metric]
                self.publish('{}.{}'.format(exporter_name, diamond_metric), value, precision=2)
                published_count += 1
        
        # Publish health metric
        self.publish('{}_health'.format(exporter_name), 1)
        
        self.log.debug('Published {} metrics from {}'.format(published_count, exporter_name))


if __name__ == '__main__':
    # Minimal local test harness
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='Prometheus exporter URL to test')
    args = parser.parse_args()
    
    if requests is None:
        print('ERROR: requests library not available')
        exit(1)
    
    try:
        response = requests.get(args.url, timeout=10)
        response.raise_for_status()
        metrics = parse_prometheus_metrics(response.text)
        print('Found {} counter/gauge metrics:'.format(len(metrics)))
        for metric_name, (value, metric_type) in sorted(metrics.items())[:20]:
            print('  {} [{}] = {}'.format(metric_name, metric_type, value))
        if len(metrics) > 20:
            print('  ... and {} more'.format(len(metrics) - 20))
    except Exception as e:
        print('ERROR: {}'.format(e))
        exit(1)

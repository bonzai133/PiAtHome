#!/usr/bin/env python
"""
SslCertificateCollector.py

A simple Diamond collector that checks SSL certificate expiration for configured hosts
and emits two metrics per host:
- `ssl_cert_days_until_expiry` (float): days until certificate expires (negative if expired)
- `ssl_cert_status` (int): 0 = valid, 1 = expired, 2 = error

This collector is intentionally minimal and works with Diamond's collector API.
Place this file in Diamond's collectors directory or package it as appropriate.
"""
from __future__ import print_function

import ssl
import tempfile
import os
from datetime import datetime

try:
    from diamond.collector import Collector
    from diamond.metric import Metric
except Exception:  # pragma: no cover - collected when Diamond not installed
    Collector = object
    Metric = None


def get_cert_dict(host, port=443):
    pem = ssl.get_server_certificate((host, port))
    tf = None
    try:
        with tempfile.NamedTemporaryFile('w', delete=False) as f:
            f.write(pem)
            tf = f.name
        cert = ssl._ssl._test_decode_cert(tf)
        return cert
    finally:
        if tf and os.path.exists(tf):
            try:
                os.unlink(tf)
            except Exception:
                pass


def parse_notafter_seconds(cert):
    """Return (seconds_until_expiry, status)
    status: 0 valid, 1 expired, 2 error
    """
    not_after = cert.get('notAfter')
    fmt = '%b %d %H:%M:%S %Y %Z'
    try:
        na = datetime.strptime(not_after, fmt)
    except Exception:
        return 0.0, 2
    # Python 2.7 compatible UTC time comparison
    now = datetime.utcnow()
    delta = na - now
    seconds = delta.total_seconds()
    status = 0 if seconds >= 0 else 1
    return seconds, status


class SslCertificateCollector(Collector):
    """Diamond collector for SSL certificate expiry"""

    def get_default_config_help(self):
        help_str = super(SslCertificateCollector, self).get_default_config_help()
        help_str.update({
            'hosts': 'List of hosts to check, comma-separated (host or host:port)',
            'interval': 'Polling interval in seconds',
        })
        return help_str

    def get_default_config(self):
        config = super(SslCertificateCollector, self).get_default_config()
        config.update({
            'path': 'ssl_cert',
            'hosts': 'example.com',
            'interval': 300,
        })
        return config

    def collect(self):
        hosts = self.config.get('hosts', 'example.com')
        for entry in [h.strip() for h in hosts.split(',') if h.strip()]:
            if ':' in entry:
                host, port_s = entry.rsplit(':', 1)
                try:
                    port = int(port_s)
                except Exception:
                    self.log.error('Invalid port for {}'.format(entry))
                    continue
            else:
                host = entry
                port = 443

            cert = get_cert_dict(host, port)

            seconds, status = parse_notafter_seconds(cert)
            days = seconds / 86400.0

            # publish metrics
            # Diamond expects publish(metric_path, value, hostname=None, metric_type='gauge')
            hostname = host.replace(".", "")
            self.publish('{}.days_until_expiry'.format(hostname), days)
            self.publish('{}.status'.format(hostname), status)


if __name__ == '__main__':
    # Minimal local test harness when diamond is not installed
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('hosts', nargs='+', help='host[:port] to check')
    args = parser.parse_args()
    for h in args.hosts:
        if ':' in h:
            host, port = h.rsplit(':', 1)
            port = int(port)
        else:
            host = h
            port = 443
        try:
            cert = get_cert_dict(host, port)
            seconds, status = parse_notafter_seconds(cert)
            print('{}:{} -> days_until_expiry={:.2f}, status={}'.format(host, port, seconds/86400.0, status))
        except Exception as e:
            print('{}:{} -> error: {}'.format(host, port, e))

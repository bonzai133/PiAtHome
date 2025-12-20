ssl_cert_check
=================

Manual script
-------------

Simple Python script to check an SSL/TLS certificate for a host and report creation date, expiration date and validity.

Usage
-----

Run the script with a hostname or hostname:port:

```
python3 ssl_cert_check.py example.com
python3 ssl_cert_check.py example.com:8443
```

Exit codes
----------
- `0`: certificate valid
- `1`: certificate expired
- `2`: error (network, parse error, invalid args)

Diamond collector
-----------------

A lightweight Diamond collector is provided in `diamond_ssl_cert_collector.py`. It emits two metrics per configured host:
- `<host>.days_until_expiry` (float): days until expiry (negative if expired)
- `<host>.status` (int): 0 = valid, 1 = expired, 2 = error

Example Diamond config in `examples/diamond_ssl_cert_collector.conf`:

```
[SSLCertCollector]
hosts = example.com, google.com:443, piathome.freeboxos.fr
interval = 300
path = ssl_cert
```

To use the collector place `diamond_ssl_cert_collector.py` in Diamond's collectors folder and enable it in Diamond's config. The collector file contains a small `__main__` test harness so you can also run it directly for quick checks:

```
python3 diamond_ssl_cert_collector.py example.com piathome.freeboxos.fr
```

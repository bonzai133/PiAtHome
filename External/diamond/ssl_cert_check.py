#!/usr/bin/env python3
"""ssl_cert_check.py

Simple script to fetch and display SSL certificate dates and validity for a host.

Usage: python ssl_cert_check.py example.com[:port]
"""
import sys
import ssl
from datetime import datetime, timezone
import tempfile
import os


def get_cert(hostname: str, port: int = 443, timeout: float = 5.0):
    # Use ssl.get_server_certificate to obtain PEM and decode it using
    # the internal _test_decode_cert helper which returns the same dict
    # structure as SSLSocket.getpeercert(). This avoids issues with
    # missing fields on some platforms.
    pem = ssl.get_server_certificate((hostname, port))
    # write to a temp file for _test_decode_cert
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


def parse_dates(cert: dict):
    not_before = cert.get('notBefore')
    not_after = cert.get('notAfter')

    fmt = '%b %d %H:%M:%S %Y %Z'
    try:
        nb = datetime.strptime(not_before, fmt).replace(tzinfo=timezone.utc) if not_before else None
    except Exception:
        nb = None
    try:
        na = datetime.strptime(not_after, fmt).replace(tzinfo=timezone.utc) if not_after else None
    except Exception:
        na = None
    return nb, na


def check_cert(host_port: str):
    if ':' in host_port:
        host, port_s = host_port.rsplit(':', 1)
        try:
            port = int(port_s)
        except Exception:
            print(f'Invalid port: {port_s}')
            return 2
    else:
        host = host_port
        port = 443

    try:
        cert = get_cert(host, port)
    except Exception as e:
        print(f'Error fetching certificate from {host}:{port} - {e}')
        return 2

    nb, na = parse_dates(cert)
    now = datetime.now(timezone.utc)

    print(f'Host: {host}:{port}')
    print(f'Certificate subject: {cert.get("subject")}')
    print(f'Issuer: {cert.get("issuer")}')
    print(f'Creation (notBefore): {nb.isoformat() if nb else cert.get("notBefore")}')
    print(f'Expiration (notAfter):  {na.isoformat() if na else cert.get("notAfter")}')

    if na:
        if now <= na:
            print('Status: VALID')
            return 0
        else:
            print('Status: EXPIRED')
            return 1
    else:
        print('Status: UNKNOWN (could not parse dates)')
        return 2


def main(argv):
    if len(argv) != 2:
        print('Usage: ssl_cert_check.py host[:port]')
        return 2
    return check_cert(argv[1])


if __name__ == '__main__':
    sys.exit(main(sys.argv))

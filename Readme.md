# PiAtHome

## Project Description
This project for Raspberry Pi contains several parts.

PySolar: Collect information from Solarmax inverter and store it in local database
PyTeleinfo: Collect information from Teleinfo of eletric counter and store it in local database
ParseTIC: Collect information from Teleinfo of Linky eletric counter
PiAtHome: Web pages to display previous information and production configuration
External: Contains Diamond custom collectors and configuration for various monitoring purposes

## Current status
### TODO List
* Migration to Python 3
* Remove old code
* Replace Diamond by Prometheus
* Update RPi to latest RPiOS

### Migration to Python 3
* External/diamond : N/A (will drop diamond, not maintained. Replace by Prometheus exporters ?)

* PySolar
** 2 to 3: Done
** Unit tests: Done
** Test on RPi: Todo

* PyTeleinfo
** 2 to 3: Done
** Unit tests: Done
** Test on RPi: Todo

* ParseTIC
** 2 to 3: Done
** Unit tests: Done
** Test on RPi: Done

* PiAtHome
** 2 to 3: Done
** Unit tests: Done
** Test on RPi: Todo

* Update magic headers to force Python3

### Remove old code
* Solarmax2: Done
* PyTeleinfo vs ParseTIC
** ParseTIC/teleinfo2.py: used in production with Python 3. To move to PyTeleinfo. Launched by a service.
** ParseTIC/teleinfo.py: to remove
** ParseTIC/parseTic.py: to move to test folder ?
** PyTeleinfo/teleinfo.py: collect teleinfo to /var/run/shm and prom exporter
** PyTeleinfo/teleinfo_aggr.py: Not used anymore (linked to teleinfo.py). To remove.
** PyTeleinfo/teleinfo_store.py: Store daily values of Teleinfo (/var/run/shm) into TeleinfoByDay. Launched by cron. Ok, but need to make shm path configurable
* Setup.py
** update all, really a mess
** test on qemu
* PiAtHome
** pyproject.toml (poetry init)
** bottle
** tests


### Replace Diamond by Prometheus
* Check how to install/configure Prometheus on RPi
* Dev Prom Exporter
** https://github.com/cliviu74/onewire-prom-exporter
** https://github.com/prometheus/client_python
*** See also Bridges to Graphite
*** Custom collectors
*** https://github.com/hikhvar/w1_prometheus_exporter
** https://github.com/prometheus/blackbox_exporter

### Update RPi to latest RPiOS
* Backup current install (PiAtHome db + graphite Db)
* Reinstall RPiOS
* Install PiAthome
* Install Prometheus
* Install Grafana
* Migrate Graphite to Prometheus

# PiAtHome

## Project Description
This project for Raspberry Pi contains several parts.

PySolar: Collect information from Solarmax inverter and store it in local database
PyTeleinfo: Collect information from Teleinfo of eletric counter and store it in local database
ParseTIC: Collect information from Teleinfo of Linky eletric counter => Merge to PyTeleinfo
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
** ParseTIC/teleinfo2.py: used in production with Python 3. To move to PyTeleinfo. Launched by a service. => Done
** ParseTIC/teleinfo.py: to remove => Done
** ParseTIC/parseTic.py: to move to test folder ? => Done
** PyTeleinfo/teleinfo.py: collect teleinfo to /var/run/shm and prom exporter => Done
** PyTeleinfo/teleinfo_aggr.py: Not used anymore (linked to teleinfo.py). To remove => Done
** PyTeleinfo/teleinfo_store.py: Store daily values of Teleinfo (/var/run/shm) into TeleinfoByDay. Launched by cron.  => Done

### Deployement
* Setup.py
** Use Poetry
*** poetry build
*** sudo pip install xxx.whl: => scripts installed in /usr/local/bin, packages in /usr/local/lib/python3.9/dist-packages/
** Projects
*** External -> Diamond and spikes
*** MyPromExporters -> build done, deploy ok, test qemu ok
**** sudo apt install python3-lxml
**** python -m mypromexporters.fioulleclerc_exporter => ok
**** python -m mypromexporters.solarmax_exporter => ok
**** python -m mypromexporters.onewirenet_exporter => ok
*** PiAtHome -> build done
*** PySolar -> build done, deploy ok, test qemu ok
*** PyTeleinfo -> build done, deploy ok, test qemu ok
** test on qemu
* PiAtHome
** pyproject.toml (poetry init)
** bottle
** tests
* Service systemd + cron job
** MyPromExporters
** PiAtHome
** PySolar
** PyTeleinfo

### Replace Diamond by Prometheus
* Check how to install/configure Prometheus on RPi
* Dev Prom Exporter
** https://github.com/cliviu74/onewire-prom-exporter
** https://github.com/prometheus/client_python
*** See also Bridges to Graphite
*** Custom collectors
*** https://github.com/hikhvar/w1_prometheus_exporter
** https://github.com/prometheus/blackbox_exporter

### Exporters
* Fioul Leclerc: standalone exporter -> Done
* Freebox status
** https://github.com/trazfr/freebox-exporter: not tested.
** https://github.com/saphoooo/freebox_exporter: tested ok on RPi, need to increase time to validate app on Fbx
* OneWire / OneWireNet: using i2c master (owfs on /mnt/1wire ?) -> Done
** https://github.com/Nick4154/raspberrypi_onewire_exporter: python read "/sys/bus/w1/devices/"
** https://github.com/l3akage/onewire_exporter: go read "/sys/bus/w1/devices/"
** Need to implement exporter with owfs server on port 4304 (http on 2121 for visualisation)
* Philipstv -> Not required
* Solarmax: standalone exporter -> Done
* Teleinfo: integrated to teleinfo.py service -> Done

### Exporters improvments
* Run exporter as systemd service: see pyteleinfo.service
* Expose exporter on /metrics: it is the case. Any path give same response in fact. -> Done

### Update RPi to latest RPiOS
* Backup current install (PiAtHome db + graphite Db)
* Reinstall RPiOS
* Install PiAthome
* Install Prometheus
* Install Grafana
* Migrate Graphite to Prometheus

### Existing Prometheus Exporter with ports
* https://github.com/prometheus/prometheus/wiki/Default-port-allocations

### RPi Exporters and Prometheus setup
* https://github.com/fahlke/raspberrypi_exporter: interesting service example to replace cron
* https://pimylifeup.com/raspberry-pi-prometheus/
* https://github.com/eko/pihole-exporter/
* https://github.com/dr1s/pihole_exporter.py

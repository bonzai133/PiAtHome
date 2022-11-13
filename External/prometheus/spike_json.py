from prometheus_client import Gauge, start_http_server, Counter, MetricsHandler
import json
import requests
import sys
from http.server import HTTPServer
import urllib.parse

REQUESTS = Counter('hello_worlds_total',
        'Hello Worlds requested.')
METRIC1 = Gauge('metric1', 'Testing1', ["label1"])
METRIC2 = Gauge('metric2', 'Testing2', ["label2"])

ENDPOINT = ""
PORT = ""

class MyRequestHandler(MetricsHandler):
    def do_GET(self):
      REQUESTS.inc()

      parsed_path = urllib.parse.urlsplit(self.path)
      query = urllib.parse.parse_qs(parsed_path.query)
      print(self.path, query)

      if("target" in query):
        host = query['target'][0]
        j = json.loads(requests.get(urllib.parse.urljoin(ENDPOINT, host)).content.decode('UTF-8'))
        METRIC1.clear()
        METRIC1.clear()
        METRIC1.labels(label1=j['label1']).set(j['value1'])
        METRIC2.labels(label2=j['label2']).set(j['value2'])
        return super(MyRequestHandler, self).do_GET()
      else:
        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"No target defined\n")

if __name__ == '__main__':
  # Usage: json_exporter.py port endpoint
  PORT = sys.argv[1]
  ENDPOINT = sys.argv[2]
  
  server_address = ('', int(PORT))
  HTTPServer(server_address, MyRequestHandler).serve_forever()

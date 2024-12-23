import json
import threading
import time
from mqtt_client import MQTTClient
from central_heating import CentralHeating, RadiatorSubscriberMqtt
from status_memento import StatusMemento
from http.server import BaseHTTPRequestHandler, HTTPServer


class CentralHeatingController:
    def __init__(self, broker_address, switch_name):
        self.PUBLISH_INTERVAL = 300
        self.REFRESH_STATE_INTERVAL = 900
        self.REFRESH_PAYLOAD = json.dumps({"child_lock": "UNLOCK"}).encode('utf-8')
        self.mqtt_client = MQTTClient(broker_address)
        self.switch_name = switch_name
        self.central_heating = CentralHeating()
        self.mqtt_client.add_subscriber(RadiatorSubscriberMqtt(self.central_heating))
        self.status_memento = StatusMemento()

    def run(self):
        try:
            self.mqtt_client.connect()
            self.mqtt_client.subscribe("zigbee2mqtt/#")

            class RequestHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header('Content-type', '')
                    self.end_headers()
                    status = self.server.controller.status_memento.get_status()
                    self.wfile.write(status.encode('utf-8'))

            def start_http_server(controller):
                server_address = ('', 1234)
                httpd = HTTPServer(server_address, RequestHandler)
                httpd.controller = controller
                httpd_thread = threading.Thread(target=httpd.serve_forever)
                httpd_thread.daemon = True
                httpd_thread.start()

            start_http_server(self)

            self.refresh()
            self.update()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
            self.mqtt_client.disconnect()

    def send_heat_demand(self):
        heat_demand = self.central_heating.is_heat_demanded()
        topic = f"zigbee2mqtt/{self.switch_name}/set"
        command = {}
        if heat_demand:
            command["state"] = "ON"
        else:
            command["state"] = "OFF"
        command["countdown"] = 600
        payload = json.dumps(command).encode('utf-8')
        self.mqtt_client.publish(topic, payload) 

    def update(self):
        self.central_heating.update()
        self.send_heat_demand()
        self.status_memento.add_status(self.central_heating.get_status())
        print(self.central_heating.get_status())
        self.update_timer = threading.Timer(self.PUBLISH_INTERVAL, self.update)
        self.update_timer.start()

    def refresh(self):
        dev_to_refresh = self.central_heating.get_dev_to_refresh()
        for dev in dev_to_refresh:
            topic = f"zigbee2mqtt/{dev}/set"
            self.mqtt_client.publish(topic, self.REFRESH_PAYLOAD)
        self.refresh_timer = threading.Timer(self.REFRESH_STATE_INTERVAL, self.update)
        self.refresh_timer.start()

    def stop(self):
        if hasattr(self, 'update_timer'):
            self.update_timer.cancel()
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.cancel()
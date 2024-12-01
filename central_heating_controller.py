import json
import threading
import time
from mqtt_client import MQTTClient
from central_heating import CentralHeating, RadiatorSubscriberMqtt


class CentralHeatingController:
    def __init__(self, broker_address, switch_name):
        self.PUBLISH_INTERVAL = 3
        self.mqtt_client = MQTTClient(broker_address)
        self.switch_name = switch_name
        self.central_heating = CentralHeating()
        self.mqtt_client.add_subscriber(RadiatorSubscriberMqtt(self.central_heating))

    def run(self):
        try:
            self.mqtt_client.connect()
            self.mqtt_client.subscribe("zigbee2mqtt/#")
            self.update()
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_update()
            self.mqtt_client.disconnect()

    def send_heat_demand(self):
        heat_demand = self.central_heating.is_heat_demanded()
        topic = f"zigbee2mqtt/{self.switch_name}/set"
        command = {}
        if heat_demand:
            command["state"] = "ON"
        else:
            command["state"] = "OFF"
        command["countdown"] = 300
        payload = json.dumps(command).encode('utf-8')
        self.mqtt_client.publish(topic, payload) 

    def update(self):
        self.central_heating.update()
        self.send_heat_demand()
        self.central_heating.print_status()
        self.update_timer = threading.Timer(self.PUBLISH_INTERVAL, self.update)
        self.update_timer.start()

    def stop_update(self):
        if hasattr(self, 'update_timer'):
            self.update_timer.cancel()
import json
import threading
import time
from mqtt_client import MQTTClient
from central_heating import CentralHeating, RadiatorSubscriberMqtt


class CentralHeatingController:
    def __init__(self, broker_address, switch_name):
        self.PUBLISH_INTERVAL = 60
        self.REFRESH_STATE_INTERVAL = 3600
        self.REFRESH_PAYLOAD = json.dumps({"child_lock": "UNLOCK"}).encode('utf-8')
        self.mqtt_client = MQTTClient(broker_address)
        self.switch_name = switch_name
        self.central_heating = CentralHeating()
        self.mqtt_client.add_subscriber(RadiatorSubscriberMqtt(self.central_heating))

    def run(self):
        try:
            self.mqtt_client.connect()
            self.mqtt_client.subscribe("zigbee2mqtt/#")
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
        command["countdown"] = 300
        payload = json.dumps(command).encode('utf-8')
        self.mqtt_client.publish(topic, payload) 

    def update(self):
        self.central_heating.update()
        self.send_heat_demand()
        self.central_heating.print_status()
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
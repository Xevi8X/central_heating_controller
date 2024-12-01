import random
import sys
import paho.mqtt.client as mqtt


class MQTTClient:
    def __init__(self, broker_address, broker_port=1883, username = "mqtt", password = None):
        client_id = f'python-mqtt-{random.randint(0, 1000)}'
        print (f"Client ID: {client_id}")
        print (f"Address: {broker_address}:{broker_port}")
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
        self.broker_address = broker_address
        self.broker_port = broker_port
        self.connected = False
        self.subscribers = []

        if username:
            if password:
                self.client.username_pw_set(username, password)
            else:
                self.client.username_pw_set(username, None)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, status, properties=None):
        print(f"Connected with status: {status}")

    def on_disconnect(client, userdata, flags, reason_code, status, properties=None):
        print(f"Disconnected with status: {status}")

    def on_message(self, client, userdata, msg):
        for subscriber in self.subscribers:
            subscriber.on_message(client, userdata, msg)

    def connect(self):
        self.client.connect(self.broker_address, self.broker_port, 60)
        self.client.loop_start()
        self.connected = True

    def disconnect(self):
        self.connected = False
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def add_subscriber(self, subscriber):
        self.subscribers.append(subscriber)
    
    def publish(self, topic, payload):
        if not self.connected:
            return
        print(f"Publishing: {topic}, {payload}")
        self.client.publish(topic, payload)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python mqtt_client.py <broker_address>")
        sys.exit(1)

    broker_address = sys.argv[1]
    mqtt_client = MQTTClient(broker_address)

    class Subscriber:
        def on_message(self, client, userdata, msg):
            print(f"Received message: {msg.topic}")

    mqtt_client.add_subscriber(Subscriber())

    try:
        mqtt_client.connect()
        mqtt_client.subscribe("#")
        while True:
            pass
    except KeyboardInterrupt:
        mqtt_client.disconnect()
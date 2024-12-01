import datetime
import json
import threading
from typing import Optional


class Radiator:
    def __init__(self, name, temperature, setpoint, position):
        self.name = name
        self.temperature = temperature
        self.setpoint = setpoint
        self.position = position
        self.last_updated = datetime.datetime.now()

    def from_status(name, status) -> Optional['Radiator']:
        if not 'current_heating_setpoint' in status or not 'local_temperature' in status:
            return None
        temperature = status['local_temperature']
        setpoint = status['current_heating_setpoint']
        if 'position' in status:
            position = status['position']
        elif 'running_state' in status:
            if status['running_state'] == 'heat':
                position = 100
            else:
                position = 0
        else:
            position = -1
        return Radiator(name, temperature, setpoint, position)
    
    def __str__(self):
        name_str = f"{self.name[:25]:<25}" if len(self.name) > 25 else f"{self.name:<25}"
        temperature_str = f"{self.temperature:.1f}°C"
        setpoint_str = f"{self.setpoint:.1f}°C"
        position_str = f"{self.position:3d}%"
        return f"Name: {name_str}, Temperature: {temperature_str}, Setpoint: {setpoint_str}, Position: {position_str} at {self.last_updated}"


class CentralHeating:
    def __init__(self):
        self.RADIATOR_STALE_HOURS=6
        self.MINIMAL_POSITION=30

        self.radiators : dict[str, Radiator] = {}
        self.heat_demand : bool = False
        self.mutex = threading.RLock()

    def update_radiator(self, radiator: Radiator):
        with self.mutex:
            self.radiators[radiator.name] = radiator

    def delete_stale_radiators(self):
        stale_time = datetime.datetime.now() - datetime.timedelta(hours=self.RADIATOR_STALE_HOURS)
        with self.mutex:
            self.radiators = {name: radiator for name, radiator in self.radiators.items() if radiator.last_updated > stale_time}

    def update_heat_demand(self):
        with self.mutex:
            self.heat_demand = False
            for _, radiator in self.radiators.items():
                if radiator.position > self.MINIMAL_POSITION:
                    self.heat_demand = True
                    return
                
    def update(self):
        self.delete_stale_radiators()
        self.update_heat_demand()
                
    def is_heat_demanded(self):
        with self.mutex:
            return self.heat_demand
            
    def print_status(self):
        with self.mutex:
            print("Radiator status:")
            for _, radiator in self.radiators.items():
                print("    ", end="")
                print(radiator)
            print(f"Heat demand: {'on' if self.heat_demand else 'off'}")
            print()


class RadiatorSubscriberMqtt:
    def __init__(self, central_heating: CentralHeating):
        self.central_heating = central_heating

    def on_message(self, client, userdata, msg):
        topic = msg.topic.split('/')

        if len(topic) != 2 or topic[0] != 'zigbee2mqtt' or topic[1] == 'bridge':
            return
        
        name = topic[1]
        try:
            status = json.loads(msg.payload)
        except json.JSONDecodeError:
            return
        radiator = Radiator.from_status(name, status)
        if radiator:
            self.central_heating.update_radiator(radiator)

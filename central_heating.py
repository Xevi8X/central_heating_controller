import datetime
import json
import threading
from typing import Optional
from config import ConfigLoader, RadiatorConfig


class Radiator:
    def __init__(self, name, temperature, setpoint, position):
        self.name = name
        self.temperature = temperature
        self.setpoint = setpoint
        self.position = position
        self.last_updated = datetime.datetime.now()
        self.FIX_PAYLOAD = json.dumps({"current_heating_setpoint": "20"}).encode('utf-8')

    def from_status(name, status) -> Optional['Radiator']:
        if not 'current_heating_setpoint' in status or not 'local_temperature' in status:
            return None
        temperature = status['local_temperature']
        setpoint = status['current_heating_setpoint']
        if 'position' in status:
            position = status['position']
        else:
            error = setpoint - temperature
            position = 100 * error / ConfigLoader._config.temperature_constant
            position = int(min(100, max(0, position)))
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

    def update_radiator(self, radiator: Radiator) -> bool:
        if not self.check_radiator(radiator):
            return False
        if not radiator.name in ConfigLoader._config.radiators:
            ConfigLoader._config.radiators[radiator.name] = RadiatorConfig()
            ConfigLoader.save()
        with self.mutex:
            self.radiators[radiator.name] = radiator
        return True

    def delete_stale_radiators(self):
        stale_time = datetime.datetime.now() - datetime.timedelta(hours=self.RADIATOR_STALE_HOURS)
        with self.mutex:
            self.radiators = {name: radiator for name, radiator in self.radiators.items() if radiator.last_updated > stale_time}

    def update_heat_demand(self):
        with self.mutex:
            self.heat_demand = False
            self.total_power = 0
            config = ConfigLoader._config
            if not config.radiators:
                return
            for name, radiator in self.radiators.items():              
                if not name in config.radiators or not config.radiators[name].included:
                    continue
                self.total_power += config.radiators[name].power * radiator.position / 100
            self.heat_demand = self.total_power > config.power_required
                
    def update(self):
        self.delete_stale_radiators()
        self.update_heat_demand()
                
    def is_heat_demanded(self):
        with self.mutex:
            return self.heat_demand
            
    def get_status(self) -> str:
        with self.mutex:
            status = ["Radiator status:"]
            for _, radiator in self.radiators.items():
                status.append(f"    {radiator}")
            status.append(f"Total power: {self.total_power:.0f}W")
            status.append(f"Heat demand: {'on' if self.heat_demand else 'off'}")
            return "\n".join(status)

    def get_dev_to_refresh(self):
        with self.mutex:
            return list(self.radiators.keys())
        
    def check_radiator(self, radiator: Radiator) -> bool:
        if radiator.temperature < 5 or radiator.temperature > 35:
            return False
        return True

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
            if not self.central_heating.update_radiator(radiator):
                print(f"Detected fault in radiator: {radiator.name}")
                self.fix_radiator(client, radiator)

    def fix_radiator(self, client, radiator: Radiator):
        client.publish(f"zigbee2mqtt/{radiator.name}/set", radiator.FIX_PAYLOAD)

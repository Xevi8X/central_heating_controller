
import sys
from central_heating_controller import CentralHeatingController

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python central_heating_controller.py <broker_address> <switch_name>")
        sys.exit(1)

    broker_address = sys.argv[1]
    switch_name = sys.argv[2]
    central_heating_controller = CentralHeatingController(broker_address, switch_name)
    central_heating_controller.run()
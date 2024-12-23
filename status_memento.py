from datetime import datetime

class StatusMemento:
    def __init__(self):
        self.statuses : list[(str, str)] = []

    def add_status(self, status: str):
        self.statuses.insert(0, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status))
        while len(self.statuses) > 1000:
            self.statuses.pop()

    def get_status(self) -> str:
        return "\n".join([f"{time}\n{status}\n" for time, status in self.statuses])

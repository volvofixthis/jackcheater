from yamspy import MSPy
import time
from kivy.logger import Logger
import logging
from enum import StrEnum

class States(StrEnum):
    ARMING = "arming"
    ARMED = "armed"
    COOLDOWN = "cooldown"
    DISARMED = "disarmed"

class Events:
    ARMED = "armed"
    COOLDOWN = "cooldown"
    DISARMED = "disarmed"
    TRIGGERED = "triggered"
    ALERT = "alert"
    MSP = "msp"
    SUMMARY = "summary"


class Agent:
    state = ""
    running = False
    THRESHOLD = 0
    start_time = time.time()
    last_alert_time = 0
    previous_beep = 0
    trigger_count = 0
    total_trigger_count = 0
    beep_max_delay = 10
    beep_current_delay = beep_max_delay

    def __init__(self, serial):
        self.state = States.ARMING
        self.serial = serial
        self.msp = MSPy(device='', loglevel=logging.INFO, baudrate=115200, logfilename=None)
        self.msp.conn = serial

    def process(self):
        self.running = True
        while self.running:
            dataHandler = self.msp.receive_msg()
            codestr = MSPy.MSPCodes2Str.get(dataHandler['code'])
            if codestr:
                self.msp.process_recv_data(dataHandler)
                if codestr == "MSP2_SENSOR_RANGEFINDER":
                    yield {"name": Events.MSP}
                    if self.state == States.ARMING:
                        Logger.info(f"Range finder quality={self.msp.RANGEFINDER['quality']}, distance={self.msp.RANGEFINDER['distance_mm']}")
                        if time.time() - self.start_time > 5 and self.msp.RANGEFINDER['distance_mm'] > 100:
                            self.THRESHOLD = self.msp.RANGEFINDER['distance_mm'] * 0.85
                            self.state = States.COOLDOWN
                            Logger.info(f"Threshold found: {self.THRESHOLD}")
                            self.last_alert_time = time.time() - 28
                            yield {"name": Events.COOLDOWN}
                    elif self.msp.RANGEFINDER['distance_mm'] < 100 and (self.state in [States.ARMED, States.COOLDOWN]):
                        self.state = States.DISARMED
                        yield {"name": Events.DISARMED, "msg": {"sound": "disarmed"}}
                        break
                    elif self.state == States.ARMED:
                        if self.msp.RANGEFINDER['distance_mm'] <  self.THRESHOLD:
                            self.state = States.COOLDOWN
                            self.last_alert_time = time.time()
                            self.trigger_count += 1
                            self.total_trigger_count += 1
                            self.beep_current_delay = self.beep_current_delay / self.trigger_count
                            sound = "beep"
                            yield {
                                "name": Events.TRIGGERED,
                                "msg": {
                                    "sound": sound,
                                    "trigger_count": self.trigger_count,
                                    "total_trigger_count": self.total_trigger_count,
                                }
                            }
                        elif self.trigger_count > 0:
                            if time.time() - self.last_alert_time > 5 * 60:
                                self.trigger_count = 0
                                self.beep_current_delay = self.beep_max_delay
                            if time.time() - self.previous_beep > self.beep_current_delay:
                                self.previous_beep = time.time()
                                yield {"name": Events.ALERT, "msg": {"sound": "beep"}}
                    elif self.state == States.COOLDOWN:
                        if time.time() - self.last_alert_time > 10:
                            self.state = States.ARMED
                            self.previous_beep = time.time()
                            yield {"name": Events.ARMED, "msg": {"sound": "armed"}}
            elif dataHandler['packet_error'] == 1:
                Logger.info('Packet error!')
        if self.running and (self.state in [States.ARMED, States.COOLDOWN]):
            self.state = States.DISARMED
            yield {"name": Events.DISARMED, "msg": {"sound": "disarmed"}}
        self.running = False

        yield {
            "name": Events.SUMMARY, 
            "msg": {
                "trigger_count": self.trigger_count,
                "total_trigger_count": self.total_trigger_count
            }
        }

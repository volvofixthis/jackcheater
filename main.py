import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.clock import mainthread
from src.agent import Agent, Events
from src.serial import Serial
from threading import Thread
from kivy.logger import Logger, LOG_LEVELS
import json
from kivy.core.audio import SoundLoader
from kivy.graphics import Color

Logger.setLevel(LOG_LEVELS["info"])

class DeviceButton(Button):
    _col = [1, 1, 1, 1] 

    def get_col(self):
        return self._col

    @mainthread
    def set_col(self, v):
        for i in self.canvas.get_group(None):
            if type(i) is Color:
                i.r, i.g, i.b, i.a = v
                break
        self._col = v

    col = property(get_col, set_col)

ASSETS_PATH = "assets/"
# if kivy.platform == "android":
#     ASSETS_PATH = "/data/data/tech.lakin.jackcheater/files/app/assets/"

class MainScreen(GridLayout):
    spacing = [10, 10]
    padding = [10, 10, 10, 10]

    serial = None
    stop_button = None
    start_button = None
    devicebutton: Button
    devicebutton_default_color = [1, 1, 1, 1]
    devicename = ""
    listen_task: Thread | None = None
    agent: Agent | None = None
    sounds = {
        "armed": SoundLoader.load(ASSETS_PATH + 'armed.mp3'),
        "disarmed": SoundLoader.load(ASSETS_PATH + 'disarmed.mp3'),
        "aiai": SoundLoader.load(ASSETS_PATH + 'aiai.mp3'),
        "beep": SoundLoader.load(ASSETS_PATH + 'beep.mp3'),
    }
    device_dropdown = None

    def reset_agent_resources(self):
        self.devicebutton.col = self.devicebutton_default_color
        self.agent = None
        self.listen_task = None
        if self.serial:
            self.serial.close()
            self.serial = None

    def listen(self):
        if not self.agent:
            return
        for event in self.agent.process():
            if event["name"] == Events.MSP:
                if self.devicebutton.col == self.devicebutton_default_color:
                    self.devicebutton.col = [1, 1.5, 1, 1]
                else:
                    self.devicebutton.col = self.devicebutton_default_color
            else:
                self.add_log(f"Event: {json.dumps(event)}")
                if "msg" in event and event["msg"].get("sound"):
                    self.play_sound(event["msg"]["sound"])
        self.reset_agent_resources()

    def open_device_dropdown(self, _):
        self.device_dropdown.clear_widgets()
        for device in Serial.get_devices():
            btn = Button(text=device, size_hint_y=None, height=100)
            btn.bind(on_release=lambda btn: self.device_dropdown.select(btn.text))
            self.device_dropdown.add_widget(btn)
        self.device_dropdown.open(self.devicebutton)

    def add_devicebutton(self):
        self.device_dropdown = DropDown()
        self.devicebutton = DeviceButton(text='Select device')
        self.devicebutton.col = self.devicebutton_default_color
        self.devicebutton.bind(on_release=self.open_device_dropdown)
        self.device_dropdown.bind(on_select=self.on_device_select)
        self.add_widget(self.devicebutton)

    def on_new_intent(self, intent):
        from jnius import cast
        from jnius import autoclass
        UsbManager = autoclass("android.hardware.usb.UsbManager")
        UsbDevice = autoclass("android.hardware.usb.UsbDevice")
        self.add_log("Received intent: " + intent.getAction())
        if intent.getAction() == UsbManager.ACTION_USB_DEVICE_ATTACHED:
            message = intent.getParcelableExtra(UsbManager.EXTRA_DEVICE)
            usb_device = cast(UsbDevice, message)
            self.on_device_select(None, usb_device.getDeviceName())
        elif intent.getAction() == UsbManager.ACTION_USB_DEVICE_DETACHED:
            self.on_stop(None)

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.cols = 2
        self.rows = 3
        start_button = Button(text="Start")
        start_button.bind(on_press=self.on_start)
        self.add_widget(start_button)
        stop_button = Button(text="Stop")
        stop_button.bind(on_press=self.on_stop)
        self.add_widget(stop_button)

        self.add_devicebutton()

        self.log = TextInput(readonly=True)
        self.add_widget(self.log)

        if kivy.platform == "android":
            from android.permissions import request_permissions
            request_permissions(["android.permission.USB_PERMISSION"])
            import android.activity
            android.activity.bind(on_new_intent=self.on_new_intent)

    def on_start(self, _):
        if self.devicename == "":
            self.add_log("select device!")
            return
        if self.listen_task:
            self.add_log("already connected!")
            return
        self.serial = Serial.connect(self.devicename)
        if not self.serial:
            self.add_log("can't connect! try again!")
        self.add_log("connected.")
        self.agent = Agent(self.serial)
        self.listen_task = Thread(target=self.listen, args=[], daemon=True)
        self.listen_task.start()

    def on_stop(self, _):
        if self.agent and self.listen_task and self.listen_task.is_alive():
            self.agent.running = False
            self.listen_task.join()
        self.reset_agent_resources()

    @mainthread
    def add_log(self, line):
        self.log.text += line + "\n"

    @mainthread
    def clean_log(self):
        self.log.text = ""

    @mainthread
    def play_sound(self, sound):
        for _, s in self.sounds.items():
            if s.state == 'play':
                s.stop()
        self.sounds[sound].play()

    def on_device_select(self, _, x):
        self.devicebutton.text = x
        self.devicename = x


class MainApp(App):

    def build(self):
        return MainScreen()

if __name__ == '__main__':
    MainApp().run()

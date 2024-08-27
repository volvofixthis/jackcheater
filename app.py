from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
import glob


class LoginScreen(GridLayout):

    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.cols = 2
        self.rows = 3
        start_button = Button(text="Start")
        start_button.bind(on_press=self.on_start)
        self.add_widget(start_button)
        stop_button = Button(text="Stop")
        stop_button.bind(on_press=self.on_stop)
        self.add_widget(stop_button)
        dropdown = DropDown()
        devices = glob.glob("/dev/tty*")
        for device in devices:
            btn = Button(text=device, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)
        mainbutton = Button(text='Select device')
        mainbutton.bind(on_release=dropdown.open)
        dropdown.bind(on_select=lambda instance, x: setattr(mainbutton, 'text', x))
        self.add_widget(mainbutton)

        self.log = TextInput()
        self.add_widget(self.log)

    def on_start(self, instance):
        self.log.insert_text("started\n")

    def on_stop(self, instance):
        self.log.insert_text("stoped\n")


class MainApp(App):

    def build(self):
        return LoginScreen()

if __name__ == '__main__':
    MainApp().run()

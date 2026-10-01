import pygetwindow as gw
from pywinauto.application import Application
from io import StringIO
from contextlib import redirect_stdout
import pyttsx3
from utils import *
from pywinauto.uia_defines import IUIA  
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.win32functions import SetProcessDPIAware
from PIL import ImageGrab

from speech.tts import *

class UIManager:

    def __init__(self):

        SetProcessDPIAware()  # avoid blurry crops on high-DPI

        self.util = Utils()
        self.tts = TTS()

        self.active_window = gw.getActiveWindow()
        self.app = Application(backend="uia").connect(title=self.active_window.title, visible_only=False)
        self.window = self.app.window(title=self.active_window.title)

    def get_ui_tree(self):
        """
        Retrieves the UI tree of the currently active window.
        """
        dialog = self.app.top_window()  
        dialog.set_focus()

        output = StringIO()

        with redirect_stdout(output):
            dialog.print_control_identifiers()

        ui_tree = output.getvalue()

        return ui_tree
    
    def get_screenshot(self, filename="screenshot.png"):

        """
        Takes a screenshot of the currently active window and saves it to the specified filename.
        """
        img = self.window.capture_as_image()  
        img.save(filename)
        return filename
    
    def get_control_properties(self, element):
        """
        Retrieves properties of a given control element.
        """
        try:
            control = self.window.child_window(title=element["title"], control_type=element["control_type"])
            control.wait('exists', timeout=3)
            properties = control.get_properties()
            return properties
        except Exception as e:
            print("Error retrieving properties:", e)
            return None
    
    def simulate(self, element_data):

        """
        Simulates a click on the element specified in element_data.
        """
        try:
            spec = self.window.child_window(
                control_type=element_data["control_type"],
                title=element_data["title"]
            )

            element = spec.wait('exists', timeout=2)


            if element_data["control_type"] == "Edit":

                print("Yes, it's an Edit control")
                element.set_focus()
                element.type_keys("^a{BACKSPACE}")

                print("Doing...")
                element.type_keys(str(element_data["value"]), with_spaces=True, set_foreground=True)
                print("Done!")

                self.tts.speak(f"Prediction -- {element_data['title']} -- {element_data['reason']}")
                # self.tts.speak(f"Verified -- the {element_data['title']} element is present, typing {element_data['value']} into it now.")
                
                return 1

            self.tts.speak(f"Prediction -- {element_data['title']} -- {element_data['reason']}")
            # self.tts.speak(f"Verified -- the {element_data['title']} element is present, clicking on it now.")

            element.click_input()
            print(f"Clicked on element using control_type='{element_data['control_type']}' and title='{element_data['title']}'.")

            return 1

        except Exception as e:
            print("Error:", e)
            return 0
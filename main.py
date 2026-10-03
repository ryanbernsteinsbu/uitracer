# import cProfile
from pywinauto import Desktop, Application
import pygetwindow as gw
from collections import deque
import time
import tkinter as tk
import sys
import hashlib
import json
from uitree import *
import threading

running = False
record = StateTree()

# profiler = cProfile.Profile()
def switch_wait():
    # hold program till main app is switched
    last_title = gw.getActiveWindow().title
    global running
    running = True #ensure this does not break things, just for testing
    while running:
        active = gw.getActiveWindow()

        if active:
            title = active.title

            if title != last_title:
                print(f"Focus changed to: {title}")
                return

def wait_for_tree_change(window, timeout=30, poll_interval=0.25):
    initial = get_tree_signature(window)
    start = time.time()
    global running
    while time.time() - start < timeout and running:
        current = get_tree_signature(window)

        if current != initial:
            #record_tree()
            return True

        time.sleep(poll_interval)

    return False

def print_tree():
    switch_wait()
    while True:
        window, default = get_tree()
        # profiler.enable()
        data = window.get_control_tree_json()
        # profiler.disable()
        print(json.dumps(data, indent=4))
        wait_for_tree_change(window)

def capture_tree():
    global running
    # record = StateTree()
    last_state = None
    last_action = None
    switch_wait()
    while running:
        window, default = get_tree()
        
        data = window.get_control_tree_json()
        state = get_json_tree_signature(data)
        if state in record.states.keys():
            print("backtrack found")       
        record.add_state(get_node(data, default))
        print("ready")
        # check window sig for backtrack 
        # update last state with action

        wait_for_tree_change(window)

def create_overlay_window(width=300, height=100, padding=50, title="UI Explorer"):
    root = tk.Tk()

    def toggle_capture():
        global running
        global record
        if running: 
            running = False
            
            # profiler.dump_stats("profile.prof")
            save_state_tree(record, "states.jsonl")
            
            button.config(text="Run")
        else:
            running = True
            threading.Thread(
                target=capture_tree,
                daemon=True
            ).start()
            button.config(text="Stop")


    root.title(title)
    root.attributes("-topmost", True)

    # Screen size
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Bottom-left positioning
    x = screen_width - width - padding
    y = screen_height - height - padding

    root.geometry(f"{width}x{height}+{x}+{y}")

    # UI
    label = tk.Label(root, text="UI Explorer Running")
    label.pack(pady=(10, 5))

    button = tk.Button(root, text="Run", command=toggle_capture)
    button.pack()

    return root

if __name__ == "__main__":

    root = create_overlay_window()
    root.mainloop()
    # time.sleep(0.1)
    # print("Switch to your target app in 3 seconds...")
    # time.sleep(3)


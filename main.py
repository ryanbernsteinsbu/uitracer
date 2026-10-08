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

import os
import nest_asyncio
import pandas as pd
from dotenv import find_dotenv, load_dotenv 
from langsmith import Client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langsmith import evaluate

running = False

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

def choose_next_action(llm, task, ui_tree, history=None):
    history = history or []

    prompt = f"""
    You are a UI navigation agent.

    Task:
    {task}

    Previous Actions:
    {history}

    Current UI Tree:
    {ui_tree}

    Select the next UI element the user should interact with.

    Return JSON:
    {{
        "automation_id": "...",
        "control_type": "...",
        "action": "click|type|select",
        "reason": "..."
    }}
    """

    response = llm.invoke(prompt)

    text = response.content[0]["text"]
    text = text.replace("```json", "")
    text = text.replace("```", "")
    text = text.strip()

    action = json.loads(text)
    return action


def capture_tree(record, llm, client, dataset_id):
    global running
    # record = StateTree()
    task = "change the margins to narrow" # to be settable at runtime
    history = []
    last_state = None
    last_action = None
    switch_wait()
    while running:
        window, default = get_tree() # possibly improve this function by making it return json
        data = window.get_control_tree_json()
        state = get_json_tree_signature(data)

        print("state processed")
        if state in record.states.keys():
            print("backtrack found") # maybe add a back track flag


        record.add_state(get_node(data, default))
        #ask LLM for next move
        print("querying for next move")
        action = choose_next_action(llm, task, data, history=None)
        history.append(action)
        print(action)
        client.create_example(
            inputs={
                "task": task,
                "ui_tree": data,
            },
            outputs={
                "automation_id": action["automation_id"],
                "control_type": action["control_type"],
                "action": action["action"],
                "reason": action["reason"]
            },
            dataset_id=dataset_id,
        )
        
        print(action)
        control = window.child_window(
            auto_id=action["automation_id"],
            control_type=action["control_type"]
        )

        control.wrapper_object().click_input() 
        # check window sig for backtrack 
        # update last state with action

        wait_for_tree_change(window)

def create_overlay_window(record, llm, client, dataset_id, width=300, height=100, padding=50, title="UI Explorer"):
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
                # target=lambda: capture_tree(record, llm, client, dataset_id),
                target= print_tree,
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
    
    load_dotenv(find_dotenv())
    os.environ["LANGCHAIN_API_KEY"] = str(os.getenv("LANGCHAIN_API_KEY"))
    os.environ["GOOGLE_API_KEY"] = str(os.getenv("MODEL_API_KEY"))
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_PROJECT"] = "ui-dataset-langsmith"

    client = Client()

    # llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")

    record = StateTree()
    dataset_name = "UI tempNavigation Dataset 2"

    dataset = client.create_dataset(
        dataset_name=dataset_name,
        description="UIs and their navigation",
    )

    root = create_overlay_window(record, llm, client, dataset.id)
    root.mainloop()
    # time.sleep(0.1)
    # print("Switch to your target app in 3 seconds...")
    # time.sleep(3)


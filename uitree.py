from pywinauto import Desktop, Application
import pygetwindow as gw
from collections import deque
import time
import tkinter as tk
import sys
import hashlib
import json

class Action: # how to get from one state to another
    def __init__(self, automation_id, content, action_type):
        self.automation_id = automation_id
        self.content = content
        self.action_type = action_type

    def __repr__(self):
        return (
            f"{self.action_type}:"
            f"{self.content}"
            f"({self.automation_id})"
        )

    def __hash__(self):
        return (
            f"{self.action_type}:"
            f"{self.content}"
            f"({self.automation_id})"
        )
    
class StateNode:
    def __init__(self, state_hash, ui_tree, default_action):
        self.state_hash = state_hash 
        self.ui_tree = ui_tree
        self.default_action = default_action

        self.transitions = {}  # all possible next screens

    def add_transition(self, action, child):
        self.transitions[action] = child

class StateTree:
    def __init__(self):
        self.root = None
        self.states = {}

    def add_state(self, state):
        self.states[state.state_hash] = state

        if self.root is None:
            self.root = state

        return state

def get_tree_signature(element):
    parts = []
    def walk(node):
        try:
            info = node.element_info
            parts.append(
                (
                    info.control_type,
                    info.name,
                    info.automation_id,
                )
            )
            for child in node.children():
                walk(child)
        except Exception:
            pass
    walk(element)

    data = repr(parts).encode()
    return hashlib.sha256(data).hexdigest()

def get_json_tree_signature(data):
    parts = []
    def walk(node):
        parts.append(
            (
                node["control_type"],
                node["name"],
                node["automation_id"],
            )
        )
        for child in node["children"]:
            walk(child)
    walk(data)

    encoded = repr(parts).encode()
    return hashlib.sha256(encoded).hexdigest()

def get_tree(): #returns a tree and control of the current screen
    try:
        default = None
        active_window = gw.getActiveWindow()
        app = Application(backend="uia").connect(title=active_window.title, visible_only=False)
        window = app.window(title=active_window.title)
        for ctrl in window.descendants():
            try:
                if ctrl.has_keyboard_focus():
                    default = ctrl
            except:
                pass
        print(f"Active window: {window.window_text()}\n")
        return window, default
    except Exception as e:
        print("Error:", e)

def get_node(window, default):
    new_node = StateNode(get_tree_signature(window), window, default)
    return new_node
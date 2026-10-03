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
        return hash((
            self.action_type,
            self.content,
            self.automation_id
        ))

    def __eq__(self, other):
        if not isinstance(other, Action):
            return NotImplemented

        return (
            self.automation_id == other.automation_id
            and self.content == other.content
            and self.action_type == other.action_type
        )

    def to_dict(self):
        return {
            "automation_id": self.automation_id,
            "content": self.content,
            "action_type": self.action_type,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["automation_id"],
            data["content"],
            data["action_type"],
        )
    
class StateNode:
    def __init__(self, state_hash, ui_tree, default_action):
        self.state_hash = state_hash 
        self.ui_tree = ui_tree
        self.default_action = default_action

        self.transitions = {}  # all possible next screens

    def add_transition(self, action, child):
        self.transitions[action] = child

    def to_dict(self):
        return {
            "state_hash": self.state_hash,
            "ui_tree": self.ui_tree,
            "default_action": repr(self.default_action),
            "transitions": [
                {
                    "action": action.to_dict(),
                    "child": child.state_hash,
                }
                for action, child in self.transitions.items()
            ],
        }
    
class StateTree:
    def __init__(self):
        self.root = None
        self.states = {}

    def add_state(self, state):
        self.states[state.state_hash] = state

        if self.root is None:
            self.root = state

        return state

def save_state_tree(state_tree, filename):
    with open(filename, "w", encoding="utf-8") as f:

    # First record describes the tree itself
        f.write(json.dumps({
            "type": "state_tree",
            "root": (
                state_tree.root.state_hash
                if state_tree.root is not None
                else None
            )
        }) + "\n")

        # One state per line
        for state in state_tree.states.values():
            f.write(json.dumps({
                "type": "state",
                "data": state.to_dict()
            }) + "\n")

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
                node["text"],
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
    new_node = StateNode(get_json_tree_signature(window), window, default)
    return new_node

def load_state_tree(filename):
    state_tree = StateTree()

    records = []

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            records.append(json.loads(line))

    # First record contains tree metadata
    tree_record = records[0]

    root_hash = tree_record["root"]

    # First pass: create every StateNode
    for record in records[1:]:
        if record["type"] != "state":
            continue

        data = record["data"]

        default_action = None

        if data["default_action"] is not None:
            default_action = Action.from_dict(
                data["default_action"]
            )

        state = StateNode(
            state_hash=data["state_hash"],
            ui_tree=data["ui_tree"],
            default_action=default_action,
        )

        state_tree.states[state.state_hash] = state

    # Second pass: reconstruct transitions
    for record in records[1:]:
        if record["type"] != "state":
            continue

        data = record["data"]

        state = state_tree.states[data["state_hash"]]

        for transition in data["transitions"]:
            action = Action.from_dict(
                transition["action"]
            )

            child_hash = transition["child"]
            child = state_tree.states[child_hash]

            state.add_transition(action, child)

    # Restore root
    if root_hash is not None:
        state_tree.root = state_tree.states[root_hash]

    return state_tree
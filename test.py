from uitree import *

import json

def read_states(filename):
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            print(json.dumps(record, indent=4))
            print("-" * 80)


if __name__ == "__main__":
    read_states("states.jsonl")
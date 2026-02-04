#!/usr/bin/env python3
import json
import sys

def main():
    input_data = json.loads(sys.stdin.read())
    name = input_data.get("name", "World")
    print(json.dumps({"greeting": f"Hello, {name}! Nice to meet you."}))

if __name__ == "__main__":
    main()


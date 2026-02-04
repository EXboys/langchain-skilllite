#!/usr/bin/env python3
import json
import sys

def main():
    input_data = json.loads(sys.stdin.read())
    text = input_data.get("text", "")
    print(json.dumps({"result": text.upper()}))

if __name__ == "__main__":
    main()


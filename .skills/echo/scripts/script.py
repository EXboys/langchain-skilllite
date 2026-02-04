#!/usr/bin/env python3
import json
import sys

def main():
    input_data = json.loads(sys.stdin.read())
    message = input_data.get("message", "")
    print(json.dumps({"message": message}))

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Generate a batch of v4 UUIDs for use as Weave node/edge ids.
Usage: python3 generate_uuids.py <count>
"""
import sys
import uuid

def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    for _ in range(count):
        print(str(uuid.uuid4()))

if __name__ == "__main__":
    main()

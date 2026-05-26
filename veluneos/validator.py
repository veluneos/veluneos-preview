import json
import os
import sys
from collections import defaultdict

CORE_REQUIRED_FIELDS = ["event_id", "trace_id", "parent_event_ids", "timestamp", "event_type", "agent", "summary"]
AGENT_REQUIRED_FIELDS = ["id", "type"]

def load_jsonl(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Target log file not found: {file_path}")
    events = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Line {line_number}: invalid JSON: {exc}") from exc
            validate_event_shape(event, line_number)
            events.append(event)
    validate_event_graph(events)
    return events

def validate_event_shape(event, line_number):
    for field in CORE_REQUIRED_FIELDS:
        if field not in event:
            raise ValueError(f"Line {line_number}: missing required field '{field}'")
    if not isinstance(event["parent_event_ids"], list):
        raise ValueError(f"Line {line_number}: parent_event_ids must be a list")
    if not isinstance(event["agent"], dict):
        raise ValueError(f"Line {line_number}: agent must be an object")
    for field in AGENT_REQUIRED_FIELDS:
        if field not in event["agent"]:
            raise ValueError(f"Line {line_number}: missing agent field '{field}'")
    if "artifacts" in event and not isinstance(event["artifacts"], list):
        raise ValueError(f"Line {line_number}: artifacts must be a list when present")

def validate_event_graph(events):
    event_ids = [event["event_id"] for event in events]
    duplicates = {event_id for event_id in event_ids if event_ids.count(event_id) > 1}
    if duplicates:
        raise ValueError(f"duplicate event_id values found: {sorted(duplicates)}")
    event_id_set = set(event_ids)
    for event in events:
        for parent_id in event["parent_event_ids"]:
            if parent_id not in event_id_set:
                raise ValueError(f"event {event['event_id']} references missing parent_event_id {parent_id}")
    children = defaultdict(list)
    for event in events:
        for parent_id in event["parent_event_ids"]:
            children[parent_id].append(event["event_id"])
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            raise ValueError(f"cycle detected at event_id {node}")
        if node in visited:
            return
        visiting.add(node)
        for child in children.get(node, []):
            visit(child)
        visiting.remove(node)
        visited.add(node)
    for event_id in event_id_set:
        visit(event_id)

def validate_lineage_file(file_path):
    print(f"[*] [VALIDATOR] Inspecting event-lineage file: {file_path}")
    try:
        events = load_jsonl(file_path)
    except Exception as exc:
        print(f"[-] [SPEC VIOLATION] {exc}")
        sys.exit(1)
    print(f"[+] [SUCCESS] Core lineage specification verified ({len(events)} events).\n")
    return events

import argparse
import sys
from collections import defaultdict, deque
from veluneos.validator import validate_lineage_file

def configure_stdout_encoding():
    """Avoid UnicodeEncodeError on Windows consoles with non-UTF-8 defaults."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def build_indexes(events):
    event_map = {event["event_id"]: event for event in events}
    children_map = defaultdict(list)
    for event in events:
        for parent_id in event["parent_event_ids"]:
            children_map[parent_id].append(event["event_id"])
    return event_map, children_map

def sort_events(events):
    return sorted(events, key=lambda event: (event.get("timestamp", ""), event["event_id"]))

def filter_events(events, event_type=None, artifacts_only=False):
    filtered = events
    if event_type:
        filtered = [event for event in filtered if event["event_type"] == event_type]
    if artifacts_only:
        filtered = [event for event in filtered if event.get("artifacts")]
    return filtered

def backtrace(event_id, event_map):
    if event_id not in event_map:
        raise KeyError(f"event_id not found: {event_id}")
    result, visited = [], set()
    def walk(current_id, depth):
        if current_id in visited:
            return
        visited.add(current_id)
        event = event_map[current_id]
        result.append((depth, event))
        for parent_id in event.get("parent_event_ids", []):
            walk(parent_id, depth + 1)
    walk(event_id, 0)
    return result

def branch_trace(event_id, event_map, children_map):
    if event_id not in event_map:
        raise KeyError(f"event_id not found: {event_id}")
    result, queue, visited = [], deque([(0, event_id)]), set()
    while queue:
        depth, current_id = queue.popleft()
        if current_id in visited:
            continue
        visited.add(current_id)
        result.append((depth, event_map[current_id]))
        for child_id in children_map.get(current_id, []):
            queue.append((depth + 1, child_id))
    return result

def print_event(event, prefix=""):
    agent = event["agent"]
    artifacts = event.get("artifacts", [])
    metadata = event.get("metadata", {})
    print(f"{prefix}🟢 [{event['event_id']}] {event['event_type']} | {event.get('timestamp', '-')}")
    print(f"{prefix}   Agent: {agent['id']} ({agent['type']})")
    print(f"{prefix}   Summary: {event['summary']}")
    if event.get("parent_event_ids"):
        print(f"{prefix}   Parents: {', '.join(event['parent_event_ids'])}")
    if metadata:
        print(f"{prefix}   Metadata:")
        for key, value in metadata.items():
            print(f"{prefix}     - {key}: {value}")
    if artifacts:
        print(f"{prefix}   Artifacts:")
        for artifact in artifacts:
            print(f"{prefix}     - URI: {artifact.get('uri', '-')}")
            if artifact.get("sha256"):
                print(f"{prefix}       SHA256: {artifact['sha256'][:16]}...")

def display_timeline(events):
    print("=" * 80)
    print(" VELUNEOS - EVENT LINEAGE TIMELINE PREVIEW")
    print("=" * 80)
    for event in sort_events(events):
        if event.get("parent_event_ids"):
            print(f"   │  Parent Link: {', '.join(event['parent_event_ids'])}")
            print("   ▼")
        else:
            print("   [ORIGIN ROOT]")
        print_event(event)
        print("-" * 80)

def display_backtrace(event_id, event_map):
    print("=" * 80)
    print(f" VELUNEOS - BACKTRACE FROM {event_id}")
    print("=" * 80)
    for depth, event in backtrace(event_id, event_map):
        prefix = "  " * depth
        connector = "↳ " if depth > 0 else ""
        print(f"{prefix}{connector}", end="")
        print_event(event)
        print("-" * 80)

def display_branches(event_id, event_map, children_map):
    print("=" * 80)
    print(f" VELUNEOS - DOWNSTREAM BRANCHES FROM {event_id}")
    print("=" * 80)
    for depth, event in branch_trace(event_id, event_map, children_map):
        prefix = "  " * depth
        connector = "↳ " if depth > 0 else ""
        print(f"{prefix}{connector}", end="")
        print_event(event)
        print("-" * 80)

def main():
    configure_stdout_encoding()
    parser = argparse.ArgumentParser(description="VeluneOS event-lineage traversal preview.")
    parser.add_argument("file", help="Path to JSONL event trace file")
    parser.add_argument("--event-type", help="Filter events by event_type")
    parser.add_argument("--event-id", help="Target event_id for backtrace or branch view")
    parser.add_argument("--backtrace", action="store_true", help="Trace parent lineage from event_id")
    parser.add_argument("--branches", action="store_true", help="Show downstream branches from event_id")
    parser.add_argument("--artifacts-only", action="store_true", help="Show only events with artifacts")
    args = parser.parse_args()
    events = validate_lineage_file(args.file)
    event_map, children_map = build_indexes(events)
    if args.backtrace:
        if not args.event_id:
            parser.error("--backtrace requires --event-id")
        display_backtrace(args.event_id, event_map)
        return
    if args.branches:
        if not args.event_id:
            parser.error("--branches requires --event-id")
        display_branches(args.event_id, event_map, children_map)
        return
    filtered = filter_events(events, event_type=args.event_type, artifacts_only=args.artifacts_only)
    display_timeline(filtered)

if __name__ == "__main__":
    main()

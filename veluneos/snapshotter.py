import argparse
import hashlib
import heapq
import json
from collections import deque
from pathlib import Path

from veluneos.validator import stream_events

__version__ = "0.2.2"


def sha256_file(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)

    return h.hexdigest()


def extract_window_streaming(input_path, trigger_event_id, pre, post):
    pre_buffer = deque(maxlen=pre)
    post_buffer = []

    trigger_event = None
    found_trigger = False

    for event in stream_events(input_path):
        if not found_trigger:
            if event["event_id"] == trigger_event_id:
                trigger_event = event
                found_trigger = True
            else:
                pre_buffer.append(event)
        else:
            post_buffer.append(event)

            if len(post_buffer) >= post:
                break

    if trigger_event is None:
        raise ValueError(f"Trigger event not found: {trigger_event_id}")

    return list(pre_buffer) + [trigger_event] + post_buffer, trigger_event


def topological_sort_timeline(window_events):
    event_map = {
        event["event_id"]: event
        for event in window_events
    }

    in_degree = {
        event["event_id"]: 0
        for event in window_events
    }

    adjacency = {
        event["event_id"]: []
        for event in window_events
    }

    for event in window_events:
        event_id = event["event_id"]

        for parent_id in event.get("parent_event_ids", []):
            if parent_id in event_map:
                adjacency[parent_id].append(event_id)
                in_degree[event_id] += 1

    heap = []
    counter = 0

    for event_id, degree in in_degree.items():
        if degree == 0:
            event = event_map[event_id]

            heapq.heappush(
                heap,
                (
                    event.get("timestamp", ""),
                    counter,
                    event_id,
                ),
            )

            counter += 1

    sorted_events = []

    while heap:
        _, _, current_id = heapq.heappop(heap)

        sorted_events.append(event_map[current_id])

        for next_id in adjacency[current_id]:
            in_degree[next_id] -= 1

            if in_degree[next_id] == 0:
                next_event = event_map[next_id]

                heapq.heappush(
                    heap,
                    (
                        next_event.get("timestamp", ""),
                        counter,
                        next_id,
                    ),
                )

                counter += 1

    if len(sorted_events) != len(window_events):
        return sorted(
            window_events,
            key=lambda event: (
                event.get("timestamp", ""),
                event["event_id"],
            ),
        )

    return sorted_events


def build_replay_graph(window_events):
    event_ids = {
        event["event_id"]
        for event in window_events
    }

    edges = []

    for event in window_events:
        for parent_id in event.get("parent_event_ids", []):
            if parent_id in event_ids:
                edges.append(
                    {
                        "from": parent_id,
                        "to": event["event_id"],
                    }
                )

    return {
        "event_ids": [
            event["event_id"]
            for event in window_events
        ],
        "edges": edges,
    }


def create_report(events, trigger_event):
    return {
        "trace_id": trigger_event["trace_id"],
        "trigger_event_id": trigger_event["event_id"],
        "trigger_event_type": trigger_event["event_type"],
        "trigger_severity": trigger_event["severity"],
        "event_count": len(events),
    }


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )


def write_jsonl(path, events):
    with open(path, "w", encoding="utf-8") as f:
        for event in events:
            f.write(
                json.dumps(event, ensure_ascii=False) + "\n"
            )


def create_manifest(out_dir):
    lines = [
        "VELUNEOS_PREVIEW_V0.2.2_MANIFEST",
        ""
    ]

    for path in sorted(out_dir.glob("*")):
        if path.is_file() and path.name != "MANIFEST_SHA256.txt":
            lines.append(
                f"{sha256_file(path)}  {path.name}"
            )

    manifest_path = out_dir / "MANIFEST_SHA256.txt"

    manifest_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    return manifest_path


def main():
    parser = argparse.ArgumentParser(
        description="Create an incident snapshot from JSONL lineage events."
    )

    parser.add_argument("input")
    parser.add_argument("--trigger-event-id", required=True)
    parser.add_argument("--pre", type=int, default=100)
    parser.add_argument("--post", type=int, default=50)
    parser.add_argument("--out", required=True)

    args = parser.parse_args()

    events, trigger_event = extract_window_streaming(
        args.input,
        args.trigger_event_id,
        args.pre,
        args.post,
    )

    events = topological_sort_timeline(events)

    replay_graph = build_replay_graph(events)

    report = create_report(events, trigger_event)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_jsonl(
        out_dir / "incident_events.jsonl",
        events,
    )

    write_json(
        out_dir / "replay_graph.json",
        replay_graph,
    )

    write_json(
        out_dir / "reconstruction_report.json",
        report,
    )

    create_manifest(out_dir)

    print("[+] snapshot created")


if __name__ == "__main__":
    main()

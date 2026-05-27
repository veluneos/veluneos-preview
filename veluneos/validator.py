import json
import logging

__version__ = "0.2.2"

logging.basicConfig(level=logging.INFO)

CORE_REQUIRED_FIELDS = [
    "event_id",
    "trace_id",
    "parent_event_ids",
    "timestamp",
    "event_type",
    "severity",
    "agent",
    "summary",
]


def stream_events(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        seen_event_ids = set()

        for line_number, line in enumerate(f, 1):
            line = line.strip()

            if not line:
                continue

            try:
                event = json.loads(line)

                for field in CORE_REQUIRED_FIELDS:
                    if field not in event:
                        raise ValueError(f"Missing field: {field}")

                if not isinstance(event["parent_event_ids"], list):
                    raise ValueError("parent_event_ids must be a list")

                if not isinstance(event["agent"], dict):
                    raise ValueError("agent must be an object")

                if event["event_id"] in seen_event_ids:
                    raise ValueError(f"Duplicate event_id: {event['event_id']}")

                seen_event_ids.add(event["event_id"])

                yield event

            except Exception as exc:
                logging.warning(
                    f"Line {line_number} skipped: {exc}"
                )

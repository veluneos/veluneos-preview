# VeluneOS Preview v0.2.2

Experimental replayable incident snapshot and event-lineage reconstruction preview.

This repository explores lightweight approaches for reconstructing event timelines from JSONL lineage logs.

## Features

- streaming JSONL parser
- incident window extraction
- stable topological replay ordering
- replay graph generation
- reconstruction report generation
- SHA256 integrity manifest generation

## Concept

```text
Continuous Events
→ Trigger Event
→ Incident Window
→ Stable Replay Ordering
→ Replay Graph
→ Reconstruction Report
→ Integrity Manifest
```

## Run

```bash
python -m veluneos.snapshotter examples/continuous_event_log.jsonl \
  --trigger-event-id EVT-1004 \
  --pre 3 \
  --post 2 \
  --out snapshots/demo_incident
```

## Output

```text
snapshots/demo_incident/
├── incident_events.jsonl
├── replay_graph.json
├── reconstruction_report.json
└── MANIFEST_SHA256.txt
```

## Scope

This is an experimental preview prototype and not production-ready.

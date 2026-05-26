# VeluneOS GitHub Preview v0.2.1

Experimental event-lineage traversal and replay preview for AI / agent / robotics workflows.

VeluneOS is **not** a runtime engine, robotics operating system, orchestration framework, or replacement for existing observability tools.

This preview is intentionally small:

- JSONL event examples
- lightweight validation
- event lineage traversal
- trace filtering
- artifact reference display
- branch-aware terminal visualization
- safer UTF-8 terminal output handling for Windows

## What this is

A minimal preview tool for inspecting event lineage after a workflow has already produced logs.

It helps answer:

- What happened?
- Which event came before this one?
- Which downstream events branched from it?
- Which artifacts were linked to the event?
- Can we filter a trace by event type or event id?

## What this is not

VeluneOS does not replace:

- rosbag2
- ros2_tracing
- PlotJuggler
- Foxglove Studio
- OpenTelemetry
- LangSmith
- AgentOps
- runtime control systems
- orchestration frameworks

This preview does **not** perform real-time control, scheduling, inference, policy enforcement, or runtime intervention.

## Quick start

```bash
python -m veluneos.replayer examples/multi_agent_trace.jsonl
```

Filter by event type:

```bash
python -m veluneos.replayer examples/multi_agent_trace.jsonl --event-type llm_inference
```

Trace backward from a specific event:

```bash
python -m veluneos.replayer examples/multi_agent_trace.jsonl --event-id EVT-1004 --backtrace
```

Show downstream branches from a specific event:

```bash
python -m veluneos.replayer examples/multi_agent_trace.jsonl --event-id EVT-1001 --branches
```

Show only artifact-linked events:

```bash
python -m veluneos.replayer examples/multi_agent_trace.jsonl --artifacts-only
```

## Design stance

Core event lineage fields are kept small and boring. Contextual fields remain optional.

The goal is not to prove a grand standard. The goal is to make event lineage easy to inspect, traverse, and replay from simple JSONL logs.

## Current limitations

This is a preview tool.

It does not yet include:

- real ROS2 adapter
- OpenTelemetry bridge
- binary protobuf support
- large-scale graph storage
- real-time streaming
- dashboard UI
- compliance certification
- audit authority claims

# Design Decisions

## Detecting readiness for dispatch
- The orchestrator loads each active workflow and inspects every node's stored status. Nodes missing status are initialized to `PENDING` for a clean first pass.
- A node is eligible for dispatch only when it is `PENDING` **and** every dependency has reached `COMPLETED`, checked via `all_dependencies_succeeded`. This keeps retries or straggler runs from double-enqueuing tasks.
- Before enqueueing, the orchestrator resolves templated configs (e.g., `{{ upstream.value }}`) against previously stored outputs, so workers receive fully materialized payloads.
- Runnable nodes transition to `QUEUED` and are pushed onto the Redis stream alongside handler/config metadata. Workers subsequently mark them `RUNNING` → `COMPLETED`/`FAILED` as they execute handlers.

## Handling fan-in
- Fan-in is implicit in the dependency checks: a node with multiple dependencies remains `PENDING` until **all** upstream nodes report `COMPLETED`.
- Because readiness is recomputed on every scheduler loop, the orchestrator naturally unlocks downstream fan-in nodes once the slowest prerequisite finishes—no special coordination is required.
- Completion monitoring treats any `RUNNING` or `QUEUED` node as evidence that the workflow is still active, ensuring fan-in nodes are only considered after upstream work drains.

## Trade-offs
- **Polling scheduler loop:** A simple sleep-based loop keeps orchestration logic understandable but introduces latency between a node finishing and the next dispatch window. Tightening `sleep_seconds` reduces lag at the cost of Redis chatter/CPU.
- **Redis Streams as the task bus:** Using a single stream with consumer groups provides durability and horizontal worker scaling but follows an at-least-once delivery model. Handlers and status transitions should remain idempotent to absorb replays.
- **Status gating over lock-based scheduling:** Relying on node status checks instead of locks simplifies the scheduler, but missing or corrupted status entries can temporarily block readiness until corrected.
- **Immediate template resolution:** Performing template substitution before enqueueing ensures workers are stateless, yet it also means late-arriving upstream outputs require another scheduler pass to refresh and dispatch dependent nodes.

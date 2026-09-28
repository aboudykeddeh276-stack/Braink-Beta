-- D-030 production lease/zombie recovery
-- Runs inside one transaction and uses SKIP LOCKED to avoid duplicate recovery work.
\set ON_ERROR_STOP on
BEGIN;

WITH expired AS (
  SELECT critique_slot_id, task_id, slot_index, assigned_worker_id
  FROM critique_slots
  WHERE slot_state = 'LEASED'
    AND lease_expires_at IS NOT NULL
    AND lease_expires_at < clock_timestamp()
  FOR UPDATE SKIP LOCKED
),
recovered AS (
  UPDATE critique_slots cs
  SET slot_state = 'PENDING',
      assigned_worker_id = NULL,
      lease_expires_at = NULL
  FROM expired e
  WHERE cs.critique_slot_id = e.critique_slot_id
  RETURNING e.critique_slot_id, e.task_id, e.slot_index, e.assigned_worker_id
)
SELECT count(*) AS recovered_critique_leases FROM recovered;

-- Retrigger packets are never marked dispatched merely because they are old.
-- Only packets with no execution binding remain eligible for the executor.
UPDATE global_workbook_tasks gwt
SET current_turn_state = 'RETRIGGER_QUEUED',
    updated_at = clock_timestamp()
WHERE current_turn_state = 'EXECUTION_BOUND'
  AND EXISTS (
    SELECT 1
    FROM agent_retrigger_packets arp
    WHERE arp.task_id = gwt.task_id
      AND arp.dispatched_status = FALSE
  );

COMMIT;

# AegisQA Architecture Notes

## Current Milestone

The current codebase implements the first executable spine:

```text
load_ticket
  -> requirement_agent
  -> coverage_planner
  -> test_case_generator
  -> test_data_resolver
  -> automation_generator
  -> validator
  -> human_approval
  -> report_generator
```

The implementation intentionally uses fake ticket input and deterministic stub
logic. That keeps the state contract easy to test before adding LLM calls,
memory retrieval, Jira/Azure DevOps, human approval, execution, and full
reporting.

The automation milestone writes minimal Robot Framework files under
`generated/robot/<ticket-id>/`. The validator node runs `robot --dryrun`,
checks generated artifacts, and stores the result in `TestContext.automation`.
The human approval node creates a `pending_review` approval block. Workflow
contexts are persisted under `generated/contexts/` so the API can later approve
or request changes. A `request_changes` decision records reviewer feedback,
regenerates Robot files, reruns validation, and returns the workflow to
`pending_review` with a higher automation revision. On approval, AegisQA
attempts real Git execution:
create/switch to the `aegis/<ticket-id>` branch, stage the generated Robot
files, commit them, and create a PR with `gh pr create` when the GitHub CLI is
available. Every attempt writes a result payload under `generated/git_handoff/`.
If the project is not inside a Git work tree, the approval remains recorded and
Git status is marked blocked with the reason. Approval decisions, Git attempts,
workflow starts, and generated-file reads are also written to
`generated/audit/events.jsonl`.

## Next Boundary

The next useful boundary is review UI and integrations:

- Add a small dashboard/review UI over the existing API.
- Add real Jira/Azure ticket loading behind the existing fake ticket boundary.
- Move file-backed context/audit storage to a database.
- Install/authenticate GitHub CLI for automatic PR creation.

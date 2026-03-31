# Phase 2 - Data Model & System Design

SQLite schema implemented with:
- `users`
- `medicines`
- `sales`
- `sale_items`
- `short_list` view

## Constraints
- `UNIQUE(name, batch_no)` for medicine batch uniqueness.
- `exp_date > mfg_date` enforced in service validation.
- Non-negative quantities/rates via DB checks.
- Sale quantity cannot exceed stock in service logic.
- Payment mode required (`cash` or `online`).

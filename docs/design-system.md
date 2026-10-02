# SalesSnap visual identity and design system

SalesSnap uses a dark, data-focused interface intended to feel calm, exact, and trustworthy. This document helps designers and developers understand the product experience; permanent implementation rules live in [`Skills/design-system-standards.md`](../Skills/design-system-standards.md).

## Identity

The logo combines an ascending commercial data path with the SalesSnap wordmark. Teal signals the primary product action and healthy analytical momentum; indigo adds depth for advanced intelligence and AI contexts.

| Role | Token | Purpose |
| --- | --- | --- |
| Canvas | `--canvas` | Main application background |
| Surface | `--surface` | Cards and desktop sidebar |
| Raised surface | `--surface-raised` | Drawers, dialogs, elevated areas |
| Border | `--stroke` | Subtle separation between layers |
| Primary | `--brand` | Primary actions, focus, active navigation |
| Accent | `--accent` | Supporting analytical emphasis |
| Success | `--success` | Successful or healthy outcomes |
| Warning | `--warning` | Partial results and attention states |
| Danger | `--danger` | Errors and destructive intent |

Typography uses a system-first sans-serif stack for speed and familiarity. Monospace is limited to identifiers, code, and import column names. The interface favors compact labels, clear hierarchy, and legible numbers.

## Component inventory

Shared React primitives live in `apps/web/components/ui/`.

| Component | Typical use |
| --- | --- |
| `Button` | Primary, secondary, ghost, and dangerous actions |
| `Input`, `Select`, `Textarea` | Consistent labeled form controls |
| `Card` | Grouped content and analytical panels |
| `PageHeader` | Page title, context, description, and leading action |
| `Badge` | Status, count, or compact metadata |
| `Alert` | Inline information, success, warning, or error |
| `LoadingState` | Awaiting protected or analytical data |
| `EmptyState` | No source data or no matching result |
| `ErrorState` | Failed retrieval with optional retry |
| `TableFrame`, `Table` | Responsive tabular information |
| `Modal` | Deliberate confirmation for interruptive actions |

Sales and inventory imports demonstrate success, partial-success, warning, and error patterns. The dashboard demonstrates loading, error, empty, KPI cards, responsive filters, chart presentation, and tabular data.

## Information architecture

The application shell organizes capabilities by the decision users are making:

```text
Overview     → current business performance
Data         → sales and inventory inputs
Intelligence → segmentation, forecasting, anomalies, stock risk
AI workspace → generated insights and evidence-backed conversation
```

On desktop, the sidebar remains available while users analyze data. A sticky header identifies the active company and account. On mobile, the same hierarchy appears in a drawer opened from a compact header. Public and authentication pages remain outside this shell.

## Interaction states

Data-driven pages must never collapse into an unexplained blank state. They show descriptive loading feedback, recoverable errors, actionable empty states, explicit success, warnings for partial results, and a clear unavailable state for disabled optional services such as AI.

Focus rings, labels, semantic current-page state, minimum touch targets, keyboard-accessible dialogs, and non-color status text form the accessibility baseline.

## Development checklist

Before merging an interface change:

1. Reuse or deliberately extend an existing primitive.
2. Verify loading, error, empty, success, warning, and unavailable states that apply.
3. Confirm company and tenant context remains accurate.
4. Run `npm run lint -- --max-warnings=0`.
5. Run `npm run build`.
6. Inspect the affected flow at mobile and desktop breakpoints.

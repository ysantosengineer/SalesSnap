# Design system standards

This Skill is the permanent source of truth for SalesSnap visual identity, interface primitives, application navigation, and interaction states. Read it before changing any frontend UI.

## Product personality

SalesSnap is calm, precise, confident, and analytical. The interface should make complex commercial signals feel understandable and trustworthy. Avoid playful consumer patterns, excessive decoration, futuristic AI clichés, neon-heavy styling, and motion that competes with data.

Use concise action-oriented copy. Prefer specific labels such as `Import sales data` and `Apply filters` over generic labels such as `Continue` or `Submit`.

## Visual identity

- The primary mark is the code-native ascending data-path symbol in `components/brand.tsx`.
- Dark navy is the default application canvas; layered navy surfaces establish hierarchy.
- Teal is the primary brand and action color. Indigo is a supporting analytical accent.
- Emerald, amber, and rose are semantic colors for success, warning, and danger. Do not use them as arbitrary decoration.
- Use semantic CSS custom properties from `app/globals.css` instead of scattering new color values.
- Use the system-first sans-serif stack for interface copy and tabular numerals. Use monospace only for code, external identifiers, and machine-readable field names.
- Icons use a consistent 20–24 px outline style. Decorative icons are `aria-hidden`; controls with only an icon require an accessible label.

## Layout and spacing

- Use a 4 px-derived spacing rhythm and the existing Tailwind scale.
- Cards use layered surfaces, subtle borders, restrained shadows, and rounded corners.
- Content pages use a readable maximum width with responsive horizontal padding.
- Dense data remains scannable: align numeric values, keep labels short, and place wide tables in horizontal scroll frames.
- Touch targets should normally be at least 44 px high or wide.

## Shared components

Reusable primitives live in `apps/web/components/ui/`:

- `Button` owns button variants, sizes, disabled state, focus state, and minimum targets.
- `Input`, `Select`, `Textarea`, and `FieldLabel` own form-control appearance.
- `Card` and `PageHeader` establish page hierarchy.
- `Badge` communicates compact status or category metadata.
- `Alert`, `LoadingState`, `EmptyState`, and `ErrorState` communicate application state.
- `TableFrame` and `Table` provide responsive, consistent tabular presentation.
- `Modal` is reserved for interruptive decisions such as destructive actions or signing out.

Extend an existing primitive when a repeated need appears. Do not force unrelated behaviors into one component, and do not create abstractions without real usage.

## Required states

Every data-driven view must intentionally handle:

- loading, with a descriptive status label;
- error, with a useful message and retry when recovery is possible;
- empty, explaining why the screen is empty and offering a next action;
- success, confirming the completed operation;
- partial success or warning, preserving accepted work while explaining rejected items;
- unavailable or disabled capability, explaining the configuration or dependency without implying data loss.

Never use a blank screen as a state. Do not rely on color alone to convey meaning.

## Navigation architecture

Authenticated navigation is grouped by user intent:

```text
Overview
  Dashboard

Data
  Import sales
  Inventory

Intelligence
  Customer segments
  Demand forecast
  Anomalies
  Stock risk

AI workspace
  AI insights
  AI chat
```

Desktop uses a persistent sidebar and sticky company header. Mobile uses a compact header and dismissible drawer. The current route must be visually and semantically identified with `aria-current`. Company context and signed-in user context must remain visible without turning the header into a second navigation system.

Public landing and authentication pages do not render the authenticated application shell.

## Accessibility and interaction

- Inputs require explicit labels; placeholders do not replace labels.
- Keyboard focus must remain visible.
- Dialogs require a title, `role="dialog"`, `aria-modal`, Escape support, and an explicit cancel path.
- Drawers and overlays require accessible open and close controls.
- Preserve sufficient text and control contrast against each surface.
- Prefer reduced, purposeful transitions. Do not make essential information dependent on hover.
- Responsive behavior must be visually checked at mobile and desktop breakpoints in addition to lint and build validation.

## Boundaries

The frontend presents results returned by the backend; it does not duplicate analytics, ML rules, tenancy decisions, or authorization. The design system must not introduce a third-party component framework unless a demonstrated need justifies the dependency and the decision is documented here.

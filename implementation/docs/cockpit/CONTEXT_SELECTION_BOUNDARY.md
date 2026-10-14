# Context selection boundary

`context/context_selection.js` provides a read-only Cockpit projection for explicit context selection.

It may:

- query authorized Agency Data resources through the Context Resolver binding;
- display candidates and provider errors;
- retain explicit user selections for the current browser session;
- emit the selected entity identities to the handoff surface.

It must not:

- widen scope implicitly;
- convert retrieval into truth or Evidence;
- write Agency Data;
- admit, authorize, schedule or dispatch Hermes execution.

```text
selected != Evidence
retrieved != truth
context addition != implicit scope widening
```

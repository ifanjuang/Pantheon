# Radix Icons — MVP semantic selection

Status: active native Cockpit presentation binding.

This file records the mapping between existing MVP Cockpit icon keys and the pinned Radix SVG set. It is a rendering convention only: the underlying governed object, status and label remain authoritative.

| Cockpit key | Radix asset | Intended presentation |
|---|---|---|
| `document` | `file-text.svg` | project document / derived document card |
| `knowledge` | `reader.svg` | Knowledge item / reference reading |
| `work` | `backpack.svg` | work item / professional task |
| `questionnaire` | `question-mark-circled.svg` | questionnaire / clarification request |
| `source` | `link-2.svg` | source relation / provenance link |
| `review` | `check-circled.svg` | review affordance; never approval by itself |
| `scope` | `target.svg` | declared scope / bounded perimeter |
| `memory` | `archive.svg` | retained/archive-related projection; never automatic memory admission |
| `history` | `counter-clockwise-clock.svg` | history / trace navigation |
| `decision` | `commit.svg` | explicit decision record / decision point |
| `hermes` | `lightning-bolt.svg` | Hermes/runtime-side activity indication |
| `comment` | `chat-bubble.svg` | comment / discussion |
| `project` | `home.svg` | project navigation identity |
| `evidence` | `badge.svg` | Evidence-related projection; visible label/status remains required |
| `gate` | `lock-closed.svg` | Gate/control threshold; icon does not imply blocked or satisfied state |
| `close` | `cross-2.svg` | close/dismiss Cockpit detail surface |

## Activation

The shared tag renderer emits semantic `.radix-icon` elements directly; `styles/cards.css` resolves those keys to vendored SVG assets using `currentColor` masks. There is no post-bootstrap replacement layer and no legacy inline SVG fallback.

## Semantic constraints

```text
icon != object identity
icon != status
check icon != approval
lock icon != blocked
badge icon != validated evidence
archive icon != memory admission
lightning icon != runtime success
```

Any future mapping change is a Cockpit UX change. It does not modify Pantheon doctrine, authorize an action, activate Hermes, or change the lifecycle of the underlying governed object.

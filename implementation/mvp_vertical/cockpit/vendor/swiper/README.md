# Swiper presentation dependency

Cockpit V2 currently loads the browser bundle and stylesheet for Swiper `14.0.7` from jsDelivr.

This dependency is presentation-only:

```text
Swiper movement != navigation authority
visible card != selected Evidence
slide transition != workflow transition
```

`PantheonSpatialNavigation` remains the source of the current collection, sibling index and hierarchy. Swiper only translates a horizontal gesture into the existing previous/next controls. Buttons and keyboard navigation remain available.

A later reviewed materialization may vendor the pinned assets locally if offline operation becomes a requirement.

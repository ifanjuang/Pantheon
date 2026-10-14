# Cockpit entrypoint contract

`index.html` loads `cockpit_bootstrap.js`.

Live mode delegates to `live_bootstrap.js`, which loads `live_collection_adapter.js` before the classic renderer and loads `shell_controls.js` as the shell-only interaction module.

The retired filenames `v3_bootstrap.js`, `v2_bootstrap.js`, `v3_swiper.js` and `v2_shell_controls.js` are not part of the active or published contract.

Functional `v2-*` DOM identifiers remain temporarily active and are migrated separately with all consumers.

# Cockpit classic-script loading boundary

`boot/classic_script_loader.js` owns only the mechanical loading of ordered classic browser scripts.

It may create `<script>` elements, append them to a caller-provided parent and preserve source order. It must not select application modules, acquire Swiper, project boot failures, fetch domain data, dispatch Hermes, authorize actions or interpret Pantheon objects.

`live_bootstrap.js` remains responsible for choosing the ordered source list and starting the Cockpit. `navigation/swiper_loader.js` remains responsible for optional Swiper acquisition. `v3/collection/motion_adapter.js` remains the sole Swiper instance and navigation API boundary.

```text
script loaded != module approved
load success != runtime Evidence
UI startup != authorization
```

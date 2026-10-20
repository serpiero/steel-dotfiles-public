# RuTracker search layout

Install `rutracker.user.js` in Tampermonkey. It changes the forum homepage and tracker search results, and hides scrollbars across the site without disabling scrolling.

The homepage shows the native logo and native quick-search form in a centered layout. Results use a compact search header, with advanced options collapsed on every new page. **Advanced search** opens the original form without clearing its fields. For Visual Enhancer 1, **View options**, beside it, starts closed and reveals Visual view, S/M/L, Light/Dark and Infinite scroll. Filter, Columns and the seeded-only checkbox (SO) remain visible above the results. The floating Light/Dark widget is hidden on the homepage. The Tampermonkey menu **Toggle original RuTracker layout** restores the original page for the current visit.

Visual Enhancer 2 retains its own VE button, controls, placement, palette and saved preferences. The script does not restyle or rearrange this version.

For Visual Enhancer 1, the optional script adapts the existing extension controls in place and shares the Steel palette with their buttons, badges and cards. It preserves the original control nodes, listeners, filters, saved extension settings and results. Common native interface labels are translated locally to English; titles, descriptions and messages are left as written. No translator service is contacted. Topic, login and other forum pages retain their layout. It moves the live search form so native handlers and hidden fields stay intact. If the expected markup is missing, it restores the native layout after a short timeout.

Colors come from the shared Steel palette. Edit `themes/steel.json` or `local-theme.json`, run `python3 theme.py`, and reinstall the generated script after palette changes. Edit `rutracker.user.js.in` for layout changes; `rutracker.user.js` is generated. No background polling, network prefetching or personal page data is added.

# Browser review

The desktop and mobile Chrome tests opened the full frozen map from a local HTTP server. They exercised title, author and paper-ID searches, canvas selection, the alphaXiv link, on-demand abstract text, related-paper navigation, deep links, zoom, reset, the CSV download, and switching between editions. Topic, subject, year and minimum-like filters were also tested together against an independent count from the public point index. [Browser test](../../../tests/browser_smoke.py)

The UMAP, PCA and shuffled selectors displayed the corresponding full-corpus recall from the saved display-seed measurements. Inspection of the desktop and phone screenshots confirmed that the projection control, visible count, map, topic list and export link fit both layouts. The phone test also opened a paper after searching for its ID. [Desktop screenshot](browser-desktop.png) · [Mobile screenshot](browser-mobile.png) · [Walkthrough](../../../docs/over-10/walkthrough.mp4)

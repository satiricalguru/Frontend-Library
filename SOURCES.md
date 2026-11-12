<div align="center">

# 🧾 Source tracker

Every entry in this library records the **exact page it was taken from**.

<sub><b>3,870</b> tracked entries · machine-readable log: <a href="data/sources.csv">data/sources.csv</a> · raw data: <a href="data/">data/</a></sub>

</div>

## 📍 Where each library file came from

| Library file | Entries | Exact pages collected from |
|:--|--:|:--|
| [inspiration/lusion/README.md](inspiration/lusion/README.md) | 36 | <https://lusion.co/projects><br><https://labs.lusion.co/> |
| [styles/refero-design-systems/README.md](styles/refero-design-systems/README.md) | 1,342 | <https://styles.refero.design/><br><https://styles.refero.design/sitemaps/styles.xml> |
| [animations/motion-dev/README.md](animations/motion-dev/README.md) | 616 | <https://motion.dev/examples><br><code>https://motion.dev/examples?category=<name> (27 category pages)</code><br><https://motion.dev/sitemap.xml> |
| [animations/transitions-dev/README.md](animations/transitions-dev/README.md) | 44 | <https://transitions.dev/><br><https://transitions.dev/sitemap.xml> |
| [inspiration/godly/README.md](inspiration/godly/README.md) | 434 | <https://godly.design/><br><https://godly.design/websites><br><https://godly.design/hero><br><https://godly.design/cta><br><https://godly.design/footer><br><https://godly.design/tools><br><https://godly.design/resources> |
| [templates/godly-templates/README.md](templates/godly-templates/README.md) | 163 | <https://godly.design/templates><br><https://godly.design/sitemap.xml> |
| [fonts/envato-award-fonts/README.md](fonts/envato-award-fonts/README.md) | 1,225 | <https://elements.envato.com/fonts/awards><br><https://elements.envato.com/fonts/awards/pg-2><br><https://elements.envato.com/fonts/awards/pg-3><br><https://elements.envato.com/fonts/awards/pg-4><br><https://elements.envato.com/fonts/awards/pg-5><br><https://elements.envato.com/fonts/awards/pg-6><br><https://elements.envato.com/fonts/awards/pg-7><br><https://elements.envato.com/fonts/awards/pg-8><br><https://elements.envato.com/fonts/awards/pg-9><br><https://elements.envato.com/fonts/awards/pg-10><br><https://elements.envato.com/fonts/awards/pg-11><br><https://elements.envato.com/fonts/awards/pg-12><br><https://elements.envato.com/fonts/awards/pg-13><br><https://elements.envato.com/fonts/awards/pg-14><br><https://elements.envato.com/fonts/awards/pg-15><br><https://elements.envato.com/fonts/awards/pg-16><br><https://elements.envato.com/fonts/awards/pg-17><br><https://elements.envato.com/fonts/awards/pg-18><br><https://elements.envato.com/fonts/awards/pg-19><br><https://elements.envato.com/fonts/awards/pg-20><br><https://elements.envato.com/fonts/awards/pg-21><br><https://elements.envato.com/fonts/awards/pg-22><br><https://elements.envato.com/fonts/awards/pg-23><br><https://elements.envato.com/fonts/awards/pg-24><br><https://elements.envato.com/fonts/awards/pg-25><br><https://elements.envato.com/fonts/script-and-handwritten/awards/pg-3><br><https://elements.envato.com/fonts/script-and-handwritten/awards/pg-4><br><https://elements.envato.com/fonts/script-and-handwritten/awards/pg-5><br><https://elements.envato.com/fonts/script-and-handwritten/awards/pg-6> |
| [animations/snippets/README.md](animations/snippets/README.md) | 10 | <https://motion.dev/examples/js-split-text><br><https://motion.dev/examples/react-cursor-magnetic><br><https://transitions.dev/transitions/error-state-shake/><br><https://transitions.dev/transitions/like-button/><br><https://transitions.dev/transitions/number-pop-in/><br><https://transitions.dev/transitions/shimmer-text/><br><https://transitions.dev/transitions/skeleton-loader-and-reveal/><br><https://transitions.dev/transitions/success-check/><br><https://transitions.dev/transitions/tabs-sliding/><br><https://transitions.dev/transitions/toggle/> |

## 🌍 Source sites

| Site | What we index | Terms to respect |
|:--|:--|:--|
| [lusion.co](https://lusion.co/) | Case studies + Labs experiments | Links only; all work © Lusion |
| [styles.refero.design](https://styles.refero.design/) | Brand palettes, typefaces, style pages | Links + factual color/font data; DESIGN.md files stay on Refero |
| [motion.dev](https://motion.dev/) | Examples + UI components | Motion library is MIT; example pages © Motion |
| [transitions.dev](https://transitions.dev/) | Transition library | Links only (custom license); our own versions live in `animations/snippets/` |
| [godly.design](https://godly.design/) | Websites, sections, templates, tools, resources | Links only; designs © their owners |
| [elements.envato.com/fonts/awards](https://elements.envato.com/fonts/awards) | Premium award fonts | Names + links only; fonts need an Envato licence |

## 🔍 Find the source of any entry

```bash
# which page did "Linear" come from?
grep -i '"Linear"\|,Linear,' data/sources.csv
```

Columns: `library_file, name, item_url, taken_from, collected`.

## ♻️ Rebuild

```bash
python3 scripts/build-catalog.py
```

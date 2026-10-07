=== Tavoos Article TOC ===
Tags: table of contents, headings, accessibility, rtl
Requires at least: 6.2
Tested up to: 6.8.3
Requires PHP: 7.4
Stable tag: 1.0.0
License: GPL-2.0-or-later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

An accessible, expandable article table of contents. Local assets, Persian and English translations, RTL support, and no tracking.

== Description ==

Tavoos Article TOC builds a navigation box from article headings. It does not summarize prose or use AI. Article text and saved heading IDs are never rewritten in the database.

By default, it runs on single posts containing at least three H2 headings. The box appears immediately before the first eligible heading, opens on desktop (768px and up), and stays collapsed on smaller screens. Native details/summary controls support keyboard operation.

Features:

* Heading levels H2-H6, public post types, threshold, title, position, expansion, and scroll offset settings.
* Scoped WordPress content detection with an optional article-body CSS selector for custom themes.
* Preserved authored IDs, collision-safe Unicode anchors, and safe aliases for duplicate authored IDs.
* Keyboard focus moves to the selected heading; reduced motion produces immediate scrolling.
* Native browser smooth scrolling with no animation loops; fragment history supports Back and Forward.
* Persian and English catalogs; logical CSS properties for RTL and LTR.
* No external API, CDN, fonts, telemetry, cookies, or visitor storage.
* Local files and small dependency-free JavaScript, loaded only for eligible singular content.

The plugin requires JavaScript. With JavaScript disabled, the article remains readable without a table of contents. Themes must call wp_head(), wp_footer(), and normally the_content(). Where the_content() is bypassed, set the custom article-body selector; never target body or html. A malformed selector results in no table.

Heading links are a flat ordered list with visual indentation for selected subheading levels. Headings inside nav, aside, footer, header, hidden/aria-hidden regions, .tvs-upd, .tvs-rel, .tavoos-toc-exclude or [data-tavoos-toc-exclude] are excluded. Content added after page load requires the documented refresh event.

== Installation ==

1. Upload tavoos-article-toc.zip under Plugins > Add New > Upload Plugin, or copy the tavoos-article-toc folder into wp-content/plugins.
2. Activate Tavoos Article TOC.
3. Open Settings > Article TOC. The defaults work for normal single posts.
4. Test on staging with your theme before enabling it on a live site.

== Frequently Asked Questions ==

= Does this send my content to an AI service? =

No. This is a heading-based table of contents. It makes no external requests.

= What happens if the original Tavoos snippet is still enabled? =

The plugin detects .tvs-toc or script#tvs-toc anywhere in the page and does not add a second table. It also removes its own table if delayed legacy markup appears. It does not edit or disable any other plugin or snippet. The original HFCM snippets may contain unrelated code; remove only the TOC-specific JavaScript and CSS after a separate, approved migration. As long as the legacy code remains, this plugin intentionally yields to it, so its settings do not control the old table.

= Why is there no table on an article? =

Check that display is enabled, the post type is selected, the article has enough eligible headings, JavaScript is enabled, and there is no legacy table/script. Archives, feeds, embeds, previews, password-locked content, and REST responses are not enhanced. For a theme that bypasses the_content(), set a valid article-body selector. CSS-hidden responsive copies may require a more specific selector.

= Can I omit headings? =

Add class tavoos-toc-exclude or the attribute data-tavoos-toc-exclude to a heading or its enclosing group. Existing navigation, sidebar, header, footer, hidden and legacy related-content regions are excluded automatically.

= Can a page builder refresh the table after changing content? =

Yes. After replacing/inserting article content, dispatch document.dispatchEvent(new Event('tavoos-toc:refresh')). The page must already be an eligible singular request with this plugin's assets loaded. This plugin does not continuously rescan changing content.

= How are existing and duplicate IDs handled? =

A heading's unique existing ID is retained, including Persian text and special characters. New IDs are prefixed with tavoos-toc- and are checked against the whole document. If an authored heading ID collides with an earlier element, a separate anchor is inserted next to that heading. The plugin's links target that alias, leaving the authored ID unchanged. It does not repair malformed source markup or resolve pre-existing duplicate IDs in other links.

= What settings are stored? =

One WordPress option, tavoos_article_toc_options. It holds display settings only. Deactivation keeps it; deletion removes it for the current site. On multisite, remove settings on each site before a network-wide uninstall if full cleanup is required. No article content or visitor data is stored.

= Is the directory slug reserved or publication approved? =

No. This ZIP uses the proposed slug tavoos-article-toc. WordPress.org availability, ownership, username, and final directory review must be verified separately before submission. This package is not a publication or approval claim.

== Screenshots ==

1. Display settings: heading levels, threshold, placement, expansion, and scroll offset.
2. An automatically generated table of contents in a Persian article.

== Changelog ==

= 1.0.0 =
* First standalone release with configurable, accessible, bilingual article navigation.

== Upgrade Notice ==

= 1.0.0 =
Standalone first release. The legacy TOC must be migrated separately; never disable entire HFCM snippets blindly.

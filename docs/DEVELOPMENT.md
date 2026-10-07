# Development

The runtime plugin has no npm or Composer dependencies. Node and Playwright are only used for development checks and are excluded from the release ZIP. The source was imported from the owner's `tavoos-article-toc-1.0.0.zip`; runtime PHP, JS, CSS and translation files are preserved.

## Checks

```sh
npm ci
npx playwright install chromium
npm test
python3 tools/build-release.py
find . -name '*.php' -not -path './node_modules/*' -print0 | xargs -0 -n1 php -l
node --check assets/toc.js
```

For a preinstalled browser, set `CHROMIUM_PATH=/usr/bin/chromium`. The fixture suite has 12 functional checks. To add the live-site check, set `WP_BASE_URL` and `WP_POST_ID` to a staging site with a published article containing three eligible H2 headings. For the optional Settings API save/reload test, set `WP_TEST_CREDENTIALS` to a local JSON file with `username` and `password` keys; never commit credentials. The settings test temporarily changes the TOC title and restores it on success; use a disposable staging site.

## Prepared cloud machine

This cloud task already provides an isolated checkout at `/workspace/tavoos-article-toc`. Use it directly; do not create a worktree unless explicitly requested.

- PHP CLI wrapper: `/workspace/.tavoos-tools/php-cli` (PHP 8.4.24, locally extracted Debian packages, authenticated APT index and checksum verification retained).
- WordPress staging root: `/workspace/.tavoos-tools/wordpress` (6.8.3).
- SQLite adapter: `/workspace/.tavoos-tools/sqlite`, commit `d0a5d8cc2cce990a692041d9a881a70125695d35`. This is a development-only database; it is not shipped with the plugin.
- Browser: `/usr/bin/chromium` with Playwright 1.62.1 from the npm lockfile.
- Local fixture credentials: `/workspace/.tavoos-tools/admin.json`, generated for this disposable site and excluded from the repository.

Restart the local staging server when needed:

```sh
/workspace/.tavoos-tools/php-cli -S 127.0.0.1:8080 -t /workspace/.tavoos-tools/wordpress
```

In another terminal, from the repository root:

```sh
CHROMIUM_PATH=/usr/bin/chromium \
WP_BASE_URL=http://127.0.0.1:8080 \
WP_POST_ID=4 \
WP_TEST_CREDENTIALS=/workspace/.tavoos-tools/admin.json npm test
```

These loopback addresses are for internal requests, not user-facing preview links. The prepared PHP/runtime/database files are retained filesystem state; the PHP server process must restart in a future task. SMTP is not configured; outgoing mail is unnecessary for this plugin. Core Persian language-pack download returned HTTP 403; screenshots therefore use the real English core admin UI with Persian article content. The bundled Persian MO catalog was loaded and its translated output verified independently.

## Validation on 2026-10-07

- PHP syntax: all three shipped PHP files passed on 8.4.24.
- JavaScript syntax passed.
- 12 fixture browser checks plus live article and real Settings API save/reload: 14 passed, zero browser exceptions.
- Persian catalog translation verified: `In this article` → `فهرست مطالب این مقاله`.
- Runtime ZIP: archive integrity, expected top-level directory, stable tag/version consistency and reproducible output checked.
- The built ZIP was uploaded through WordPress's actual plugin installer; installation succeeded and the activated plugin produced three article links.
- Screenshots captured from the real WordPress site; directory image dimensions checked.

Minimum PHP 7.4 / WordPress 6.2 behavior, latest stable WordPress, multisite, Plugin Check and official readme validation remain release-owner checks. CI includes PHP 7.4 and 8.4 syntax checks; adding the workflow does not claim a remote CI run passed. The initial `Tested up to: 7.1` claim was replaced with the locally exercised 6.8.3 version.

## Release contents

`tools/build-release.py` reads the version from the plugin header and includes only the four root runtime/readme/license files and `assets`, `includes`, `languages`. It uses fixed timestamps for reproducible ZIPs. GitHub documentation and WordPress.org images stay outside the installable ZIP. `wordpress-org` files belong in the root `assets` directory of the approved WordPress.org SVN repository, not in the plugin's runtime `assets` directory.

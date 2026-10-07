/* Tavoos Article TOC 1.0.0 | GPL-2.0-or-later */
(function () {
    'use strict';

    var config = window.tavoosArticleTOC;
    if (!config || window.tavoosArticleTOCStarted) return;
    window.tavoosArticleTOCStarted = true;

    var nav = null;
    var observer = null;
    var targets = new Map();
    var aliases = new WeakMap();
    var legacySelector = '.tvs-toc, script#tvs-toc';
    var excluded = 'nav, aside, footer, header, [hidden], [aria-hidden="true"], [data-tavoos-toc-exclude], .tavoos-toc-exclude, .tvs-upd, .tvs-rel, .tavoos-article-toc';
    var levels = Array.isArray(config.levels) ? config.levels.filter(function (h) { return /^h[2-6]$/.test(h); }) : ['h2'];
    if (!levels.length) levels = ['h2'];
    var minimum = Math.max(2, Math.min(20, Number(config.minimum) || 3));
    var offset = Math.max(0, Math.min(500, Number(config.offset) || 0));

    function legacyPresent() {
        return !!document.querySelector(legacySelector);
    }

    function headings(root) {
        return Array.from(root.querySelectorAll(levels.join(','))).filter(function (heading) {
            return heading.textContent.trim().length > 1 && !heading.closest(excluded);
        });
    }

    function uniqueId(base) {
        var id = base;
        var suffix = 2;
        while (document.getElementById(id)) id = base + '-' + suffix++;
        return id;
    }

    function slug(text) {
        // Keep Persian and other Unicode letters; use no heading HTML as markup.
        var normalized = text.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '');
        return Array.from(normalized).slice(0, 64).join('') || 'section';
    }

    function anchorFor(heading) {
        if (heading.id && document.getElementById(heading.id) === heading) return heading.id;
        var previous = aliases.get(heading);
        if (previous && previous.isConnected) return previous.id;
        var id = uniqueId('tavoos-toc-' + slug(heading.textContent.trim()));
        if (!heading.id) {
            heading.id = id;
        } else {
            // Never rewrite an authored duplicate ID. Give this target its own alias.
            var alias = document.createElement('span');
            alias.id = id;
            alias.className = 'tavoos-toc-anchor';
            alias.setAttribute('aria-hidden', 'true');
            alias.style.setProperty('--tavoos-toc-offset', offset + 'px');
            heading.before(alias);
            aliases.set(heading, alias);
        }
        return id;
    }

    function reducedMotion() {
        return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    function jump(heading, instant) {
        if (!heading || !heading.isConnected) return;
        if (!heading.hasAttribute('tabindex')) {
            heading.setAttribute('tabindex', '-1');
            heading.addEventListener('blur', function () { heading.removeAttribute('tabindex'); }, { once: true });
        }
        heading.focus({ preventScroll: true });
        var y = Math.max(0, heading.getBoundingClientRect().top + window.scrollY - offset);
        if (instant || reducedMotion()) {
            // Override even a theme's global smooth-scroll rule for reduced motion.
            var root = document.documentElement;
            var oldValue = root.style.getPropertyValue('scroll-behavior');
            var oldPriority = root.style.getPropertyPriority('scroll-behavior');
            root.style.setProperty('scroll-behavior', 'auto', 'important');
            window.scrollTo({ top: y, left: window.scrollX, behavior: 'instant' });
            if (oldValue) root.style.setProperty('scroll-behavior', oldValue, oldPriority);
            else root.style.removeProperty('scroll-behavior');
        } else {
            window.scrollTo({ top: y, left: window.scrollX, behavior: 'smooth' });
        }
    }

    function hashTarget() {
        var hash;
        try { hash = decodeURIComponent(window.location.hash.slice(1)); } catch (error) { return null; }
        return targets.get(hash);
    }

    function removeNavigation() {
        if (nav) nav.remove();
        nav = null;
        targets.clear();
        if (observer) observer.disconnect();
        observer = null;
    }

    function initialize() {
        if (nav || legacyPresent() || document.querySelector('.tavoos-article-toc')) return;
        var roots;
        try {
            roots = Array.from(document.querySelectorAll(config.content_selector || '[data-tavoos-toc-content]'));
        } catch (error) { return; }
        roots = roots.filter(function (root) {
            return root !== document.body && root !== document.documentElement && !root.closest(excluded);
        });
        // A page builder can render desktop/mobile duplicates; use one eligible article.
        var candidates = roots.map(function (root) { return { root: root, headings: headings(root) }; });
        candidates.sort(function (a, b) { return b.headings.length - a.headings.length; });
        var candidate = candidates[0];
        if (!candidate || candidate.headings.length < minimum) return;

        nav = document.createElement('nav');
        nav.className = 'tavoos-article-toc';
        nav.setAttribute('aria-label', config.label || 'Table of contents');
        var details = document.createElement('details');
        details.open = config.expansion === 'open' || (config.expansion !== 'closed' && window.matchMedia('(min-width: 768px)').matches);
        var summary = document.createElement('summary');
        summary.textContent = config.title || 'In this article';
        var list = document.createElement('ol');
        var baseLevel = Math.min.apply(null, candidate.headings.map(function (h) { return Number(h.tagName.slice(1)); }));
        candidate.headings.forEach(function (heading) {
            var id = anchorFor(heading);
            targets.set(id, heading);
            heading.classList.add('tavoos-toc-target');
            heading.style.setProperty('--tavoos-toc-offset', offset + 'px');
            var item = document.createElement('li');
            item.className = 'tavoos-toc-depth-' + Math.min(4, Math.max(0, Number(heading.tagName.slice(1)) - baseLevel));
            var link = document.createElement('a');
            link.setAttribute('href', '#' + encodeURIComponent(id));
            link.textContent = heading.textContent.trim();
            item.appendChild(link);
            list.appendChild(item);
        });
        details.append(summary, list);
        nav.appendChild(details);
        if (config.placement === 'top') candidate.root.prepend(nav);
        else candidate.headings[0].before(nav);

        nav.addEventListener('click', function (event) {
            var link = event.target.closest('a');
            if (!link || !nav.contains(link) || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
            var id;
            try { id = decodeURIComponent(link.hash.slice(1)); } catch (error) { return; }
            var heading = targets.get(id);
            if (!heading) return;
            event.preventDefault();
            if (window.location.hash !== link.hash) {
                try { window.history.pushState(null, '', link.hash); } catch (error) { window.location.hash = link.hash; }
            }
            jump(heading, false);
        });

        // Coexist safely if a delayed legacy snippet inserts its table after ours.
        if (window.MutationObserver) {
            observer = new MutationObserver(function (records) {
                var legacyAdded = records.some(function (record) {
                    return Array.from(record.addedNodes).some(function (node) {
                        return node.nodeType === 1 && (node.matches(legacySelector) || node.querySelector(legacySelector));
                    });
                });
                if (legacyAdded) removeNavigation();
            });
            observer.observe(document.body, { childList: true, subtree: true });
        }
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize, { once: true });
    else initialize();
    window.addEventListener('load', function () {
        initialize();
        var heading = hashTarget();
        if (heading) jump(heading, true);
    }, { once: true });
    window.addEventListener('popstate', function () {
        var heading = hashTarget();
        if (heading) jump(heading, true);
    });
    document.addEventListener('tavoos-toc:refresh', function () {
        removeNavigation();
        initialize();
    });
}());

// Functional browser tests against the actual shipped JS and CSS.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const root = path.resolve(__dirname, '..');
let passed = 0;
async function main() {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}),
    args: ['--no-sandbox'] });
  try {
    const p = await browser.newPage({ viewport: { width: 1200, height: 850 } });
    const errors = [];
    p.on('pageerror', e => errors.push(e.message));
    async function fixture(options = {}, body = '') {
      await p.goto('about:blank');
      await p.setContent('<html lang="fa" dir="rtl"><body>' + (body ||
        '<article data-tavoos-toc-content><h2>بخش اول</h2><p>متن نمونه</p><h2>بخش دوم</h2><h2>بخش سوم</h2></article>') + '</body></html>');
      await p.evaluate(config => { window.tavoosArticleTOC = config; }, {
        levels: ['h2'], minimum: 3, offset: 104, expansion: 'auto', placement: 'before',
        title: 'در این مقاله', label: 'فهرست مقاله', ...options });
      await p.addStyleTag({ path: path.join(root, 'assets/toc.css') });
      await p.addScriptTag({ path: path.join(root, 'assets/toc.js') });
    }
    async function check(name, fn) { await fn(); passed++; console.log('PASS ' + name); }
    await check('RTL desktop creates three links and opens automatically', async () => {
      await fixture(); assert.equal(await p.locator('nav a').count(), 3);
      assert.equal(await p.locator('nav details').evaluate(e => e.open), true);
      assert.equal(await p.locator('nav').evaluate(e => getComputedStyle(e).direction), 'rtl');
    });
    await check('link navigation transfers focus and updates the fragment', async () => {
      await p.locator('nav a').nth(1).click();
      assert.equal(await p.evaluate(() => document.activeElement.textContent), 'بخش دوم');
      assert.ok(await p.evaluate(() => location.hash.startsWith('#tavoos-toc-')));
    });
    await check('mobile starts collapsed; keyboard opens summary', async () => {
      await p.setViewportSize({ width: 390, height: 844 }); await fixture();
      assert.equal(await p.locator('details').evaluate(e => e.open), false);
      await p.locator('summary').focus(); await p.keyboard.press('Enter');
      assert.equal(await p.locator('details').evaluate(e => e.open), true);
      await p.setViewportSize({ width: 1200, height: 850 });
    });
    await check('threshold prevents a TOC for insufficient headings', async () => {
      await fixture({ minimum: 4 }); assert.equal(await p.locator('nav').count(), 0);
    });
    await check('excluded and hidden headings are omitted', async () => {
      await fixture({ minimum: 2 }, '<article data-tavoos-toc-content><h2>نمایش اول</h2><h2 class="tavoos-toc-exclude">حذف</h2><section hidden><h2>پنهان</h2></section><h2>نمایش دوم</h2></article>');
      assert.equal(await p.locator('nav a').count(), 2);
    });
    await check('authored IDs are preserved and duplicate IDs get a safe alias', async () => {
      await fixture({ minimum: 2 }, '<div id="existing"></div><article data-tavoos-toc-content><h2 id="existing">تیتر تکراری</h2><h2 id="unique">تیتر یکتا</h2></article>');
      assert.equal(await p.locator('h2').first().getAttribute('id'), 'existing');
      assert.equal(await p.locator('nav a').nth(1).getAttribute('href'), '#unique');
      assert.ok((await p.locator('nav a').first().getAttribute('href')).startsWith('#tavoos-toc-'));
    });
    await check('invalid and whole-page selectors safely suppress the TOC', async () => {
      await fixture({ content_selector: '[' }); assert.equal(await p.locator('nav').count(), 0);
      await fixture({ content_selector: 'body' }); assert.equal(await p.locator('nav').count(), 0);
    });
    await check('H3 selection, top placement and forced closed state', async () => {
      await fixture({ levels: ['h2', 'h3'], placement: 'top', expansion: 'closed', minimum: 2 }, '<article data-tavoos-toc-content><p>مقدمه</p><h2>تیتر اصلی</h2><h3>زیرتیتر</h3></article>');
      assert.equal(await p.locator('article').evaluate(e => e.firstElementChild.tagName), 'NAV');
      assert.equal(await p.locator('.tavoos-toc-depth-1').count(), 1);
      assert.equal(await p.locator('details').evaluate(e => e.open), false);
    });
    await check('refresh rebuilds once with dynamically inserted content', async () => {
      await fixture(); await p.evaluate(() => {
        const h = document.createElement('h2'); h.textContent = 'بخش تازه';
        document.querySelector('article').append(h);
        document.dispatchEvent(new Event('tavoos-toc:refresh'));
      }); assert.equal(await p.locator('nav').count(), 1); assert.equal(await p.locator('nav a').count(), 4);
    });
    await check('late legacy markup removes the plugin navigation', async () => {
      await p.evaluate(() => { const n = document.createElement('div'); n.className = 'tvs-toc'; document.body.append(n); });
      await p.waitForFunction(() => !document.querySelector('.tavoos-article-toc'));
    });
    await check('existing legacy markup suppresses initialization', async () => {
      await fixture({}, '<div class="tvs-toc"></div><article data-tavoos-toc-content><h2>اول</h2><h2>دوم</h2><h2>سوم</h2></article>');
      assert.equal(await p.locator('.tavoos-article-toc').count(), 0);
    });
    await check('reduced motion requests immediate scrolling', async () => {
      await p.emulateMedia({ reducedMotion: 'reduce' }); await fixture();
      await p.evaluate(() => { window.scrollTo = opts => { window.lastScroll = opts; }; });
      await p.locator('nav a').first().click();
      assert.equal(await p.evaluate(() => window.lastScroll.behavior), 'instant');
    });
    if (process.env.WP_BASE_URL) {
      await check('live WordPress serves an article with local assets and working heading links', async () => {
        const response = await p.goto(process.env.WP_BASE_URL + '/?p=' + (process.env.WP_POST_ID || '4'));
        assert.equal(response.status(), 200); await p.locator('.tavoos-article-toc').waitFor();
        assert.equal(await p.locator('.tavoos-article-toc a').count(), 3);
        assert.equal(await p.locator('script[src*="tavoos-article-toc/assets/toc.js"]').count(), 1);
        await p.locator('.tavoos-article-toc a').first().click();
        assert.equal(await p.evaluate(() => document.activeElement.tagName), 'H2');
      });
      if (process.env.WP_TEST_CREDENTIALS) {
        await check('real Settings API saves and reloads plugin options', async () => {
          const c = JSON.parse(fs.readFileSync(process.env.WP_TEST_CREDENTIALS));
          await p.goto(process.env.WP_BASE_URL + '/wp-login.php');
          await p.locator('#user_login').fill(c.username); await p.locator('#user_pass').fill(c.password);
          await Promise.all([p.waitForURL('**/wp-admin/**'), p.locator('#wp-submit').click()]);
          const url = process.env.WP_BASE_URL + '/wp-admin/options-general.php?page=tavoos-article-toc';
          await p.goto(url); const title = await p.locator('#tavoos-toc-title').inputValue();
          await p.locator('#tavoos-toc-title').fill('تست ذخیره تنظیمات');
          await Promise.all([p.waitForURL('**settings-updated=true'), p.locator('#submit').click()]);
          assert.equal(await p.locator('#tavoos-toc-title').inputValue(), 'تست ذخیره تنظیمات');
          await p.locator('#tavoos-toc-title').fill(title);
          await Promise.all([p.waitForURL('**settings-updated=true'), p.locator('#submit').click()]);
        });
      }
    }
    assert.deepEqual(errors, [], 'Unexpected browser exceptions');
    console.log(`${passed} checks passed; no browser exceptions.`);
  } finally { await browser.close(); }
}
main().catch(e => { console.error(e); process.exitCode = 1; });

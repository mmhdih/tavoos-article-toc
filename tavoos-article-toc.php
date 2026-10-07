<?php
/**
 * Plugin Name: Tavoos Article TOC
 * Description: An accessible, expandable table of contents for article headings, with RTL support and configurable display settings.
 * Version: 1.0.0
 * Requires at least: 6.2
 * Requires PHP: 7.4
 * Author: Mahdi Habibi / Tavoos Web
 * License: GPL-2.0-or-later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: tavoos-article-toc
 * Domain Path: /languages
 *
 * @package TavoosArticleTOC
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'TAVOOS_ARTICLE_TOC_VERSION', '1.0.0' );
define( 'TAVOOS_ARTICLE_TOC_FILE', __FILE__ );
require_once __DIR__ . '/includes/class-plugin.php';
Tavoos\ArticleTOC\Plugin::boot();

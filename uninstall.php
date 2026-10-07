<?php
/**
 * Remove this plugin's one per-site option on uninstall.
 *
 * @package TavoosArticleTOC
 */
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
	exit;
}
delete_option( 'tavoos_article_toc_options' );

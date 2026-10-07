<?php
/**
 * WordPress integration and settings.
 *
 * @package TavoosArticleTOC
 */

namespace Tavoos\ArticleTOC;

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

final class Plugin {
	const OPTION = 'tavoos_article_toc_options';
	const PAGE   = 'tavoos-article-toc';

	/** Register hooks without executing translations before init. */
	public static function boot() {
		add_action( 'init', array( __CLASS__, 'translations' ) );
		add_action( 'admin_menu', array( __CLASS__, 'admin_menu' ) );
		add_action( 'admin_init', array( __CLASS__, 'register_settings' ) );
		add_action( 'wp_enqueue_scripts', array( __CLASS__, 'enqueue' ) );
		add_filter( 'the_content', array( __CLASS__, 'wrap_content' ), 99 );
		add_filter( 'plugin_action_links_' . plugin_basename( TAVOOS_ARTICLE_TOC_FILE ), array( __CLASS__, 'action_links' ) );
	}

	/** Register bundled translations for standalone ZIP installs. */
	public static function translations() {
		load_plugin_textdomain( 'tavoos-article-toc', false, dirname( plugin_basename( TAVOOS_ARTICLE_TOC_FILE ) ) . '/languages' );
	}

	/** Return unlocalized storage defaults. */
	public static function defaults() {
		return array(
			'enabled' => 1,
			'title' => '',
			'levels' => array( 'h2' ),
			'post_types' => array( 'post' ),
			'minimum' => 3,
			'placement' => 'before',
			'expansion' => 'auto',
			'offset' => 104,
			'content_selector' => '',
		);
	}

	/** Return public, individually viewable post types. */
	public static function post_types() {
		return array_filter( get_post_types( array( 'public' => true ), 'objects' ), static function ( $type ) {
			return 'attachment' !== $type->name && is_post_type_viewable( $type );
		} );
	}

	/** Return sanitized settings, including safe defaults for older values. */
	public static function options() {
		$saved = get_option( self::OPTION, array() );
		return self::sanitize( array_merge( self::defaults(), is_array( $saved ) ? $saved : array() ) );
	}

	/** Validate the complete Settings API submission; no HTML or executable input. */
	public static function sanitize( $input ) {
		$input = is_array( $input ) ? $input : array();
		$out   = self::defaults();
		$out['enabled'] = empty( $input['enabled'] ) ? 0 : 1;
		foreach ( array( 'title' => 160, 'content_selector' => 250 ) as $key => $limit ) {
			$value = isset( $input[ $key ] ) && is_string( $input[ $key ] ) ? sanitize_text_field( $input[ $key ] ) : '';
			$out[ $key ] = function_exists( 'mb_substr' ) ? mb_substr( $value, 0, $limit ) : substr( $value, 0, $limit );
		}
		$levels = isset( $input['levels'] ) && is_array( $input['levels'] ) ? $input['levels'] : array();
		$out['levels'] = array_values( array_intersect( array( 'h2', 'h3', 'h4', 'h5', 'h6' ), array_filter( $levels, 'is_string' ) ) );
		if ( ! $out['levels'] ) {
			$out['levels'] = array( 'h2' );
		}
		$types = isset( $input['post_types'] ) && is_array( $input['post_types'] ) ? array_filter( $input['post_types'], 'is_string' ) : array();
		$out['post_types'] = array_values( array_intersect( array_keys( self::post_types() ), $types ) );
		foreach ( array( 'minimum' => array( 2, 20 ), 'offset' => array( 0, 500 ) ) as $key => $bounds ) {
			if ( isset( $input[ $key ] ) && is_scalar( $input[ $key ] ) && is_numeric( $input[ $key ] ) ) {
				$out[ $key ] = max( $bounds[0], min( $bounds[1], (int) $input[ $key ] ) );
			}
		}
		foreach ( array( 'placement' => array( 'before', 'top' ), 'expansion' => array( 'auto', 'open', 'closed' ) ) as $key => $allowed ) {
			if ( isset( $input[ $key ] ) && in_array( $input[ $key ], $allowed, true ) ) {
				$out[ $key ] = $input[ $key ];
			}
		}
		return $out;
	}

	/** Whether the singular frontend request is eligible. */
	public static function eligible() {
		$options = self::options();
		return ! is_admin() && ! is_feed() && ! is_embed()
			&& ! ( defined( 'REST_REQUEST' ) && REST_REQUEST )
			&& ! is_preview() && ! post_password_required()
			&& $options['enabled'] && $options['post_types'] && is_singular( $options['post_types'] );
	}

	/** Enqueue local assets only on eligible singular requests. */
	public static function enqueue() {
		if ( ! self::eligible() ) {
			return;
		}
		$url = plugin_dir_url( TAVOOS_ARTICLE_TOC_FILE );
		wp_enqueue_style( self::PAGE, $url . 'assets/toc.css', array(), TAVOOS_ARTICLE_TOC_VERSION );
		wp_enqueue_script( self::PAGE, $url . 'assets/toc.js', array(), TAVOOS_ARTICLE_TOC_VERSION, true );
		$options = self::options();
		$options['title'] = '' !== $options['title'] ? $options['title'] : __( 'In this article', 'tavoos-article-toc' );
		$options['label'] = __( 'Table of contents', 'tavoos-article-toc' );
		wp_localize_script( self::PAGE, 'tavoosArticleTOC', $options );
	}

	/** Scope the article without parsing, rewriting or storing its HTML. */
	public static function wrap_content( $content ) {
		if ( ! self::eligible() || ! in_the_loop() || ! is_main_query() || get_the_ID() !== get_queried_object_id()
			|| false !== strpos( $content, 'data-tavoos-toc-content' ) ) {
			return $content;
		}
		return '<div class="tavoos-toc-content" data-tavoos-toc-content="1">' . $content . '</div>';
	}

	/** Add the settings link to the Plugins screen. */
	public static function action_links( $links ) {
		array_unshift( $links, '<a href="' . esc_url( admin_url( 'options-general.php?page=' . self::PAGE ) ) . '">' . esc_html__( 'Settings', 'tavoos-article-toc' ) . '</a>' );
		return $links;
	}

	/** Register a standard WordPress settings page. */
	public static function admin_menu() {
		add_options_page( __( 'Tavoos Article TOC', 'tavoos-article-toc' ), __( 'Article TOC', 'tavoos-article-toc' ), 'manage_options', self::PAGE, array( __CLASS__, 'settings_page' ) );
	}

	/** Register sanitization; options.php enforces capability and nonce checks. */
	public static function register_settings() {
		register_setting( self::PAGE, self::OPTION, array( 'type' => 'array', 'sanitize_callback' => array( __CLASS__, 'sanitize' ), 'default' => self::defaults(), 'show_in_rest' => false ) );
		add_settings_section( 'tavoos_toc_display', __( 'Display settings', 'tavoos-article-toc' ), '__return_false', self::PAGE );
		$fields = array(
			'enabled' => __( 'Automatic table of contents', 'tavoos-article-toc' ),
			'title' => __( 'Title', 'tavoos-article-toc' ),
			'post_types' => __( 'Post types', 'tavoos-article-toc' ),
			'levels' => __( 'Heading levels', 'tavoos-article-toc' ),
			'minimum' => __( 'Minimum headings', 'tavoos-article-toc' ),
			'placement' => __( 'Placement', 'tavoos-article-toc' ),
			'expansion' => __( 'Initial state', 'tavoos-article-toc' ),
			'offset' => __( 'Scroll offset (pixels)', 'tavoos-article-toc' ),
			'content_selector' => __( 'Custom content selector', 'tavoos-article-toc' ),
		);
		foreach ( $fields as $key => $label ) {
			$args = array( 'key' => $key );
			if ( ! in_array( $key, array( 'levels', 'post_types' ), true ) ) {
				$args['label_for'] = 'tavoos-toc-' . $key;
			}
			add_settings_field( $key, $label, array( __CLASS__, 'field' ), self::PAGE, 'tavoos_toc_display', $args );
		}
	}

	/** Output an escaped field. */
	public static function field( $args ) {
		$key = $args['key'];
		$o = self::options();
		$name = self::OPTION . '[' . $key . ']';
		$id = 'tavoos-toc-' . $key;
		if ( 'enabled' === $key ) {
			printf( '<label><input type="checkbox" id="%1$s" name="%2$s" value="1" %3$s> %4$s</label>', esc_attr( $id ), esc_attr( $name ), checked( $o[ $key ], 1, false ), esc_html__( 'Enable automatic display', 'tavoos-article-toc' ) );
		} elseif ( in_array( $key, array( 'post_types', 'levels' ), true ) ) {
			$choices = array();
			if ( 'post_types' === $key ) {
				foreach ( self::post_types() as $type ) {
					$choices[ $type->name ] = $type->labels->name;
				}
			} else {
				$choices = array( 'h2' => 'H2', 'h3' => 'H3', 'h4' => 'H4', 'h5' => 'H5', 'h6' => 'H6' );
			}
			echo '<fieldset>';
			foreach ( $choices as $value => $label ) {
				printf( '<label><input type="checkbox" name="%1$s[]" value="%2$s" %3$s> %4$s</label><br>', esc_attr( $name ), esc_attr( $value ), checked( in_array( $value, $o[ $key ], true ), true, false ), esc_html( $label ) );
			}
			echo '</fieldset>';
			if ( 'post_types' === $key ) {
				echo '<p class="description">' . esc_html__( 'Select no post types to disable display everywhere.', 'tavoos-article-toc' ) . '</p>';
			} else {
				echo '<p class="description">' . esc_html__( 'H2 is used if no heading level is selected.', 'tavoos-article-toc' ) . '</p>';
			}
		} elseif ( in_array( $key, array( 'placement', 'expansion' ), true ) ) {
			$choices = 'placement' === $key
				? array( 'before' => __( 'Before the first heading', 'tavoos-article-toc' ), 'top' => __( 'At the start of the content', 'tavoos-article-toc' ) )
				: array( 'auto' => __( 'Expanded on desktop, collapsed on mobile', 'tavoos-article-toc' ), 'open' => __( 'Always expanded', 'tavoos-article-toc' ), 'closed' => __( 'Always collapsed', 'tavoos-article-toc' ) );
			printf( '<select id="%1$s" name="%2$s">', esc_attr( $id ), esc_attr( $name ) );
			foreach ( $choices as $value => $label ) {
				printf( '<option value="%1$s" %2$s>%3$s</option>', esc_attr( $value ), selected( $o[ $key ], $value, false ), esc_html( $label ) );
			}
			echo '</select>';
		} elseif ( in_array( $key, array( 'minimum', 'offset' ), true ) ) {
			printf( '<input type="number" id="%1$s" name="%2$s" value="%3$d" min="%4$d" max="%5$d" step="1" class="small-text">', esc_attr( $id ), esc_attr( $name ), (int) $o[ $key ], 'minimum' === $key ? 2 : 0, 'minimum' === $key ? 20 : 500 );
		} else {
			printf( '<input type="text" id="%1$s" name="%2$s" value="%3$s" maxlength="%4$d" class="regular-text">', esc_attr( $id ), esc_attr( $name ), esc_attr( $o[ $key ] ), 'title' === $key ? 160 : 250 );
			$help = 'title' === $key
				? __( 'Leave empty to use the translated default title.', 'tavoos-article-toc' )
				: __( 'Optional CSS selector for the article body, for example .entry-content. Leave empty for automatic WordPress content detection. Never select the whole page. An invalid selector safely disables the table.', 'tavoos-article-toc' );
			echo '<p class="description">' . esc_html( $help ) . '</p>';
		}
	}

	/** Settings API form supplies nonce and capability checks. */
	public static function settings_page() {
		if ( ! current_user_can( 'manage_options' ) ) {
			return;
		}
		echo '<div class="wrap"><h1>' . esc_html__( 'Tavoos Article TOC', 'tavoos-article-toc' ) . '</h1>';
		echo '<p>' . esc_html__( 'Build a table of contents from headings without changing the saved article. No external services or tracking.', 'tavoos-article-toc' ) . '</p>';
		echo '<p>' . esc_html__( 'If the legacy Tavoos TOC is detected, this plugin stays inactive on that page. Do not disable entire HFCM snippets; remove only their TOC code during a separately approved migration.', 'tavoos-article-toc' ) . '</p>';
		echo '<form action="options.php" method="post">';
		settings_fields( self::PAGE );
		do_settings_sections( self::PAGE );
		submit_button();
		echo '</form></div>';
	}
}

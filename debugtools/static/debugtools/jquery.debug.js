/**
 * The jQuery plugin with almost larger copyright text then code..
 * Output the current jQuery selector to the console, with optional prefix.
 *
 * (C) 2008-2012 Diederik van der Boor, BSD licensed.
 */
jQuery.fn.debug = function(p) { window.console && console.log((p || '') + this.selector, this); return this; };

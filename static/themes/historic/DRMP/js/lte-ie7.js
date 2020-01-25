/* Load this script using conditional IE comments if you need to support IE 7 and IE 6. */

window.onload = function() {
	function addIcon(el, entity) {
		var html = el.innerHTML;
		el.innerHTML = '<span style="font-family: \'DRMP\'">' + entity + '</span>' + html;
	}
	var icons = {
			'icon-tsunami' : '&#x31;',
			'icon-transport-accident' : '&#x32;',
			'icon-rain-wind' : '&#x33;',
			'icon-landslide' : '&#x34;',
			'icon-industrial-accident' : '&#x35;',
			'icon-flood' : '&#x36;',
			'icon-fire' : '&#x37;',
			'icon-earthquake' : '&#x38;',
			'icon-drought' : '&#x39;',
			'icon-cyclone' : '&#x30;',
			'icon-updates' : '&#x71;',
			'icon-training-materials' : '&#x77;',
			'icon-report' : '&#x65;',
			'icon-projects' : '&#x72;',
			'icon-plan' : '&#x74;',
			'icon-map' : '&#x79;',
			'icon-incident' : '&#x75;',
			'icon-event' : '&#x69;',
			'icon-assessment' : '&#x6f;',
			'icon-alert' : '&#x70;',
			'icon-activity5' : '&#x5b;',
			'icon-activity4' : '&#x5d;',
			'icon-activity3' : '&#x5c;',
			'icon-activity2' : '&#x2d;',
			'icon-activity1' : '&#x3d;',
			'icon-updates-dark' : '&#x51;',
			'icon-training-materials-dark' : '&#x57;',
			'icon-report-dark' : '&#x45;',
			'icon-projects-dark' : '&#x52;',
			'icon-plan-dark' : '&#x54;',
			'icon-map-dark' : '&#x59;',
			'icon-incident-dark' : '&#x55;',
			'icon-event-dark' : '&#x49;',
			'icon-assessment-dark' : '&#x4f;',
			'icon-alert-dark' : '&#x50;',
			'icon-activity5-dark' : '&#x7b;',
			'icon-activity4-dark' : '&#x7d;',
			'icon-activity3-dark' : '&#x7c;',
			'icon-activity2-dark' : '&#x5f;',
			'icon-activity1-dark' : '&#x2b;'
		},
		els = document.getElementsByTagName('*'),
		i, attr, html, c, el;
	for (i = 0; ; i += 1) {
		el = els[i];
		if(!el) {
			break;
		}
		attr = el.getAttribute('data-icon');
		if (attr) {
			addIcon(el, attr);
		}
		c = el.className;
		c = c.match(/icon-[^\s'"]+/);
		if (c && icons[c[0]]) {
			addIcon(el, icons[c[0]]);
		}
	}
};
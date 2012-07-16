var org_hierarchy = {};
var organisations = {};
var entities = {};

/*
wishlist ==
1: {
	id: 1,
	pe_id: 1,
	name: "Organisation One",
	resource: "org_organisation",
	roles: {
		1: {
			id: 1,
			name: "Role One",
			type: "Organisational Units",
			affiliates: {
				2: {
					id: 2,
					pe_id: 2,
					name: "Organisation Two",
					resource: "org_organisation"
				}
			}
		}
	}
}

*/

function parseOrganisations(json) {
	var json_orgs = json["$_org_organisation"];
	var organisations = [];
	for (var i=0; i < json_orgs.length; i++) {
		var id = json_orgs[i]["$k_pe_id"]["@id"];
		var name = json_orgs[i]["name"];
		var resource = json_orgs[i]["@resource"];

		organisations.push({
			"id": id,
			"name": name,
			"resource": resource,
			"type": "entity"
		});
	}
	return organisations;
}

function getOrganisations(callback) {
	var url = S3.Ap.concat('/org/organisation.s3json?components=role&show_ids=true');
	$.getJSON(url, callback);
}

function parseAffiliates(json) {
	var json_affiliates = json["$_pr_role"][0]["$_pr_affiliation"];
	var affiliates = [];

	if (json_affiliates != undefined) {
		for (var i=0; i < json_affiliates.length; i++) {
			var affiliate = json_affiliates[i]["$k_pe_id"];
			var pe_id = parseInt(affiliate["@id"]);
			var name = affiliate["$"];
			var resource = affiliate["@resource"];

			var id = null;
			if (resource == "org_organisation") {
				id = organisations[pe_id]["id"];
			}

			affiliates.push({
				"id": id,
				"pe_id": pe_id,
				"name": name,
				"resource": resource,
				"type": "entity"
			});
		}
	}

	return affiliates;
}
// Get the list of aff
function getAffiliates(role_id, callback) {
	var url = S3.Ap.concat('/pr/role/' + role_id + '.s3json?show_ids=true');
	$.getJSON(url, callback);
}

function parseRoles(json) {
	var json_roles = json["$_pr_pentity"][0]["$_pr_role"];
	var roles = [];

	if (json_roles != undefined) {
		for (var i=0; i < json_roles.length; i++) {
			var role = json_roles[i];
			var id = parseInt(role["@id"]);
			var name = role["role"];
			var resource = role["role_type"]["$"];

			roles.push({
				"id": id,
				"name": name,
				"resource": resource,
				"type": "role"
			});
		}
	}

	return roles;
}
// Get the list of roles for an entity
function getRoles(entity_pe_id, callback) {
        var url = S3.Ap.concat('/pr/pentity/' + entity_pe_id + '.s3json?show_ids=true');
	$.getJSON(url, callback);
}

function loadNode(event) {
	node = $(event.currentTarget).closest("li");
	menu = $(event.delegateTarget);

	var path = node.data("path"); // convert to string
	if (path == undefined) {
		return;
	}

	var entity = getEntity(String(path));
	var field_name = menu.data("field_name");
	var crumb = $("<li><a>" + node.text() + "</a></li>").data("target", field_name + "-" + entity.path);
	$("#" + field_name + "-crumbs").append(crumb);

	if (entity.resource == "org_organisation") {
		var field = $("select[name='" + field_name + "']");
		field.val(entity.id);
		field.change();
		crumb.prevAll().removeClass("selected");
		crumb.addClass("selected");
	}

	menu.nextAll().remove();

	var new_menu = new Menu(menu.data("field_name"));
	new_menu.attr("id", field_name + "-" + entity.path);
	new_menu.insertAfter(menu);
	new_menu.position({of: menu, my: "left top", at: "right top", offset: "4 0", collision: "none"});

	if (entity.children == undefined) {
		// this entity has not had children loaded
		// fetch roles or affiliates
		// populate entity (org_hierarchy)
		// populate node (dom tree)
		if (entity.type == "entity") {
			// this is an organisation or office
			var id = entity.pe_id;
			var fn = getRoles;
			var parser = parseRoles;
		}
		else {
			// this is a role
			var id = entity.id;
			var fn = getAffiliates;
			var parser = parseAffiliates;
		}


		fn(id, function(data) {
			var children = parser(data);
			updateOrgHierarchy(entity, children);
			updateDomHierarchy(new_menu, children);
		});
	}
	else {
		var children = [];
		for (idx in entity.children) {
			children.push(entity.children[idx]);
		}
		updateDomHierarchy(new_menu, children);
	}

	new_menu.animate({
		left: parseInt(new_menu.css('left'),10) == 0 ?
			-new_menu.outerWidth() :
			0
	});
	menu.animate({
		left: parseInt(menu.css('left'),10) == 0 ?
			-menu.outerWidth() :
			0
	});
}

function Menu(field_name) {
	return $("<ul/>")
		.addClass(" ui-menu ui-widget ui-widget-content ui-corner-all")
		.attr("role", "listbox")
		.attr("aria-activedescendant", "ui-active-menuitem")
		.data("field_name", field_name)
		.on("click", "li.ui-menu-item", loadNode);
}

function getEntity(path) {
	var path_list = path.split("_");
	var entity = org_hierarchy[path_list[0]];

	for (var i=1; i < path_list.length; i++) {
		var id = path_list[i];
		entity = entity["children"][id];
	}

	return entity;
}

function updateOrgHierarchy(entity, items) {
	/*
		@param entity: object in the org_hierarchy object
		@param items: arrary of objects [{ id:%d, name:%s, path:%s }]
	*/
	entity.children = {};

	for (var i=0; i < items.length; i++) {
		var item = items[i];

		if (item.pe_id != undefined) {
			var idx = item.pe_id;
		}
		else {
			var idx = item.id;
		}

		entity.children[idx] = item;

		if (entity.path) {
			entity.children[idx].path = entity.path + "_";
		}
		entity.children[idx].path += idx;
	}
}

function updateDomHierarchy(parent, items) {
	/*
		@param parent: jQuery node
		@param items: array of objects [{ id:%d, name:%s, path:%s }]
	*/
	var item_count = items.length;

	if (item_count > 0) {
		for (var i=0; i < item_count; i++) {
			var item = items[i];

			var icon = $("<span/>").addClass("ui-menu-icon ui-icon ui-icon-carat-1-e");
			var a = $("<a/>").addClass("ui-corner-all")
			                 .attr("tabindex", "-1")
			                 .attr("aria-haspopup", "true")
			                 .append(icon)
			                 .append(item.name);
			var li = $("<li/>").addClass("ui-menu-item")
			                   .attr("role", "menuitem")
			                   .data({"id":item.id,
			                          "pe_id":item.pe_id,
			                          "path":item.path})
			                   .append(a);
			parent.append(li);
		}
	}
	else {
		parent.append('<li class="ui-menu-item" role="menuitem">None</li>');
	}
}

jQuery(function($) {
    url = S3.Ap.concat('/org/organisation.json?show_ids=true');
    $.getJSON(url, function(data) {
        for (var i=0; i<data.length; i++) {
            var id = data[i].id;
            var pe_id = data[i].pe_id;
            var name = data[i].name;

            organisations[pe_id] = {
                "id": id,
                "pe_id": pe_id,
                "name": name
            };
        }
    });

	$(".widget-org-hierarchy").each(function(index) {
		var field = $(this);
		var field_name = field.attr("name");
        var field_value = field.val();
		var options = window[field_name + "_options"];

        var selected_index = null;

		var entity_list = [];
		if (options != undefined) {
			for (var i=0; i<options.length; i++) {
				var id = options[i].id;
				var pe_id = options[i].pe_id;
				var name = options[i].name;
				var path = pe_id;

				entity = {
					"id": id,
					"pe_id": pe_id,
					"name": name,
					"path": path,
					"type": "entity",
					"resource": "org_organisation"
				};
				org_hierarchy[pe_id] = entity;
				entity_list.push(entity);
                if (field_value == id) {
					selected_index = i;
				}
			}
		}

		var container = $("<div/>").addClass("widget-org-hierarchy-menu");
		var menu = new Menu(field_name).attr("id", field_name + "-top");
		updateDomHierarchy(menu, entity_list);
		container.append(menu);
		container.insertAfter(field);

		var crumbs = $("<ul/>")
			.attr("id", field_name + "-crumbs")
			.addClass("widget-org-hierarchy-crumbs")
			.insertAfter(field);

		var crumb_top = $("<li><a>All</a></li>").data("target", field_name + "-top");

		crumbs.append(crumb_top);

		crumbs.on("click", "li", function(event) {
			crumb = $(this);
			var target = crumb.data("target");

			crumb.nextAll().remove();

			var menu = $("#" + target);
			menu.nextAll().remove();

			if (parseInt(menu.css('left'),10) < 0) {
				menu.animate({
					left: 0
				});
			}

			var path = target.replace(field_name + "-", "");
			var entity = getEntity(path);
			if(entity != undefined && entity.resource == "org_organisation") {
				field.val(entity.id);
				field.change();
				crumb.addClass("selected");
			}
			else if (entity == undefined) {
				field.val("");
				field.change();
			}
		});

		field.hide();
		if (selected_index != undefined) {
			loadNode({currentTarget:menu[0].childNodes[selected_index].childNodes[0],delegateTarget:menu[0]});
		}
	});
});

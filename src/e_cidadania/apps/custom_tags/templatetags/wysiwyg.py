from django import template

register = template.Library()

def wysiwyg_editor(parser):
	return {'Title': "Edit"}

register.inclusion_tag('wysiwyg.html')(wysiwyg_editor)

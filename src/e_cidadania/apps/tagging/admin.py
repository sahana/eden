from django.contrib import admin
from e_cidadania.apps.tagging.models import Tag, TaggedItem
from e_cidadania.apps.tagging.forms import TagAdminForm

class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm

admin.site.register(TaggedItem)
admin.site.register(Tag, TagAdmin)





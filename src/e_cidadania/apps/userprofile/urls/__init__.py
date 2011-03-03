from django.conf import settings

if hasattr(settings, "I18N_URLS") and settings.I18N_URLS:
    try:
        module = __import__("e_cidadania.apps.userprofile.urls.%s" % (settings.LANGUAGE_CODE), \
                            {}, {}, "urlpatterns")
        globals().update({ "urlpatterns": module.__dict__["urlpatterns"] })
    except:
        module = __import__("e_cidadania.apps.userprofile.urls.en", {}, {}, "urlpatterns")
        globals().update({ "urlpatterns": module.__dict__["urlpatterns"] })
else:
    module = __import__("e_cidadania.apps.userprofile.urls.en", {}, {}, "urlpatterns")
    globals().update({ "urlpatterns": module.__dict__["urlpatterns"] })

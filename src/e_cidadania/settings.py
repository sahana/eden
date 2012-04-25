# Django settings for e_cidadania project.

"""
Main configuration file for e-cidadania. Please refer to the documentation on
http://docs.ecidadania.org before you modify anything.
"""

__version__ = "0.2"
__status__ = "alpha 1"

# Get the current directory
import os
cwd = os.path.dirname(os.path.realpath(__file__))

# Django settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Extending the user profile a bit more
AUTH_PROFILE_MODULE = "apps.ecidadania.accounts.UserProfile"
ACCOUNT_ACTIVATION_DAYS = 2
LOGIN_REDIRECT_URL = '/accounts/'
GOOGLE_MAPS_API_KEY = 'ABQIAAAATqrYeRgzMa92HeAJ337iJhRIU2G0euEtM3XnBHtmv6MD_woHxRSapJw6ROu7OKaPDPIwetftitHBcw'

# Stablish WYSIWYG editor for HTML forms. By default, we set CKEditor, but if
# you want to use YUI editor just comment DJANGO_WYSIWYG_FLAVOR.
# Values: ckeditor, empty

# Registration mail settings
#EMAIL_HOST = ""
#EMAIL_PORT=
#EMAIL_HOST_USER=""
#EMAIL_HOST_PASSWORD=""
#DEFAULT_FROM_EMAIL = ""

# Calendar
FIRST_WEEK_DAY = 0 # '0' for Monday, '6' for Sunday

ADMINS = (
    ('', ''),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db/sqlite.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

TIME_ZONE = 'Europe/Madrid'
LANGUAGE_CODE = 'es-es'
LANGUAGES = (
    ('es_ES', 'Espanol'),
    ('en_GB', 'English'),
    ('gl_ES', 'Galego'),
)

SITE_ID = 1
USE_I18N = True
USE_L10N = True
MEDIA_ROOT = cwd + '/uploads/'
MEDIA_URL = '/uploads/'
STATIC_ROOT = cwd + '/static/'
STATIC_URL = '/static'
ADMIN_MEDIA_PREFIX = STATIC_URL + '/grappelli/'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

STATICFILES_DIRS = (
    (cwd + '/static_files/'),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '8nwcwmtau*bnu0u=shmdkda^-tpn55ch%qeqc8xn#-77r8c*0a'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
)

# Setting for debug_toolbar
#INTERNAL_IPS = ('127.0.0.1','192.168.0.204',)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'urls'
APPEND_SLASH = True

TEMPLATE_DIRS = (
    (cwd + '/templates'),
)

# The administration panel link is hardcoded because we can't handle other
# way of doing it without messing with grappelli or django-admin. The extra HTML
# tags bring the title a dropdown menu functionality'
#GRAPPELLI_ADMIN_TITLE = 'e-cidadania %s - <a href="/">Back to site</a>' % (__version__)
GRAPPELLI_ADMIN_TITLE = "<li class='user-options-container collapse closed'> \
<a href='javascript://' class='user-options-handler collapse-handler'> \
e-cidadania %s</a><ul class='user-options'><li><a href='/' \
style='padding:10px;'>Back to site</a></li></ul></li>" % (__version__)
GRAPPELLI_ADMIN_URL = '/admin'
GRAPPELLI_INDEX_DASHBOARD = 'dashboard.CustomIndexDashboard'

# We separate the applications so we can manage them through scripts
# Please do not touch this unless you know very well what you're doing

DJANGO_APPS = (
    # This list is from the builtin applications in django that are used in
    # e-cidadania
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.messages',
    'grappelli.dashboard',
    'grappelli',
    'django.contrib.admin',
    'django.contrib.comments',
)

# Stablish message storage
MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

THIRDPARTY_APPS = (
    # This list is from the third party software included in e-cidadania or
    # system-wide dependencies.
    'apps.thirdparty.userprofile',
    'apps.thirdparty.tagging',
    #'django_extensions',
)

ECIDADANIA_MODULES = (
    # Modules created for e-cidadania and installed by default. You can add
    # here your own modules
    'core.spaces',
    'apps.ecidadania.accounts',
    'apps.ecidadania.proposals',
    'apps.ecidadania.news',
    'apps.ecidadania.debate',
    'apps.ecidadania.staticpages',
    'apps.ecidadania.cal',
    'extras.custom_tags',
)

INSTALLED_APPS = DJANGO_APPS + THIRDPARTY_APPS + ECIDADANIA_MODULES

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

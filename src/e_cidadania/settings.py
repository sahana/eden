# Django settings for e_cidadania project.

__author__ = "Oscar Carballal Prego"
__copyright__ = "Cidadania Sociedade Cooperativa Galega"
__credits__ = ["Oscar Carballal Prego"]
__license__ = "GPLv3"
__version__ = "0.1.5"
__maintainer__ = "Oscar Carballal Prego"
__email__ = "oscar.carballal@cidadania.coop"
__status__ = "beta"

# Get the current directory
import os
cwd = os.path.dirname(os.path.realpath(__file__))

# Django settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# Extending the user profile a bit more
AUTH_PROFILE_MODULE = "accounts.UserProfile"
ACCOUNT_ACTIVATION_DAYS = 2
LOGIN_REDIRECT_URL = '/accounts'
GOOGLE_MAPS_API_KEY = 'ABQIAAAATqrYeRgzMa92HeAJ337iJhRIU2G0euEtM3XnBHtmv6MD_woHxRSapJw6ROu7OKaPDPIwetftitHBcw'

# Stablish WYSIWYG editor for HTML forms. By default, we set CKEditor, but if
# you want to use YUI editor just comment DJANGO_WYSIWYG_FLAVOR.
# Values: ckeditor, empty
DJANGO_WYSIWYG_FLAVOR = "ckeditor"
DJANGO_WYSIWYG_MEDIA_URL = "/static/ckeditor/"

# Registration mail settings
#EMAIL_HOST = ""
#EMAIL_PORT=
#EMAIL_HOST_USER=""
#EMAIL_HOST_PASSWORD=""
#DEFAULT_FROM_EMAIL = ""

# Calendar
FIRST_WEEK_DAY = 0 # '0' for Monday, '6' for Sunday

ADMINS = (
    ('Oscar Carballal', 'oscar@cidadania.coop'),
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

ROOT_URLCONF = 'e_cidadania.urls'

TEMPLATE_DIRS = (
    (cwd + '/templates'),
)

GRAPPELLI_ADMIN_TITLE = 'e-cidadania 0.1 / Administracion'
GRAPPELLI_ADMIN_URL = '/admin'
GRAPPELLI_INDEX_DASHBOARD = 'e_cidadania.dashboard.CustomIndexDashboard'

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
    'django_wysiwyg',
    'e_cidadania.apps.userprofile',
    'e_cidadania.apps.tagging',
    #'django_extensions',
)

ECIDADANIA_MODULES = (
    # Modules created for e-cidadania and installed by default. You can add
    # here your own modules.
    'e_cidadania.apps.accounts',
    'e_cidadania.apps.proposals',
    'e_cidadania.apps.news',
    'e_cidadania.apps.debate',
    'e_cidadania.apps.spaces',
    'e_cidadania.apps.staticpages',
    'e_cidadania.apps.cal',
    'e_cidadania.apps.massmail',
    #'debug_toolbar',
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
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
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


# WARNING. THIS SECTION WILL HAVE VOLATILE CODE, PROBABLY FOR
# COMPATIBILITY WITH OLDER OR NEWER VERSIONS OF DJANGO

# Activate the new url syntax in django 1.3 which will be
# compatible till 1.5
import django.template
django.template.add_to_builtins('django.templatetags.future')

"""
Django settings for pybackend project.

Generated by 'django-admin startproject' using Django 4.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import os
import sys
from pathlib import Path

import environ
from MySQLdb.constants.ER import DATABASE_NAME
from django.core.exceptions import ImproperlyConfigured

env = environ.Env()
environ.Env.read_env()  # Reads .env file

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-us#89kk1!imm+zl8yb$-(stb=ubi&j5ujz)id_&aj6=5f5lvz='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*", "127.0.0.1", "localhost"]


# Application definition

INSTALLED_APPS = [
    #'pybackend.apps.PyBackend',
    'pybackend',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',  # For CORS support
    "drf_spectacular"
]
# Allow requests from Angular's frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:4200",  # Adjust for your Angular app's URL
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
MIDDLEWARE += [
    'corsheaders.middleware.CorsMiddleware',
]

if 'test' in sys.argv:
    MIDDLEWARE.remove('django.middleware.csrf.CsrfViewMiddleware')

AUTH_USER_MODEL = 'pybackend.CustomUser'


ROOT_URLCONF = 'pybackend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pybackend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases
DATABASES = {'default': {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': 'test_db',
    'USER': 'test_user',
    'PASSWORD': 'test_password',
    'HOST': '127.0.0.1',
    'PORT': '3306'

}}

DATABASE_BACKEND = env(var='DATABASE_BACKEND', default='mysql')
if DATABASE_BACKEND == 'mysql':
    pass
    # DATABASES['production'] = {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': 'fake_db',
    #     'USER': 'fake_user',
    #     'PASSWORD': 'fake_password',
    #     'HOST': '127.0.0.1',
    #     'PORT': '3306'
    # }
elif DATABASE_BACKEND == 'sqlite':
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
else:
    raise ImproperlyConfigured("Unknown DATABASE_BACKEND environment variable")

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    # 'DEFAULT_RENDERER_CLASSES': (
    #     'djangorestframework_camel_case.render.CamelCaseJSONRenderer',
    #     'djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer',
    # ),
    'DEFAULT_PARSER_CLASSES': (
        # 'djangorestframework_camel_case.parser.CamelCaseJSONParser',
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Django Budget Assistant API',
    'DESCRIPTION': 'Django Budget Assistant API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': True,
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
        #'pybackend.schema.custom_schema_postprocessor'
    ],

    # OTHER SETTINGS
}

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [BASE_DIR / "templates"],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

# Email Backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

# Gmail Credentials
EMAIL_HOST_USER = 'daanvdn@gmail.com'
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'drf_spectacular': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Log all debug-level messages
            'propagate': True,
        },
    },
}
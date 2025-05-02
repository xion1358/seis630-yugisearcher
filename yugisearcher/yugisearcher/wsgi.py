"""
WSGI config for yugisearcher project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.management import call_command

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yugisearcher.settings')

application = get_wsgi_application()
call_command('import_card_inventory')
call_command('import_artworks')
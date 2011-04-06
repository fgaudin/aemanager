from django.contrib import admin
from backup.models import BackupRequest, RestoreRequest

admin.site.register(BackupRequest)
admin.site.register(RestoreRequest)

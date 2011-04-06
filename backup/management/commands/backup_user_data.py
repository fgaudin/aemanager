from django.core.management.base import BaseCommand
from django.conf import settings
from backup.models import BackupRequest, BACKUP_RESTORE_STATE_IN_PROGRESS, \
    BACKUP_RESTORE_STATE_PENDING
import datetime

class Command(BaseCommand):
    help = 'Execute pending backup request'

    def handle(self, *args, **options):
        pending = BackupRequest.objects.filter(state=BACKUP_RESTORE_STATE_PENDING).count()
        if not pending:
            self.stdout.write("No pending backup requests.\n")
            exit(0)

        in_progress = BackupRequest.objects.filter(state=BACKUP_RESTORE_STATE_IN_PROGRESS).count()

        request_to_treat = settings.CONCURRENT_BACKUP_REQUEST - in_progress
        if request_to_treat == 0:
            self.stdout.write("Maximum concurrent requests reached. Doing nothing.\n")
            exit(0)

        self.stdout.write("Can treat up to %i requests.\n" % (request_to_treat))

        pending_requests = BackupRequest.objects.filter(state=BACKUP_RESTORE_STATE_PENDING).order_by('creation_datetime')[:request_to_treat]
        self.stdout.write("%i requests will be treated.\n" % (len(pending_requests)))
        for request in pending_requests:
            request.backup()

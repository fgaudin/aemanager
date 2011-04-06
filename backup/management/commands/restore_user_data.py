from django.core.management.base import BaseCommand
from django.conf import settings
from backup.models import BackupRequest, BACKUP_RESTORE_STATE_IN_PROGRESS, \
    BACKUP_RESTORE_STATE_PENDING, RestoreRequest
import datetime

class Command(BaseCommand):
    help = 'Execute pending restore request'

    def handle(self, *args, **options):
        pending = RestoreRequest.objects.filter(state=BACKUP_RESTORE_STATE_PENDING).count()
        if not pending:
            self.stdout.write("No pending restore requests.\n")
            exit(0)

        in_progress = RestoreRequest.objects.filter(state=BACKUP_RESTORE_STATE_IN_PROGRESS).count()

        request_to_treat = settings.CONCURRENT_RESTORE_REQUEST - in_progress
        if request_to_treat == 0:
            self.stdout.write("Maximum concurrent requests reached. Doing nothing.\n")
            exit(0)

        self.stdout.write("Can treat up to %i requests.\n" % (request_to_treat))

        pending_requests = RestoreRequest.objects.filter(state=BACKUP_RESTORE_STATE_PENDING).order_by('creation_datetime')[:request_to_treat]
        self.stdout.write("%i requests will be treated.\n" % (len(pending_requests)))
        for request in pending_requests:
            #request.state = BACKUP_RESTORE_STATE_IN_PROGRESS
            request.last_state_datetime = datetime.datetime.now()
            request.save()

            request.restore()

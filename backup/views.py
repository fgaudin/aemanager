from core.decorators import settings_required
from autoentrepreneur.decorators import subscription_required
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _, ugettext
from backup.forms import BackupForm, RestoreForm, CSVForm
from backup.models import BACKUP_RESTORE_STATE_PENDING, \
    BACKUP_RESTORE_STATE_IN_PROGRESS, BackupRequest, RestoreRequest
import datetime
from django.core.urlresolvers import reverse
from django.db.transaction import commit_on_success
from django.contrib import messages
import os
from django.http import HttpResponseNotFound, HttpResponse
from django.utils.encoding import smart_str
from django.conf import settings
import unicodecsv
from accounts.models import Invoice

@settings_required
@commit_on_success
def backup(request):
    backup_request = None
    restore_request = None
    old_file = None
    action_pending = False
    try:
        backup_request = request.user.backuprequest
    except:
        pass

    try:
        restore_request = request.user.restorerequest
        old_file = restore_request.backup_file
    except:
        pass

    if (backup_request and backup_request.state <= BACKUP_RESTORE_STATE_IN_PROGRESS) \
    or (restore_request and restore_request.state <= BACKUP_RESTORE_STATE_IN_PROGRESS):
        action_pending = True

    backup_form = BackupForm(instance=backup_request)
    restore_form = RestoreForm(instance=restore_request)
    csv_form = CSVForm()

    if request.method == 'POST':
        if request.POST.get('backup_or_restore') == 'backup':
            backup_form = BackupForm(request.POST, instance=backup_request)
            if backup_form.is_valid():
                if action_pending:
                    messages.error(request, _("A backup or restore is already scheduled"))
                else:
                    backup_request = backup_form.save(commit=False)
                    backup_request.user = request.user
                    backup_request.state = BACKUP_RESTORE_STATE_PENDING
                    backup_request.creation_datetime = datetime.datetime.now()
                    backup_request.last_state_datetime = backup_request.creation_datetime
                    backup_request.save()
                    position = BackupRequest.objects.filter(state__lte=BACKUP_RESTORE_STATE_IN_PROGRESS).count()
                    messages.info(request, _("Your backup has been scheduled successfully. There are %i other backups before yours.") % (position - 1))
                    return redirect(reverse('backup'))
        elif request.POST.get('backup_or_restore') == 'restore':
            restore_form = RestoreForm(request.POST, request.FILES, instance=restore_request)
            if restore_form.is_valid():
                if request.FILES:
                    try:
                        if old_file:
                            if os.path.exists(old_file.path):
                                os.remove(old_file.path)
                    except:
                        pass

                if action_pending:
                    messages.error(request, _("A backup or restore is already scheduled"))
                else:
                    restore_request = restore_form.save(commit=False)
                    restore_request.user = request.user
                    restore_request.state = BACKUP_RESTORE_STATE_PENDING
                    restore_request.creation_datetime = datetime.datetime.now()
                    restore_request.last_state_datetime = restore_request.creation_datetime
                    restore_request.save()
                    position = RestoreRequest.objects.filter(state__lte=BACKUP_RESTORE_STATE_IN_PROGRESS).count()
                    messages.info(request, _("Your restore has been scheduled successfully. There are %i other restores before yours.") % (position - 1))
                    return redirect(reverse('backup'))
        else:
            messages.error(request, _("Form data have been tempered"))

    context = {
               'title': _('Backup'),
               'backup_request': backup_request,
               'restore_request': restore_request,
               'backup_form': backup_form,
               'restore_form': restore_form,
               'csv_form': csv_form,
               'action_pending': action_pending
               }
    return render_to_response('backup/index.html',
                              context,
                              context_instance=RequestContext(request))

@settings_required
def backup_download(request):
    try:
        backup_request = request.user.backuprequest
    except:
        return HttpResponseNotFound()

    response = HttpResponse(mimetype='application/force-download')
    response['Content-Disposition'] = 'attachment;filename="%s"'\
                                    % smart_str(backup_request.get_backup_filename())

    response["X-Sendfile"] = "%s%s/%s/%s" % (settings.FILE_UPLOAD_DIR, request.user.get_profile().uuid, 'backup', backup_request.get_backup_filename())
    return response

@settings_required
def csv_export(request):
    form = CSVForm(request.GET)
    if form.is_valid():
        begin_date = form.cleaned_data.get('begin_date')
        end_date = form.cleaned_data.get('end_date')

        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=export.csv'

        writer = unicodecsv.writer(response, encoding='utf-8')

        row = [ugettext('Reference'), ugettext('Customer'), ugettext('Address'), ugettext('State'), ugettext('Amount'),
               ugettext('Edition date'), ugettext('Payment date'), ugettext('Payment type'),
               ugettext('Paid date'), ugettext('Execution begin date'), ugettext('Execution end date'),
               ugettext('Penalty date'), ugettext('Penalty rate'), ugettext('Discount conditions')]
        writer.writerow(row)

        invoices = Invoice.objects.filter(owner=request.user)
        if begin_date:
            invoices = invoices.filter(edition_date__gte=begin_date)
        if end_date:
            invoices = invoices.filter(edition_date__lte=end_date)

        for invoice in invoices:
            row = [invoice.invoice_id, invoice.customer, invoice.customer.address, invoice.get_state_display(), invoice.amount,
                   invoice.edition_date, invoice.payment_date, invoice.get_payment_type_display(),
                   invoice.paid_date, invoice.execution_begin_date, invoice.execution_end_date,
                   invoice.penalty_date, invoice.penalty_rate, invoice.discount_conditions]
            writer.writerow(row)

        return response
    else:
        messages.error(request, _('Export dates are invalid'))
        return redirect(reverse('backup'))

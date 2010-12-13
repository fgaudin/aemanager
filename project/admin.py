from django.contrib import admin
from project.models import Project, Invoice, InvoiceRow, Proposal, ProposalRow
admin.site.register(Project)
admin.site.register(Invoice)
admin.site.register(InvoiceRow)
admin.site.register(Proposal)
admin.site.register(ProposalRow)

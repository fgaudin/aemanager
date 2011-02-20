from django.contrib import admin
from project.models import Project, Proposal, ProposalRow, Contract

admin.site.register(Contract)
admin.site.register(Project)
admin.site.register(Proposal)
admin.site.register(ProposalRow)

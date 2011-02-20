from django.contrib import admin
from bugtracker.models import Issue, Comment, Vote

admin.site.register(Issue)
admin.site.register(Comment)
admin.site.register(Vote)

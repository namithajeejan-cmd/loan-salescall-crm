from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Lead, CallLog, FollowUp

admin.site.register(User, UserAdmin)
admin.site.register(Lead)
admin.site.register(CallLog)
admin.site.register(FollowUp)

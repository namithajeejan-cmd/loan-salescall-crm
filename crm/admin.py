from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Lead, CallLog

admin.site.register(User, UserAdmin)
admin.site.register(Lead)
admin.site.register(CallLog)
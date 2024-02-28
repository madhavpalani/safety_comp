from django.contrib import admin

# Register your models here.
from .models import Employee1, Supervisor, Alert

admin.site.register(Employee1)
admin.site.register(Supervisor)
admin.site.register(Alert)

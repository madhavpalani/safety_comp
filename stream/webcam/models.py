from django.db import models

# Create your models here.
# Create your models here.
from django.db import models

class Employee1(models.Model):
    emp_id = models.IntegerField()
    name = models.CharField(max_length=100)
    email = models.EmailField()
    sup_id = models.IntegerField()

class Supervisor(models.Model):
    sup_id = models.IntegerField()
    name = models.CharField(max_length=100)
    email = models.EmailField()

class Alert(models.Model):
    name = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

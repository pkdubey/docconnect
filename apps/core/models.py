import uuid
from django.db import models


class Specialization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'specializations'
        ordering = ['name']

    def __str__(self):
        return self.name


class Qualification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'qualifications'
        ordering = ['name']

    def __str__(self):
        return self.name


class Council(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    short = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'councils'
        ordering = ['name']

    def __str__(self):
        return self.short

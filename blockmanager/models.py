from django.db import models


# Create your models here.
class VM(models.Model):
    name = models.CharField(max_length=200)
    uuid = models.CharField(max_length=200)
    host = models.CharField(max_length=200)
    instance_id = models.CharField(max_length=200)
    ip = models.CharField(max_length=200)
    tenant_id = models.CharField(max_length=200)


class Storage(models.Model):
    vm = models.ForeignKey(VM, null=True)
    block_name = models.CharField(max_length=200)
    block_path = models.CharField(max_length=200)
    xml_name = models.CharField(max_length=200, null=True)
    xml_path = models.CharField(max_length=200, null=True)
    size = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    tenant_id = models.CharField(max_length=200, null=True)
    created_at = models.DateTimeField('block created', null=True)
    mounted_at = models.DateTimeField('block mounted', null=True)
    mountpoint = models.CharField(max_length=200, null=True)
    is_mounted = models.BooleanField(False)
    host_group = models.CharField(max_length=200, null=True)
    used_size = models.CharField(max_length=200, null=True)
    uuid = models.CharField(max_length=200)


class Snapshot(models.Model):
    storage = models.ForeignKey(Storage)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(max_length=200)
    snapshot_path = models.CharField(max_length=200)

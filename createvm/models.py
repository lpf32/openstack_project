from django.db import models

# Create your models here.

class Member(models.Model):
	name = models.CharField(max_length=200)
	is_active = models.BooleanField(False)


class Vm(models.Model):
	member = models.ForeignKey(Member, null=True)
	name = models.CharField(max_length=200)
	os = models.CharField(max_length=200)
	create_at = models.DateTimeField('vm created', null=True)
	cpuAndRam = models.CharField(max_length=200)


class Network(models.Model):
	member = models.ForeignKey(Member, null=True)
	name = models.CharField(max_length=200)
	ip = models.CharField(max_length=200)
	netmask = models.CharField(max_length=200)
	vlan_id = models.CharField(max_length=200)
	start = models.CharField(max_length=200)
	end = models.CharField(max_length=200)
	is_used = models.BooleanField(False)

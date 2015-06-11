#coding=utf-8
from django.shortcuts import render,get_object_or_404,render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.template import RequestContext

import string
import ansible.runner
import ConfigParser
import uuid
from blockmanager.models import VM, Storage, Snapshot
from lxml import etree
import random

from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client
# Create your views here.


def index(request):
	blocks = Storage.objects.all()
	
	#return render(request, 'blockmanager/index.html', {'blocks': blocks})
	return render_to_response('blockmanager/index.html', {'blocks': blocks}, context_instance=RequestContext(request))


def get_vms():
	return HttpResponse('success ajax!')


def create_block(request):
	try:
		#验证input
		configs = get_config()
		block_name = request.POST['name']
		if block_name == '':
			raise ValueError('block name field is empty')

		size = request.POST['size']
		if(size == ''):
			raise ValueError('size field is empty')
		size = int(size)
		
		block_type = request.POST['type']
		if block_type == '':
			raise ValueError('block_type field is empty')
		if block_type not in configs['block_type']:
			raise ValueError('block type is undefined')
		
		#筛选出一个合适的host
		res = ansible.runner.Runner(module_name='ping', module_args='', pattern='compute', forks=10).run()
		compute_nodes = res['contacted']
		des_node = compute_nodes.keys()[int(random.random() * len(compute_nodes))]

		#得到block 的uuid, 并确保唯一性
		block_uuid = uuid.uuid1().hex

		#调用API，在筛选出的host上创建block
		if block_type == 'qcow2':
			args = '/usr/bin/qemu-img create -f qcow2 -o preallocation=metadata ' + configs['block_path'] + '/'  + block_uuid + '.qcow2 ' + str(size) + 'G'
		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=des_node, forks=10).run()
		if res['contacted'][des_node]['stderr'] != '':
			raise ValueError(res['contacted'][des_node]['stderr'])
		
		#如果成功就将此条数据，插入数据库，失败返回 ERROR
		block = Storage()
		block.block_name = block_name
		block.block_path = configs['block_path'] + '/' + block_uuid + '.' + block_type
		block.size = str(size)
		block.type = block_type
		block.crated_at = timezone.now()
		block.is_mounted = False
		block.uuid = block_uuid
		block.save()
		return HttpResponseRedirect(reverse('blockmanager:index'))
	except Exception, e:
		return HttpResponse(e)

	
def import_block(request):
	try:
		#验证input
		configs = get_config()
		block_name = request.POST['name']
		if block_name == '':
			raise ValueError('block name field is empty')
		if len(block_name.split('.')) > 1:
			raise ValueError('block name is invalid')

		size = request.POST['size']
		if(size == ''):
			raise ValueError('size field is empty')
		size = int(size)
		
		block_type = request.POST['type']
		if block_type == '':
			raise ValueError('block_type field is empty')
		if block_type not in configs['block_type']:
			raise ValueError('block type is undefined')

		#筛选出一个合适的host
		res = ansible.runner.Runner(module_name='ping', module_args='', pattern='compute', forks=10).run()
		compute_nodes = res['contacted']
		des_node = compute_nodes.keys()[int(random.random() * len(compute_nodes))]
		#验证block 是否存在
		args = 'ls ' + configs['block_path'] + '/' + block_name + '.' + block_type
		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=des_node, forks=10).run()
		if res['contacted'][des_node]['stderr'] != '':
			raise ValueError('the block is not exist!')

		#如果成功就将此条数据，插入数据库，失败返回 ERROR
		block = Storage()
		block.block_name = block_name
		block.block_path = configs['block_path'] + '/' + block_uuid + '.' + block_type
		block.size = str(size)
		block.type = block_type
		block.crated_at = timezone.now()
		block.is_mounted = False
		block.uuid = block_name
		block.save()

	except Exception, e:
		return HttpResponse(e)


def search(request):
	try:
		#根据条件，查询结果，失败返回 ERROR
		block_name = request.POST['name']
		block_type = request.POST['type']
		vm_name = request.POST['vm']
		if block_name == '' and block_type == '' and vm_name == '':
			raise ValueError('can\'t all empty')
		elif block_name != '' and block_type!= '':
			blocks = Storage.objects.filter(block_name=block_name, type=block_type)
		elif block_name != '' and vm_name != '':
			blocks = Storage.objects.filter(block_name=block_name, vm__name=vm_name)
		elif block_type != '' and vm_name != '':
			blocks = Storage.objects.filter(type=block_type, vm__name=vm_name)
		elif block_name != '':
			blocks = Storage.objects.filter(block_name=block_name)
		elif block_type != '':
			blocks = Storage.objects.filter(type=block_type)
		elif vm_name != '':
			blocks = Storage.objects.filter(vm__name=vm_name)

		#在template，显示结果
	except Exception,e:
		return HttpResponse(e)
		
	
def mount(request):
	try:
		configs = get_config()
		#验证参数正确性，vm uuid，block uuid，如果错误 return ERROR
		vm_uuid = request.POST['vm_uuid']
		block_uuid = request.POST['block_uuid']
		if vm_uuid == '' or block_uuid == '':
			raise ValueError('fields can\'t be empty!')
		
		#通过block uuid 查询block，如果没有 return ERROR
		block = get_object_or_404(Storage, uuid=block_uuid)

		#通过nova api 得到 vm 实例，如果找不到，reuturn ERROR
		auth = v2.Password(auth_url=configs['auth_url'], username=configs['username'], 
				password=configs['password'], tanant_name=configs['tenant_name'])
		sess = session.Session(auth=auth)
		nova = client.Client('2', session=sess)
		des_vm = nova.servers.get('3249f9ed-d3bb-4064-a427-7d42081825ca')
		instance_name = getattr(des_vm, 'OS-EXT-SRV-ATTR:instance_name')
		host_name = getattr(des_vm, 'OS-EXT-SRV-ATTR:hypervisor_hostname')

		if host_name not in configs['hosts']:
			raise ValueError('vm host is not in config.py')
		#xml_name = $(block_uuid).xml。 build uxml文件， 如果返回失败，return ERROR
		xml_name = block_uuid + '.xml'

		#得到挂载点
		mounted_blocks = Storage.objects.filter(vm__uuid=vm_uuid, is_mounted=True).order_by('mountpoint')
		if len(mounted_blocks) == 0:
			mountpoint = 'vdb'
		else:
			mountpoint = "vd" + string.ascii_lowercase[len(mounted_blocks) + 1]

		#bulid xml 文件
		root = etree.Element('disk', type='file', device='disk')
		dirver = etree.Element('dirver', name='qemu', type='raw', cache='none')
		source = etree.Element('source', file=block.block_path)
		target = etree.Element('target', dev=mountpoint, bus='virtio')
		root.append(dirver)
		root.append(source)
		root.append(target)
		sXml = etree.tostring(root, pretty_print=True)
		f = open('xml/' + xml_name, 'w')
		f.write(sXml)

		#将xml文件，发送的vm.host
		args = 'src=xml/' + xml_name + ' dest=' + configs['xml_path']
		res = ansible.runner.Runner(module_name='copy', module_args=args, pattern=host_name, forks=10).run()
		if res['contacted'][host_name]['failed'] == True:
			raise ValueError('transit xml file failure!')

		#挂载硬盘
		args = '/usr/bin/virsh attach-device ' + mountpoint + ' ' + configs['xml_path'] + '/' +  xml_name
		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=host_name, forks=10).run()
		if res['contacted'][des_node]['stderr'] != '':
			raise ValueError('block mounted failure!')

		#update 数据库
		vms = VM.objects.filter(uuid=vm_uuid)
		if len(vms) == 0:
			vm = VM()
			vm.uuid = vm_uuid
			vm.host = host_name
			vm.instance_id = instance_id
			vm.ip = des_vm.networks[des_vm.networks.keys()[0]]
			vm.tenant_id = des_vm.tenant_id
			vm.storage_set.add(block)
			vm.save()

		block.xml_name = xml_name
		block.xml_path = configs['xml_path'] + '/' +  xml_name
		block.mounted_at = timezone.now()
		block.mountpoint = mountpoint
		block.is_mounted = True
		block.save()

	except Exception,e:
		return HttpResponse(e)


def umount(request):
	try:
		#根据条件，查询结果，失败返回 ERROR
		block_uuid = request.POST['uuid']
		#取得block，vm 实例
		block = get_object_or_404(Storage, uuid=block_uuid)
		vm = VM.objects.filter(storage=block.id)
		#根据实例参数，调用API，卸载block， 如果失败  return ERROR
		args = '/usr/bin/virsh detach-device ' + vm.instance_id + ' ' + block.xml_path + ' --live' 
		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=vm.host, forks=10).run()
		if res['contacted'][des_node]['stderr'] != '':
			raise ValueError("detach device failure!")

		#update 数据库
		block.mounted_at = ''
		block.mountpoint = ''
		block.is_mounted = False
		block.save()

	except Exception,e:
		return HttpResponse(e)


def delete(request):
	try:
		#根据条件，查询结果，失败返回 ERROR
		block_uuid = request.POST['uuid']
		#取得block，vm 实例
		block = get_object_or_404(Storage, uuid=block_uuid)
		block.delete()
	except Exception,e:
		return HttpResponse(e)


def get_config():
	try:
		config = ConfigParser.ConfigParser()
		config.read("blockmanager/config.py")

		block_path = config.get('block', 'path')
		block_type = config.get('block', 'type')
		xml_path = config.get('xml', 'path')
		compute_nodes = config.get('compute', 'hosts')
		auth_url = config.get('auth', 'auth_url')
		username = config.get('auth', 'username')
		password = config.get('auth', 'password')
		tenant_name = config.get('auth', 'tenant_name')

		configs = {'block_path': block_path, 'xml_path': xml_path, 'compute_nodes': compute_nodes, 'block_type': block_type}
		configs['auth_url'] = auth_url
		configs['username']	= username
		configs['password'] = password
		configs['tenant_name'] = tenant_name
		return configs
	except ConfigParser.NoSectionError, e:
		return HttpResponse('config parser error: ' + str(e))
	except Exception, e:
		return HttpResponse(str(e))
		



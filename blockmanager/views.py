#coding=utf-8
from django.shortcuts import render,get_object_or_404,render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.template import RequestContext
from django_ajax.decorators import ajax
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import string
import ansible.runner
import ConfigParser
import uuid
from blockmanager.models import VM, Storage, Snapshot
from lxml import etree
import random
import logging
import logging.config

from keystoneclient.auth.identity import v2
from keystoneclient import session
from novaclient import client
# Create your views here.


def login(request):
	try:
		if request.method == 'GET':
			return render(request,'blockmanager/login.html')
		configs = get_config()
		username = request.POST.get('username', None)
		password = request.POST.get('password', None)
		tenant_name = request.POST.get('tenant_name', None)

		auth = v2.Password(auth_url=configs['auth_url'], username=username, 
				password=password, tenant_name=tenant_name)
		sess = session.Session(auth=auth)
		nova = client.Client('2', session=sess)
		nova.servers.list()

		request.session['username'] = username
		request.session['password'] = password
		request.session['tenant_name'] = tenant_name
		return HttpResponseRedirect(reverse('blockmanager:index'))
	except Exception,e:
		name = request.session.get('username', 'root')
		logger = getLogger(name)
		logger.error(e)
		return HttpResponse(e)


def logout(request):
	try:
		request.session['username'] = None
		request.session['password'] = None
		request.session['tenant_name'] = None
		return HttpResponseRedirect(reverse('blockmanager:login'))
	except Exception,e:
		return HttpResponse(e)
	


def index(request):
	if request.session.get('username', None) == None:
		return HttpResponseRedirect(reverse('blockmanager:login'))
	configs = get_config()
	compute_group = configs['compute_group'].split(',')
	blocks = Storage.objects.all()
	paginator = Paginator(blocks, 10)
	page = request.GET.get('page');
	try:
		contacts = paginator.page(page)
	except PageNotAnInteger:
		contacts = paginator.page(1)
	except EmptyPage:
		contacts = paginator.page(paginator.num_pages)
	
	#return render(request, 'blockmanager/index.html', {'blocks': blocks})
	return render_to_response('blockmanager/index.html', {'contacts': contacts, 'compute_group':compute_group, 'username': request.session.get('username', None)}, context_instance=RequestContext(request))


@ajax
def get_vms(request):
	try:
		#验证input
		configs = get_config()
		ip = request.GET.get('the_ip')	
		name = request.GET.get('the_name')	
		if ip == '' and name == '':
			raise ValueError("argument error!")

		#通过nova api 取得nova servers list
		auth = v2.Password(auth_url=configs['auth_url'], username=configs['username'], 
				password=configs['password'], tenant_name=configs['tenant_name'])
		sess = session.Session(auth=auth)
		nova = client.Client('2', session=sess)
		vms = nova.servers
		vms = nova.servers.list()

		#得到符合要求的vms
		des_vms = []
		for vm in vms:
			if ip != '' and name != '':
				if vm.name == name and vm.networks[vm.networks.keys()[0]][0] == ip:
					des_vms.append(vm)
			elif ip != '':
				if vm.networks[vm.networks.keys()[0]][0] == ip:
					des_vms.append(vm)
			elif name != '':
				if vm.name == name:
					des_vms.append(vm)
					#return HttpResponse(vm.id)

		#生成html代码
		html_str = ''
		for vm in des_vms:
			html_str += '<tr>\n<td><input type="radio" name="xj-select" /></td>\n' \
					+ '<td>'+ vm.name + '</td>\t' + '<td>'+ vm.networks[vm.networks.keys()[0]][0] \
					+ '</td>\t' + '<td name="vm_uuid">' + vm.id +'</td></tr>' + '<input type="hidden" name="vm_uuid" value="' \
					+ vm.id + '"/>'


		return HttpResponse(html_str)

	except Exception,e:
		return HttpResponse(e)


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

		compute_group = request.POST.get('compute_group')
		if compute_group == '':
			raise ValueError('compute group field is empty')
		
		#筛选出一个合适的host
		res = ansible.runner.Runner(module_name='ping', module_args='', pattern=compute_group, forks=10).run()
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
		block.size = str(size) + 'G'
		block.type = block_type
		block.crated_at = timezone.now()
		block.is_mounted = False
		block.uuid = block_uuid
		block.compute_group = compute_group
		block.save()

		#log
		name = ''
		mesStr = request.session.get('username', 'root') + ' create block ' + str(size) + 'G named ' + block_name
		logger = getLogger(name)
		logger.info(mesStr)

		#success
		return HttpResponseRedirect(reverse('blockmanager:index'))
	except Exception, e:
		name = request.session.get('username', 'root')
		logger = getLogger(name)
		logger.error(e)
		return HttpResponse(e)

	
def import_block(request):
	try:
		#验证input
		configs = get_config()
		block_name = request.POST.get('name')
		compute_group = request.POST.get('compute_group')
		if block_name == '':
			raise ValueError('block name field is empty')
		if compute_group == '':
			raise ValueError('compute group field is empty')

		#筛选出一个合适的host
		res = ansible.runner.Runner(module_name='ping', module_args='', pattern=compute_group, forks=10).run()
		compute_nodes = res['contacted']
		des_node = compute_nodes.keys()[int(random.random() * len(compute_nodes))]
		#验证block 是否存在
		args = 'ls ' + configs['block_path'] + '/' + block_name
		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=des_node, forks=10).run()
		if res['contacted'][des_node]['stderr'] != '':
			raise ValueError('the block is not exist!')
		
		#如果已经导入过返回ERROR
		result = Storage.objects.filter(uuid=block_name)
		if len(result) > 0:
			raise ValueError('已经导入过，不能重复导入')

		#得到block 的虚拟大小、实际使用大小、类型
		args = '/usr/bin/qemu-img info ' + configs['block_path'] + '/' + block_name
		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=des_node, forks=10).run()
		d = {}
		for s in res['contacted'][des_node]['stdout'].split('\n'):
			item = s.split(":")
			if item[0].strip() == 'file format' or item[0].strip() == 'virtual size' \
					or item[0].strip() == 'disk size':
				key, value = item
				d[key.strip()] = value.strip()



		#如果成功就将此条数据，插入数据库，失败返回 ERROR
		block = Storage()
		block.block_name = block_name
		block.block_path = configs['block_path'] + '/' + block_name
		block.size = d['virtual size'].split('(')[0]
		block.type = d['file format']
		block.used_size = d['disk size']
		block.crated_at = timezone.now()
		block.is_mounted = False
		block.uuid = block_name
		block.compute_group = compute_group
		block.save()

		#log
		name = ''
		mesStr = request.session.get('username', 'root') + ' import block ' + d['virtual size'].split('(')[0] + ' named ' + block_name
		logger = getLogger(name)
		logger.info(mesStr)

		return HttpResponseRedirect(reverse('blockmanager:index'))

	except Exception, e:
		name = request.session.get('username', 'root')
		logger = getLogger(name)
		logger.error(e)
		return HttpResponse(e)


def search(request):
	try:
		if request.session.get('username', None) == None:
			return HttpResponseRedirect(reverse('blockmanager:login'))
		#根据条件，查询结果，失败返回 ERROR
		configs = get_config()
		compute_group = configs['compute_group'].split(',')
		block_name = request.POST.get('name')
		block_type = request.POST.get('type')
		vm_name = request.POST.get('vm_name')
		if block_name == '' and block_type == '' and vm_name == '':
			blocks = Storage.objects.all()
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
		if block_name == None and block_type == None and vm_name == None:
			blocks = Storage.objects.all()

		#在template，显示结果
		paginator = Paginator(blocks, 10)
		page = request.GET.get('page');
		try:
			contacts = paginator.page(page)
		except PageNotAnInteger:
			contacts = paginator.page(1)
		except EmptyPage:
			contacts = paginator.page(paginator.num_pages)
	
	#return render(request, 'blockmanager/index.html', {'blocks': blocks})
		return render_to_response('blockmanager/index.html', {'contacts': contacts, 'compute_group': compute_group, 'username': request.session.get('username', None)}, context_instance=RequestContext(request))
	except Exception,e:
		return HttpResponse(e)
		
	
def mount(request):
	try:
		configs = get_config()
		#验证参数正确性，vm uuid，block uuid，如果错误 return ERROR
		vm_uuid = request.POST['vm_uuid']
		block_id = request.POST['block_id']
		if vm_uuid == '' or block_id == '':
			raise ValueError('fields can\'t be empty!')
		
		#通过block uuid 查询block，如果没有 return ERROR
		block = get_object_or_404(Storage, pk=block_id)
		block_uuid = block.uuid

		#如果已经挂载直接退出
		if block.is_mounted == True:
			return HttpResponse('已经挂载过！')

		#通过nova api 得到 vm 实例，如果找不到，return ERROR
		auth = v2.Password(auth_url=configs['auth_url'], username=configs['username'], 
				password=configs['password'], tenant_name=configs['tenant_name'])
		sess = session.Session(auth=auth)
		nova = client.Client('2', session=sess)
		des_vm = nova.servers.get(vm_uuid)
		instance_id = getattr(des_vm, 'OS-EXT-SRV-ATTR:instance_name')
		host_name = getattr(des_vm, 'OS-EXT-SRV-ATTR:hypervisor_hostname')

		#根据block compute group 得到所有可能的compute node，如果vm 不在这些compute node中，return ERROR
		res = ansible.runner.Runner(module_name='ping', module_args='', pattern=block.compute_group, forks=10).run()
		compute_nodes = res['contacted']

		if host_name not in compute_nodes:
			raise ValueError('vm and block are not in the same compute group!')

		#如果block 的 tenant_id不一致， 不能挂载
		if block.tenant_id != None and block.tenant_id != des_vm.tenant_id:
			raise ValueError("tenant id 不一致");

		#xml_name = $(block_uuid).xml。 build uxml文件， 如果返回失败，return ERROR
		xml_name = block_uuid + '.xml'

		#得到挂载点
		mounted_blocks = Storage.objects.filter(vm__uuid=vm_uuid, is_mounted=True).order_by('mountpoint')
		if len(mounted_blocks) == 0:
			mountpoint = 'vdb'
		else:
			mountpoint = "vd" + string.ascii_lowercase[len(mounted_blocks) + 1]

		if len(mounted_blocks) != 0 and mounted_blocks[len(mounted_blocks) - 1].mountpoint >= mountpoint:
			mountpoint = 'vd' + string.ascii_lowercase[string.ascii_lowercase.index(mounted_blocks[len(mounted_blocks) - 1].mountpoint[-1]) + 1]

		#bulid xml 文件
		root = etree.Element('disk', type='file', device='disk')
		dirver = etree.Element('dirver', name='qemu', type='qcow2', cache='none')
		source = etree.Element('source', file=block.block_path)
		target = etree.Element('target', dev=mountpoint, bus='virtio')
		root.append(dirver)
		root.append(source)
		root.append(target)
		sXml = etree.tostring(root, pretty_print=True)
		f = open('xml/' + xml_name, 'w')
		f.write(sXml)
		f.close()

		#将xml文件，发送的vm.host
		#args = 'src=xml/' + xml_name + ' dest=' + configs['xml_path']
		args = 'src=xml/' + xml_name +' dest=' + configs['xml_path']
		res = ansible.runner.Runner(module_name='copy', module_args=args, pattern=host_name, forks=10).run()

		#验证xml文件传输是否成功
		args = 'ls ' + configs['xml_path'] + '/' + xml_name
		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=host_name, forks=10).run()
		if res['contacted'][host_name]['stderr'] != '':
			raise ValueError('the block is not exist!</p>' + res['contacted'][host_name]['stderr'])

		#挂载硬盘
		args = '/usr/bin/virsh attach-device ' + instance_id + ' ' + configs['xml_path'] + '/' +  xml_name
		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=host_name, forks=10).run()
		if res['contacted'][host_name]['stderr'] != '':
			raise ValueError('block mounted failure!</p>' + res['contacted'][host_name]['stderr'])

		#update 数据库
		vms = VM.objects.filter(uuid=vm_uuid)
		if len(vms) == 0:
			vm = VM()
			vm.uuid = vm_uuid
			vm.host = host_name
			vm.instance_id = instance_id
			vm.ip = des_vm.networks[des_vm.networks.keys()[0]][0]
			vm.tenant_id = des_vm.tenant_id
			vm.name = des_vm.name
			vm.save()
			vm.storage_set.add(block)
			vm.save()
		else:
			vm = vms[0]
			vm.storage_set.add(block)
			vm.save()

		block.xml_name = xml_name
		block.xml_path = configs['xml_path'] + '/' +  xml_name
		block.mounted_at = timezone.now()
		block.mountpoint = mountpoint
		block.is_mounted = True
		block.tenant_id = des_vm.tenant_id
		block.save()


		#log
		mesStr = request.session.get('username', 'root') + ' mount ' + block.uuid + ' at ' + mountpoint + ' on ' + vm.name
		name = ''
		logger = getLogger(name)
		logger.info(mesStr)

		return HttpResponseRedirect(reverse('blockmanager:index'))

	except KeyError,e:
		return HttpResponse('KeyError: ' + str(e))
	except Exception,e:
		name = request.session.get('username', 'root')
		logger = getLogger(name)
		logger.error(e)
		return HttpResponse(e)


def umount(request):
	try:
		#根据条件，查询结果，失败返回 ERROR
		block_id = request.POST.get('block_id')
		#取得block，vm 实例
		block = get_object_or_404(Storage, pk=block_id)
		vm = VM.objects.get(storage__id=block.id)
		#判断是否重复卸载
		if block.is_mounted == False:
			raise ValueError("此存储没有被挂载")
		#根据实例参数，调用API，卸载block， 如果失败  return ERROR
		args = '/usr/bin/virsh detach-device ' + vm.instance_id + ' ' + block.xml_path + ' --live' 
		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=vm.host, forks=10).run()
		if res['contacted'][vm.host]['stderr'] != '':
			raise ValueError("detach device failure!</p>" + res['contacted'][vm.host]['stderr'])


		mountpoint = block.mountpoint
		#update 数据库
		block.mounted_at = None
		block.mountpoint = None
		block.is_mounted = False
		block.save()

		#log
		name = ''
		mesStr = request.session.get('username', 'root') + ' unmount ' + str(block.uuid) + ' off ' + str(mountpoint) + ' on ' + str(vm.name)
		logger = getLogger(name)
		logger.info(mesStr)

		return HttpResponse('success')

	except KeyError,e:
		return HttpResponse('KeyError: ' + str(e))
	except Exception,e:
		name = request.session.get('username', 'root')
		logger = getLogger(name)
		logger.error(e)
		return HttpResponse(e)


def delete(request):
	try:
		#根据条件，查询结果，失败返回 ERROR
		block_id = request.POST.get('block_id')

		#取得block，vm 实例
		block = get_object_or_404(Storage, pk=block_id)

		#如果此block 处于挂载状态，返回错误
		if block.is_mounted == True:
			raise ValueError("请先卸载，再删除！")

		#筛选出一个合适的host
		res = ansible.runner.Runner(module_name='ping', module_args='', pattern=block.compute_group, forks=10).run()
		compute_nodes = res['contacted']
		des_node = compute_nodes.keys()[int(random.random() * len(compute_nodes))]

		#删除block
		if block.xml_path == None:
			args = 'rm -f ' + block.block_path
		else:
			args = 'rm -f ' + block.block_path + ' ' + block.xml_path

		res = ansible.runner.Runner(module_name='shell', module_args=args, pattern=des_node, forks=10).run()
		if res['contacted'][des_node]['stderr'] != '':
			raise ValueError(res['contacted'][des_node]['stderr'])

		block.delete()

		#log
		name = ''
		mesStr = request.session.get('username', 'root') + ' delete block ' + block.uuid + ' named ' + block.block_name
		logger = getLogger(name)
		logger.info(mesStr)

		return HttpResponse('success')
	except KeyError,e:
		return HttpResponse('KeyError' + str(e))
	except Exception,e:
		name = request.session.get('username', 'root')
		logger = getLogger(name)
		logger.error(e)
		return HttpResponse(e)


def get_config():
	try:
		config = ConfigParser.ConfigParser()
		config.read("blockmanager/config.py")

		block_path = config.get('block', 'path')
		block_type = config.get('block', 'type')
		xml_path = config.get('xml', 'path')
		compute_nodes = config.get('compute', 'hosts')
		compute_group = config.get('compute', 'compute_group')
		auth_url = config.get('auth', 'auth_url')
		username = config.get('auth', 'username')
		password = config.get('auth', 'password')
		tenant_name = config.get('auth', 'tenant_name')

		configs = {'block_path': block_path, 'xml_path': xml_path, 'compute_nodes': compute_nodes, 'block_type': block_type}
		configs['auth_url'] = auth_url
		configs['username']	= username
		configs['password'] = password
		configs['tenant_name'] = tenant_name
		configs['compute_group'] = compute_group
		return configs
	except ConfigParser.NoSectionError, e:
		return HttpResponse('config parser error: ' + str(e))
	except Exception, e:
		return HttpResponse(str(e))
		

def getLogger(name):
	try:
		if name == '' or name == None:
			name = ''

		logging.config.fileConfig('blockmanager/log.conf')
		logger = logging.getLogger(name)
		return logger
	except Exception,e:
		return HttpResponse(e)

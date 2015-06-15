[block]
path: /var/lib/nova/instances/block
type: qcow2

[xml]
path: /var/lib/nova/instances/xml

[compute]
hosts: node02.openstack.com, node03.openstack.com

[auth]
auth_url: http://control:35357/v2.0
username: admin
password: aptech3#
tenant_name: admin

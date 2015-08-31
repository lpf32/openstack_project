#!/bin/bash


neutron net-create $1 --provider:network_type vlan --provider:physical_network physnet1 --provider:segmentation_id $4 --router:external=True

neutron subnet-create $1 $2 --name public_subnet --enable_dhcp=True --allocation-pool start=10.0.0.200,end=10.0.0.220 --gateway=$3

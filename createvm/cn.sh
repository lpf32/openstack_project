#!/bin/bash


neutron net-create $1 --provider:network_type vlan --provider:physical_network physnet1 --provider:segmentation_id $4 --router:external=True

neutron subnet-create $1 $2 --name public_subnet --enable_dhcp=True --allocation-pool start=$5,end=$6 --gateway=$3

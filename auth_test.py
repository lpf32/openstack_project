#!/usr/bin/python

import json
import urllib2

auth = None

def curl_auth():
	url = 'http://control:35357/v2.0/tokens'
	values = {"auth":{"passwordCredentials":{"username":"admin", "password":"aptech3#"}, "tenantName":"admin"}}
	params = json.dumps(values)
	headers = {"Content-type":"application/json","Accept":"application/json"}
	req = urllib2.Request(url, params, headers)
	response = urllib2.urlopen(req)

	return json.loads(response.read())

def get_tenants():
	if auth.get("access", None) != None:
		token = auth['access']['token']['id'] 
		endpoint = get_endpoint('identity')
		url = endpoint[0].get('publicURL') + '/tenants'
		headers = {"X-Auth-Token":token}
		req = urllib2.Request(url, headers=headers)
		response = urllib2.urlopen(req)
		#response = urllib2.urlopen(url)
		
		print response.read()


def get_endpoint(endpoint_type):
	for ep in auth['access']['serviceCatalog']:
		if ep.get('type') == endpoint_type:
			return ep['endpoints']



def get_flavors():
	if auth.get("access", None) != None:
		token = auth['access']['token']['id'] 
		endpoint = get_endpoint('compute')
		url = endpoint[0].get('publicURL') + '/flavors'
		headers = {"X-Auth-Token":token}
		req = urllib2.Request(url, headers=headers)
		response = urllib2.urlopen(req)
		#response = urllib2.urlopen(url)
		print response.read()
		

def get_images():
	if auth.get("access", None) != None:
		token = auth['access']['token']['id'] 
		endpoint = get_endpoint('compute')
		url = endpoint[0].get('publicURL') + '/images'
		headers = {"X-Auth-Token":token}
		req = urllib2.Request(url, headers=headers)
		response = urllib2.urlopen(req)
		#response = urllib2.urlopen(url)
		print response.read()


if __name__ == "__main__":
	auth = curl_auth()
	#get_tenants()
	#get_flavors()
	get_images()

import ConfigParser

config = ConfigParser.ConfigParser()
config.read("config.py")
print config.get('compute', 'hosts')
print config.get('auth', 'password')


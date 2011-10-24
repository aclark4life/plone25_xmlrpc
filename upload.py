import xmlrpclib

filename = 'screenshot.png'
mimetype = 'application/octet-stream'

try:
    proxy = xmlrpclib.ServerProxy('http://admin:admin@localhost:8080/Plone', verbose=True)
    proxy.invokeFactory('Image', filename)
except:
    pass

try:
    data = open(filename).read()
    proxy = xmlrpclib.ServerProxy('http://admin:admin@localhost:8080/Plone/screenshot.png', verbose=True)
    proxy.setImage(xmlrpclib.Binary(data))
except:
    pass

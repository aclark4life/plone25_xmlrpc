import xmlrpclib

filename = 'screenshot.png'
mimetype = 'application/octet-stream'

try:
    proxy = xmlrpclib.ServerProxy('http://admin:admin@localhost:8080/Plone', verbose=True)
    proxy.invokeFactory('Image', filename)
except:
    pass

try:
    proxy = xmlrpclib.ServerProxy('http://admin:admin@localhost:8080/Plone/screenshot.png', verbose=True)
    wrappedData = xmlrpclib.Binary(open(filename).read())
    proxy.setImage(wrappedData)
except:
    pass

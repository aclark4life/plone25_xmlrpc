from OFS import Image
import xmlrpclib

filename = 'screenshot.png'
mimetype = 'application/octet-stream'

try:
    proxy = xmlrpclib.ServerProxy('http://admin:admin@localhost:8080/Plone')
    proxy.invokeFactory('Image', filename)
except:
    pass

try:
    proxy = xmlrpclib.ServerProxy('http://localhost:8080/Plone/screenshot.png')
    infile = open('screenshot.png')
    data = File(filename, filename, infile, mimetype)
    proxy.setImage(data)
except:
    pass

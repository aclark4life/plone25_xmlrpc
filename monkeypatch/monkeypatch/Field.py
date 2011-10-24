import xmlrpclib

def _process_input(self, value, file=None, default=None, mimetype=None,
                   instance=None, filename='', **kwargs):
    if file is None:
        file = self._make_file(self.getName(), title='',
                               file='', instance=instance)
    if IBaseUnit.isImplementedBy(value):
        mimetype = value.getContentType() or mimetype
        filename = value.getFilename() or filename
        value = value.getRaw()
    elif isinstance(value, self.content_class):
        filename = getattr(value, 'filename', value.getId())
        mimetype = getattr(value, 'content_type', mimetype)
        return value, mimetype, filename
    elif isinstance(value, File):
        # In case someone changes the 'content_class'
        filename = getattr(value, 'filename', value.getId())
        mimetype = getattr(value, 'content_type', mimetype)
        value = value.data
    elif isinstance(value, xmlrpclib.Binary):
        value = value.data
    elif isinstance(value, FileUpload) or shasattr(value, 'filename'):
        filename = value.filename
    elif isinstance(value, FileType) or shasattr(value, 'name'):
        # In this case, give preference to a filename that has
        # been detected before. Usually happens when coming from PUT().
        if not filename:
            filename = value.name
            # Should we really special case here?
            for v in (filename, repr(value)):
                # Windows unnamed temporary file has '<fdopen>' in
                # repr() and full path in 'file.name'
                if '<fdopen>' in v:
                    filename = ''
    elif isinstance(value, basestring):
        # Let it go, mimetypes_registry will be used below if available
        pass
    elif (isinstance(value, Pdata) or (shasattr(value, 'read') and
                                       shasattr(value, 'seek'))):
        # Can't get filename from those.
        pass
    elif value is None:
        # Special case for setDefault
        value = ''
    else:
        klass = getattr(value, '__class__', None)
        raise FileFieldException('Value is not File or String (%s - %s)' %
                                 (type(value), klass))
    filename = filename[max(filename.rfind('/'),
                            filename.rfind('\\'),
                            filename.rfind(':'),
                            )+1:]
    file.manage_upload(value)
    if mimetype is None or mimetype == 'text/x-unknown-content-type':
        body = file.data
        if not isinstance(body, basestring):
            body = body.data
        mtr = getToolByName(instance, 'mimetypes_registry', None)
        if mtr is not None:
            kw = {'mimetype':None,
                  'filename':filename}
            # this may split the encoded file inside a multibyte character
            try:
                d, f, mimetype = mtr(body[:8096], **kw)
            except UnicodeDecodeError:
                d, f, mimetype = mtr(len(body) < 8096 and body or '', **kw)
        else:
            mimetype = getattr(file, 'content_type', None)
            if mimetype is None:
                mimetype, enc = guess_content_type(filename, body, mimetype)
    # mimetype, if coming from request can be like:
    # text/plain; charset='utf-8'
    mimetype = str(mimetype).split(';')[0].strip()
    setattr(file, 'content_type', mimetype)
    setattr(file, 'filename', filename)
    return file, mimetype, filename

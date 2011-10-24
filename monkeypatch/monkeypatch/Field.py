import xmlrpclib

from __future__ import nested_scopes

import sys

from copy import deepcopy
from cgi import escape
from cStringIO import StringIO
from logging import ERROR
from types import ListType, TupleType, ClassType, FileType, DictType, IntType
from types import StringType, UnicodeType, StringTypes

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from Acquisition import Implicit
from BTrees.OOBTree import OOBTree
from ComputedAttribute import ComputedAttribute
from DateTime import DateTime
from ExtensionClass import Base
from Globals import InitializeClass
from OFS.Image import File
from OFS.Image import Pdata
from OFS.Image import Image as BaseImage
from OFS.Traversable import Traversable
from OFS.Cache import ChangeCacheSettingsPermission
from ZPublisher.HTTPRequest import FileUpload
from ZODB.POSException import ConflictError

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore import permissions

from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.Layer import DefaultLayerContainer
from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.interfaces.field import IField
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.interfaces.field import IFileField
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.interfaces.vocabulary import IVocabulary
from Products.Archetypes.exceptions import ObjectFieldException
from Products.Archetypes.exceptions import TextFieldException
from Products.Archetypes.exceptions import FileFieldException
from Products.Archetypes.exceptions import ReferenceException
from Products.Archetypes.generator import i18n
from Products.Archetypes.Widget import BooleanWidget
from Products.Archetypes.Widget import CalendarWidget
from Products.Archetypes.Widget import ComputedWidget
from Products.Archetypes.Widget import DecimalWidget
from Products.Archetypes.Widget import FileWidget
from Products.Archetypes.Widget import ImageWidget
from Products.Archetypes.Widget import IntegerWidget
from Products.Archetypes.Widget import LinesWidget
from Products.Archetypes.Widget import StringWidget
from Products.Archetypes.Widget import ReferenceWidget
from Products.Archetypes.BaseUnit import BaseUnit
from Products.Archetypes.ReferenceEngine import Reference
from Products.Archetypes.utils import DisplayList
from Products.Archetypes.utils import Vocabulary
from Products.Archetypes.utils import className
from Products.Archetypes.utils import mapply
from Products.Archetypes.utils import shasattr
from Products.Archetypes.utils import contentDispositionHeader
from Products.Archetypes.debug import log
from Products.Archetypes.debug import log_exc
from Products.Archetypes.debug import deprecated
from Products.Archetypes import config
from Products.Archetypes.Storage import AttributeStorage
from Products.Archetypes.Storage import ObjectManagedStorage
from Products.Archetypes.Storage import ReadOnlyStorage
from Products.Archetypes.Registry import setSecurity
from Products.Archetypes.Registry import registerField
from Products.Archetypes.Registry import registerPropertyType

from Products.validation import ValidationChain
from Products.validation import UnknowValidatorError
from Products.validation import FalseValidatorError
from Products.validation.interfaces.IValidator import IValidator, IValidationChain


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

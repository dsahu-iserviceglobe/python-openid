

from openid.message import registerNamespaceAlias, \
     NamespaceAliasRegistrationError
from openid.extension import Extension
from openid import oidutil

try:
    basestring #pylint:disable-msg=W0104
except NameError:
    # For Python 2.2
    basestring = (str, unicode) #pylint:disable-msg=W0622

ns_uri = "http://specs.openid.net/extensions/oauth/1.0"
#
try:
    registerNamespaceAlias(ns_uri, 'oauth')
except NamespaceAliasRegistrationError, e:
    oidutil.log('registerNamespaceAlias(%r, %r) failed: %s' % (ns_uri,
                                                               'oauth', str(e),))


class OAuthRequest(Extension):

    ns_alias = 'oauth'

    def __init__(self, consumer=None, scope=None, oauth_ns_uri=ns_uri):
        Extension.__init__(self)
        self.consumer = consumer
        self.scope = scope
        self.ns_uri = oauth_ns_uri


    def fromOpenIDRequest(cls, request):
        self = cls()

        args = request.message.getArgs(self.ns_uri)
        self.parseExtensionArgs(args)

        return self

    fromOpenIDRequest = classmethod(fromOpenIDRequest)

    def parseExtensionArgs(self, args, strict=False):
        
        self.consumer = args['consumer']
        self.scope = args['scope']


    def getExtensionArgs(self):
        args = {}

        if self.consumer:
            args['consumer'] = self.consumer

        if self.scope:
            args['scope'] = self.scope

        return args

class OAuthResponse(Extension):

    ns_alias = 'oauth'

    def __init__(self, request_token=None, scope=None):
        Extension.__init__(self)
        self.ns_uri = ns_uri
        self.request_token = request_token
        self.scope = scope


    def fromSuccessResponse(cls, success_response, signed_only=True):
        self = cls()
        if signed_only:
            args = success_response.getSignedNS(ns_uri)
        else:
            args = success_response.message.getArgs(ns_uri)

        if not args:
            return None

        self.request_token = args['request_token']
        self.scope = args['scope']

        return self

    fromSuccessResponse = classmethod(fromSuccessResponse)

    def getExtensionArgs(self):
        args = {}

        if self.consumer:
            args['consumer'] = self.consumer

        if self.scope:
            args['scope'] = self.scope

        return args


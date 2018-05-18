# vim: set fileencoding=UTF-8 :
import logging
from spyne import Application, rpc, ServiceBase, Iterable, Integer, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
from instana.wsgi import iWSGIMiddleware

# Simple in test suite SOAP server to test suds client instrumentation against.
# Configured to listen on localhost port 4132
# WSDL: http://localhost:4232/?wsdl

class StanSoapService(ServiceBase):
    @rpc(Unicode, Integer, _returns=Iterable(Unicode))
    def ask_question(ctx, question, answer):
        """Ask Stan a question!
        <b>Ask Stan questions as a Service</b>

        @param name the name to say hello to
        @param times the number of times to say hello
        @return the completed array
        """

        yield u'To an artificial mind, all reality is virtual. How do they know that the real world isn\'t just another simulation? How do you?'


app = Application([StanSoapService], 'instana.tests.app.ask_question',
                  in_protocol=Soap11(validator='lxml'), out_protocol=Soap11())

# Use Instana middleware so we can test context passing and Soap server traces.
wsgi_app = iWSGIMiddleware(WsgiApplication(app))
soapserver = make_server('127.0.0.1', 4132, wsgi_app)

logging.basicConfig(level=logging.WARN)
logging.getLogger('suds').setLevel(logging.WARN)
logging.getLogger('suds.resolver').setLevel(logging.WARN)
logging.getLogger('spyne.protocol.xml').setLevel(logging.WARN)
logging.getLogger('spyne.model.complex').setLevel(logging.WARN)

if __name__ == '__main__':
    soapserver.serve_forever()

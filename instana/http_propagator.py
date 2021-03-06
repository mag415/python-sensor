from __future__ import absolute_import
import opentracing as ot
from basictracer.context import SpanContext
from instana import util, log


# The carrier can be a dict or a list.
# Using the trace header as an example, it can be in the following forms
# for extraction:
#   X-Instana-T
#   HTTP_X_INSTANA_T
#
# The second form above is found in places like Django middleware for
# incoming requests.
#
# For injection, we only support the standard format:
#   X-Instana-T


class HTTPPropagator():
    """A Propagator for Format.HTTP_HEADERS. """

    HEADER_KEY_T = 'X-Instana-T'
    HEADER_KEY_S = 'X-Instana-S'
    HEADER_KEY_L = 'X-Instana-L'
    ALT_HEADER_KEY_T = 'HTTP_X_INSTANA_T'
    ALT_HEADER_KEY_S = 'HTTP_X_INSTANA_S'
    ALT_HEADER_KEY_L = 'HTTP_X_INSTANA_L'
    GRPC_SAFE_HEADER_KEY_T = 'x-instana-t'
    GRPC_SAFE_HEADER_KEY_S = 'x-instana-s'
    GRPC_SAFE_HEADER_KEY_L = 'x-instana-l'
    
    def __init__(self, use_grpc_safe_headers):
        if(use_grpc_safe_headers):
            self.header_key_t = self.GRPC_SAFE_HEADER_KEY_T
            self.header_key_s = self.GRPC_SAFE_HEADER_KEY_S
            self.header_key_l = self.GRPC_SAFE_HEADER_KEY_L
        else:
            self.header_key_t = self.HEADER_KEY_T
            self.header_key_s = self.HEADER_KEY_S
            self.header_key_l = self.HEADER_KEY_L

    def inject(self, span_context, carrier):
        try:
            trace_id = util.id_to_header(span_context.trace_id)
            span_id = util.id_to_header(span_context.span_id)

            if type(carrier) is dict or hasattr(carrier, "__dict__"):
                carrier[self.header_key_t] = trace_id
                carrier[self.header_key_s] = span_id
                carrier[self.header_key_l] = "1"
            elif type(carrier) is list:
                carrier.append((self.header_key_t, trace_id))
                carrier.append((self.header_key_s, span_id))
                carrier.append((self.header_key_l, "1"))
            else:
                raise Exception("Unsupported carrier type", type(carrier))

        except Exception as e:
            log.debug("inject error: ", str(e))

    def extract(self, carrier):  # noqa
        try:
            if type(carrier) is dict or hasattr(carrier, "__dict__"):
                dc = carrier
            elif type(carrier) is list:
                dc = dict(carrier)
            else:
                raise ot.SpanContextCorruptedException()

            # Look for standard X-Instana-T/S format
            if self.HEADER_KEY_T in dc and self.header_key_s in dc:
                trace_id = util.header_to_id(dc[self.HEADER_KEY_T])
                span_id = util.header_to_id(dc[self.HEADER_KEY_S])

            # Check for alternate HTTP_X_INSTANA_T/S style
            elif self.ALT_HEADER_KEY_T in dc and self.ALT_HEADER_KEY_S in dc:
                trace_id = util.header_to_id(dc[self.ALT_HEADER_KEY_T])
                span_id = util.header_to_id(dc[self.ALT_HEADER_KEY_S])

            # Check for GRPC safe x-instana-t/s style
            elif self.GRPC_SAFE_HEADER_KEY_T in dc and self.GRPC_SAFE_HEADER_KEY_S in dc:
                trace_id = util.header_to_id(dc[self.GRPC_SAFE_HEADER_KEY_T])
                span_id = util.header_to_id(dc[self.GRPC_SAFE_HEADER_KEY_S])

            return SpanContext(span_id=span_id,
                               trace_id=trace_id,
                               baggage={},
                               sampled=True)

        except Exception as e:
            log.debug("extract error: ", str(e))

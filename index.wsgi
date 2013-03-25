import sae
from techparty import wsgi

application = sae.create_wsgi_app(wsgi.application)

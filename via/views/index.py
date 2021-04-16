from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults


@view_defaults(route_name="index")
class IndexViews:
    def __init__(self, request):
        self.request = request

    @staticmethod
    @view_config(request_method="GET", renderer="via:templates/index.html.jinja2")
    def get():
        return {}

    @view_config(request_method="POST")
    def post(self):
        return HTTPFound(
            self.request.route_url(
                route_name="proxy", url=self.request.params.get("url", "")
            )
        )

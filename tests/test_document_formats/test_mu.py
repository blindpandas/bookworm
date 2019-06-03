import pytest
from werkzeug.exceptions import NotFound
from oy import page_url
from oy.models.page import Page
from oy.views import ContentView
from oy.wrappers import OyModule


class CustomePageView(ContentView):
    def serve(self):
        return self.page.title


def test_view_basic(app, client, db, makemodel):
    custpagemod = OyModule("custpagemod", __name__, template_folder="templates")
    app.register_module(custpagemod)

    idcol = db.Column(db.Integer, db.ForeignKey(Page.id), primary_key=True)
    contype = "custom_page"
    CustomPage = makemodel(
        "CustomePage", (Page,), d={"id": idcol, "__contenttype__": contype}
    )

    cust = CustomPage(title="Hello", author_id=1)
    db.session.add(cust)
    db.session.commit()
    resp = client.get(page_url(cust), status=404)
    app.add_contenttype_handler("custom_page", CustomePageView)
    resp = client.get(page_url(cust))
    assert resp.status == "200 OK"
    assert "Hello" in resp.text

    class CustomPageResponseMiddleware:
        def process_response(self, response):
            assert response == "Hello"
            return "Custom"

    app.apply_middleware("custom_page", CustomPageResponseMiddleware)
    resp = client.get(page_url(cust))
    assert resp.status == "200 OK"
    assert "Custom" in resp.text

    class TemplatedCustomPageView(ContentView):
        """A view that render templates."""

    class CustomPageTemplateMiddleware:
        def process_context(self, context):
            return context

        def process_template(self, templates):
            assert all(
                [
                    t in templates
                    for t in (
                        "custom_page/hello.html",
                        "custom_page/custom_page.html",
                        "custom_page/page.html",
                    )
                ]
            )
            return "custom_page/cust_page.html"

    # Replace the first view
    app.add_contenttype_handler(contenttype="custom_page", view=TemplatedCustomPageView)
    app.apply_middleware("custom_page", CustomPageTemplateMiddleware)
    thismw = app.contenttype_handlers["custom_page"].middlewares
    assert thismw["process_template"][0] is thismw["process_context"][0]
    resp = client.get(page_url(cust))
    assert "from custome page template" in resp.text

    @app.before_page_request
    def custom_bfpr():
        return "That's it"

    resp = client.get(page_url(cust))
    assert "That's it" in resp.text


def testmodfunctionality(app, db, client, makemodel):
    idcol = db.Column(db.Integer, db.ForeignKey(Page.id), primary_key=True)
    contype = "newcustom_page"
    CustomPage = makemodel(
        "NewCustomePage", (Page,), d={"id": idcol, "__contenttype__": contype}
    )
    cust = CustomPage(title="Hello", author_id=1)
    db.session.add(cust)
    db.session.commit()

    newmod = OyModule("newmod", __name__)

    @newmod.contenttype_handler("newcustom_page")
    def newmod_conhand():
        return "From custom module"

    app.register_module(newmod)
    resp = client.get(page_url(cust))
    assert "From custom module" in resp.text

    def nohandlerargnewcustmw(response):
        assert "From custom module" in response
        return "Applied first middleware"

    app.apply_middleware("newcustom_page", nohandlerargnewcustmw)
    resp = client.get(page_url(cust))
    assert "Applied first middleware" in resp.text

# coding: utf-8

from bookworm import config
from bookworm.signals import app_shuttingdown
from bookworm.logger import logger

log = logger.getChild(__name__)
BUILTIN_SERVICES = {}

class ServiceHandler:
    """A singleton to manage services."""
    registered_services = set()

    def __init__(self, view):
        self.view = view
        self.reader = view.reader
        app_shuttingdown.connect(self.on_shutdown, weak=False)

    def register_service(self, service_cls):
        if service_cls.check():
            service = service_cls(self.view, self.reader)
            key, specs = service.get_config_spec()
            config.conf.spec[key] = specs
            config.save()
            self.registered_services.add(service)
        else:
            log.error(f"Service {service_cls.name} `check` returned `False`")

    def on_shutdown(self, sender):
        for service in self.registered_services:
            service.shutdown()

    def get_settings_panels(self):
        rv = set()
        for service in self.registered_services:
            rv.update(service.gui.get_settings_panels())
        return rv

    def process_menubar(self, menu):
        for service in self.registered_services:
            service.gui.add_main_menu()

    def get_contextmenu_items(self):
        rv = set()
        for service in self.registered_services:
            rv.update(service.gui.get_contextmenu())
        return rv

    def get_toolbar_items(self):
        rv = set()
        for service in self.registered_services:
            rv.update(service.gui.get_toolbar_items())
        return rv


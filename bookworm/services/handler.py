# coding: utf-8

from bookworm import config
from bookworm.signals import app_shuttingdown
from bookworm.logger import logger
from .cont_reading import ContReadingService
from .text_to_speech import TextToSpeechService

log = logger.getChild(__name__)
BUILTIN_SERVICES = {ContReadingService,TextToSpeechService}

class ServiceHandler:
    """A singleton to manage services."""
    registered_services = set()

    def __init__(self, view):
        self.view = view
        app_shuttingdown.connect(self.on_shutdown, weak=False)

    def register_builtin_services(self):
        log.info("Registering services.")
        for service_cls in BUILTIN_SERVICES:
            log.info(f"Registering service: {service_cls.name}.")
            self.register_service(service_cls)

    def get_services_with_gui(self):
        return filter(lambda s: s.has_gui, self.registered_services)

    def register_service(self, service_cls):
        if service_cls.check():
            service = service_cls(self.view)
            config.conf.spec.update(service.config_spec)
            config.conf.validate_and_write()
            self.registered_services.add(service)
        else:
            log.error(f"Service {service_cls.name} `check` returned `False`")

    def on_shutdown(self, sender):
        for service in self.registered_services:
            service.shutdown()

    def get_settings_panels(self):
        rv = set()
        for service in self.get_services_with_gui():
            rv.update(service.get_settings_panels())
        return rv

    def process_menubar(self, menubar):
        for service in self.get_services_with_gui():
            service.process_menubar(menubar)

    def get_contextmenu_items(self):
        rv = set()
        for service in self.get_services_with_gui():
            rv.update(service.get_contextmenu())
        return rv

    def get_toolbar_items(self):
        rv = set()
        for service in self.get_services_with_gui():
            rv.update(service.get_toolbar_items())
        return rv

    def get_keyboard_shourtcuts(self):
        rv = {}
        for service in self.get_services_with_gui():
            rv.update(service.get_keyboard_shourtcuts())
        return rv


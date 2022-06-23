# coding: utf-8

from bookworm import app
from bookworm import config
from bookworm.signals import app_shuttingdown
from bookworm.logger import logger


log = logger.getChild(__name__)


# Builtin services
from bookworm.otau import OTAUService
from bookworm.annotation import AnnotationService
from bookworm.ocr import OCRSettingsService, OCRService
from bookworm.text_to_speech import TextToSpeechService
from bookworm.continuous_reading import ContReadingService
from bookworm.bookshelf import BookshelfService
from bookworm.epub_serve import EpubServeService
from bookworm.webservices import (
    WebservicesBaseService,
    WikipediaService,
    UrlOpenService,
)

BUILTIN_SERVICES = (
    OTAUService,
    TextToSpeechService,
    AnnotationService,
    WebservicesBaseService,
    OCRSettingsService,
    OCRService,
    BookshelfService,
    ContReadingService,
    UrlOpenService,
    WikipediaService,
    EpubServeService,
)


class ServiceHandler:
    """A singleton to manage services."""

    registered_services = []

    def __init__(self, view):
        self.view = view
        app_shuttingdown.connect(self.on_shutdown, weak=False)

    def register_builtin_services(self):
        log.info("Registering services.")
        for service_cls in BUILTIN_SERVICES:
            self.register_service(service_cls)

    def _get_services_with_gui(self):
        return filter(lambda s: s.has_gui, self.registered_services)

    def get_service(self, service_name):
        for service in self.registered_services:
            if service.name == service_name:
                return service

    def register_service(self, service_cls):
        log.info(f"Registering service: {service_cls.name}.")
        try:
            if service_cls.check():
                service = service_cls(self.view)
                if service.config_spec is not None:
                    config.conf.spec.update(service.config_spec)
                    config.conf.validate_and_write()
                self.registered_services.insert(0, service)
            else:
                log.error(f"Service {service_cls.name} `check` returned `False`")
        except Exception as e:
            log.exception(f"Exception registering service {service_cls.name}: {e}")
            if app.debug:
                raise e

    def on_shutdown(self, sender):
        for service in self.registered_services:
            service.shutdown()

    def get_settings_panels(self):
        rv = set()
        for service in self._get_services_with_gui():
            rv.update(service.get_settings_panels())
        return rv

    def process_menubar(self, menubar):
        for service in self._get_services_with_gui():
            yield service.process_menubar(menubar)

    def get_toolbar_items(self):
        rv = set()
        for service in self._get_services_with_gui():
            rv.update(service.get_toolbar_items())
        return rv

    def get_contextmenu_items(self):
        rv = set()
        for service in self._get_services_with_gui():
            rv.update(service.get_contextmenu_items())
        return rv

    def get_stateful_menu_ids(self):
        rv = set()
        for service in self._get_services_with_gui():
            rv.update(service.stateful_menu_ids or ())
        return rv

    def get_keyboard_shortcuts(self):
        rv = {}
        for service in self._get_services_with_gui():
            rv.update(service.get_keyboard_shortcuts())
        return rv

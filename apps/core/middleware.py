"""Project middleware."""

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import translation


class AdminLanguageMiddleware:
    """
    Always show the admin in `ADMIN_LANGUAGE_CODE`, whatever the browser asks for.

    Must follow `LocaleMiddleware`, which picks the language for the public API.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.admin_prefix = "/" + settings.ADMIN_URL.lstrip("/")
        self.language = getattr(settings, "ADMIN_LANGUAGE_CODE", settings.LANGUAGE_CODE)

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path_info.startswith(self.admin_prefix):
            translation.activate(self.language)
            request.LANGUAGE_CODE = self.language
        return self.get_response(request)

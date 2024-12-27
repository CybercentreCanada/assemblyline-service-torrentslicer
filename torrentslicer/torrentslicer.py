"""Extracts information from torrent files with the help of `bencode`."""

from assemblyline.common import forge
from assemblyline_v4_service.common.base import ServiceBase
from assemblyline_v4_service.common.request import ServiceRequest
from assemblyline_v4_service.common.result import Result


class Torrentslicer(ServiceBase):
    """Extracts information from torrent files with the help of `bencode`."""

    def execute(self, request: ServiceRequest):
        """Run the service."""

        result = Result()
        request.result = result

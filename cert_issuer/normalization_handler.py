import json
import os
from cert_schema import normalize_jsonld, extend_preloaded_context

from cert_issuer.config import CONFIG


class JSONLDHandler:
    @staticmethod
    def normalize_to_utf8(certificate_json):
        JSONLDHandler.preload_contexts()
        normalized = normalize_jsonld(certificate_json, detect_unmapped_fields=False)
        return normalized.encode('utf-8')

    @staticmethod
    def preload_contexts():
        print(CONFIG.context_urls, CONFIG.context_file_paths, os.getcwd())
        with open(os.path.join(os.getcwd(), CONFIG.context_file_paths)) as context_file:
            context_data = json.load(context_file)
            print(context_data)
            extend_preloaded_context(CONFIG.context_urls, context_data)

import mimetypes
import os
from io import BytesIO

from django.conf import settings
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    def __init__(self):
        from supabase import create_client
        self._client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        self._bucket = settings.SUPABASE_BUCKET

    def _open(self, name, mode='rb'):
        data = self._client.storage.from_(self._bucket).download(name)
        return BytesIO(data)

    def _save(self, name, content):
        content.seek(0)
        data = content.read()
        content_type, _ = mimetypes.guess_type(name)
        self._client.storage.from_(self._bucket).upload(
            path=name,
            file=data,
            file_options={
                "content-type": content_type or "application/octet-stream",
                "upsert": "true",
            },
        )
        return name

    def exists(self, name):
        # Always False: upsert handles overwrites, avoids Django appending _1, _2 suffixes
        return False

    def url(self, name):
        return self._client.storage.from_(self._bucket).get_public_url(name)

    def delete(self, name):
        try:
            self._client.storage.from_(self._bucket).remove([name])
        except Exception:
            pass

    def size(self, name):
        folder = os.path.dirname(name)
        filename = os.path.basename(name)
        try:
            files = self._client.storage.from_(self._bucket).list(folder)
            for f in files or []:
                if f["name"] == filename:
                    return f.get("metadata", {}).get("size", 0)
        except Exception:
            pass
        return 0

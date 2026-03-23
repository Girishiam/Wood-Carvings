"""
Dropbox service: downloads reference images from a shared folder,
extracts them in-memory, and caches them for the session lifetime.
Re-downloading only happens on explicit cache clear or new link.
"""

import httpx
import io
import zipfile
import base64
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class DropboxService:
    def __init__(self):
        # In-memory cache: { dropbox_link: [{"b64": str, "mime": str, "name": str}] }
        self._cache: dict[str, list[dict]] = {}

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def get_reference_images(
        self, shared_link: str, force_refresh: bool = False
    ) -> list[dict]:
        """
        Return a list of reference images as base64 dicts.
        Uses in-memory cache to avoid repeated Dropbox downloads.
        Each item: {"b64": str, "mime": str, "name": str}
        """
        cache_key = self._normalize_link(shared_link)

        if not force_refresh and cache_key in self._cache:
            logger.info(f"[Dropbox] Cache hit — {len(self._cache[cache_key])} images")
            return self._cache[cache_key]

        logger.info("[Dropbox] Downloading reference folder …")
        zip_buffer = await self._download_zip(cache_key)
        images = self._extract_images(zip_buffer)

        if not images:
            logger.warning("[Dropbox] No supported images found in zip")
        else:
            logger.info(f"[Dropbox] Extracted {len(images)} images, caching")
            self._cache[cache_key] = images

        return images

    def clear_cache(self, shared_link: str | None = None) -> None:
        """Clear cache for a specific link, or all cached links."""
        if shared_link:
            self._cache.pop(self._normalize_link(shared_link), None)
        else:
            self._cache.clear()
        logger.info("[Dropbox] Cache cleared")

    def cache_status(self, shared_link: str) -> dict:
        key = self._normalize_link(shared_link)
        cached = key in self._cache
        return {
            "cached": cached,
            "image_count": len(self._cache.get(key, [])),
            "dropbox_link": shared_link if cached else None,
        }

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _normalize_link(link: str) -> str:
        """Normalize link for use as a cache key (base URL only)."""
        return link.split("?")[0]

    @staticmethod
    async def _download_zip(download_url: str) -> io.BytesIO:
        """
        Download Dropbox folder as zip.
        Preserves the rlkey param (needed for secure folder access) but forces dl=1.
        """
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(download_url)
        params = parse_qs(parsed.query, keep_blank_values=True)
        # Keep only rlkey (authentication token) and force dl=1
        clean_params = {}
        if 'rlkey' in params:
            clean_params['rlkey'] = params['rlkey'][0]
        if 'st' in params:
            clean_params['st'] = params['st'][0]
        clean_params['dl'] = '1'
        new_query = urlencode(clean_params)
        url = urlunparse(parsed._replace(query=new_query))
        logger.info(f"[Dropbox] Download URL: {url[:80]}...")
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
        return io.BytesIO(response.content)

    @staticmethod
    def _extract_images(zip_buffer: io.BytesIO) -> list[dict]:
        """Extract image files from zip, return base64-encoded list."""
        images = []
        with zipfile.ZipFile(zip_buffer) as z:
            for name in z.namelist():
                ext = Path(name).suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    continue
                # Skip macOS metadata files
                if "__MACOSX" in name or name.startswith("."):
                    continue
                data = z.read(name)
                mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else f"image/{ext[1:]}"
                images.append({
                    "b64": base64.b64encode(data).decode("utf-8"),
                    "mime": mime,
                    "name": Path(name).name,
                })
        return images
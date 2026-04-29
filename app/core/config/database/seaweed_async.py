# app.core.config.database.seaweed_async.py
import aiohttp
from fastapi import HTTPException
from typing import Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential


class SeaweedFSManager:
    def __init__(self, master_url: str):
        self.master_url = master_url.rstrip('/')
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache = {}

    async def start(self):
        if not self._session:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                raise_for_status=True  # Упрощает проверку статусов (бросает исключение сам)
            )

    async def stop(self):
        if self._session:
            await self._session.close()

    def _format_url(self, url: str) -> str:
        return f"http://{url}" if not url.startswith('http') else url

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(0.5))
    async def assign(self) -> Tuple[str, str]:
        async with self._session.get(f"{self.master_url}/dir/assign") as r:
            data = await r.json()
            return data["fid"], self._format_url(data["url"])

    async def upload(self, file_data: bytes) -> str:
        fid, vol_url = await self.assign()
        async with self._session.post(f"{vol_url}/{fid}", data=file_data):
            return fid

    async def get_url(self, fid: str) -> str:
        vid = fid.split(",")[0]
        if vid not in self._cache:
            async with self._session.get(f"{self.master_url}/dir/lookup?volumeId={vid}") as r:
                locs = (await r.json()).get("locations")
                if not locs:
                    raise RuntimeError(f"Volume {vid} not found")
                self._cache[vid] = self._format_url(locs[0]["url"])
        return f"{self._cache[vid]}/{fid}"

    async def download(self, fid: str) -> bytes:
        url = await self.get_url(fid)
        async with self._session.get(url) as r:
            return await r.read()

    async def delete(self, fid: str):
        url = await self.get_url(fid)
        async with self._session.delete(url):
            return True

    async def get_public_url(self, fid: str, internal: bool = False) -> str:
        """
        Возвращает прямую ссылку на файл.
        internal=True — для доступа внутри сети (Docker/K8s)
        internal=False — для внешних пользователей (если настроены пробросы портов)
        """
        vid = fid.split(",")[0]
        # Используем существующую логику получения URL из кэша или через lookup
        base_url = await self._get_volume_base_url(vid)
        return f"{base_url}/{fid}"


_manager: Optional[SeaweedFSManager] = None


async def init_seaweed(master_url: str):
    global _manager
    _manager = SeaweedFSManager(master_url)
    await _manager.start()


async def close_seaweed():
    if _manager:
        await _manager.stop()

# 3. Та самая Dependency Injection


def get_swfs() -> SeaweedFSManager:
    if _manager is None:
        raise HTTPException(status_code=500, detail="SeaweedFS not initialized")
    return _manager

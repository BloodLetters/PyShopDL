import aiohttp


class Metadata:
    BASE_URL = "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/"

    async def on_process(self, workshop_id: str) -> None:
        """Hook sebelum proses fetch dimulai."""
        pass

    async def on_finish(self, workshop_id: str, details: dict) -> None:
        """Hook setelah proses fetch selesai."""
        pass

    async def _fetch(self, workshop_id: str) -> dict:
        await self.on_process(workshop_id)

        data = {
            "itemcount": 1,
            "publishedfileids[0]": workshop_id,
        }

        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.BASE_URL, data=data) as response:
                response.raise_for_status()
                result = await response.json()

        try:
            details = result["response"]["publishedfiledetails"][0]
        except (KeyError, IndexError):
            raise Exception("Invalid response structure")

        if details.get("result") != 1:
            raise Exception(f"Error fetching details: {details.get('result')}")

        await self.on_finish(workshop_id, details)
        return details

    async def get(self, workshop_id: str) -> dict:
        return await self._fetch(workshop_id)

    async def getData(self, workshop_id: str) -> tuple[str, str, str]:
        details = await self.get(workshop_id)

        size_bytes = float(details.get("file_size", 0))
        size_mb = size_bytes / (1024 * 1024)
        size_text = f"{size_mb:.1f}MB"

        name_text = details.get("title", "")
        app_id_value = details.get("consumer_app_id", "")
        app_id_text = str(app_id_value) if app_id_value not in (None, "") else ""

        return name_text, size_text, app_id_text
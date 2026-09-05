import httpx


class GoOutClient:
    BASE_URL = "https://goout.net/services/entities/v1/schedules"

    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    async def get_venue_schedules(self, venue_id: int, limit: int = 100) -> dict:
        params = [
            ("languages[]", "cs"),
            ("venueIds[]", str(venue_id)),
            ("grouped", "true"),
            ("limit", str(limit)),
            ("include", "events,images,venues,cities,sales,performers,parents"),
        ]
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, http2=True) as client:
            response = await client.get(self.BASE_URL, params=params, headers={"Accept": "application/json"})
            response.raise_for_status()
            return response.json()

# -*- coding: utf-8 -*-
import sys
from random import uniform
from time import sleep, strftime
from typing import Any, Dict, Optional, Union

from aiohttp import ClientSession
from rich.console import Console


def get_time() -> str:
    return f"{strftime('%Y-%m-%d %H:%M:%S')} | "


class VBitve:
    def __init__(
        self,
        console: Console,
        session: ClientSession,
        vk_auth: str,
        friends_header: str,
        user_agent: str,
        min_delay: float,
        max_delay: float,
    ) -> None:
        """
        vk_auth (str): vk_access_token_settings...
        user_agent (str): User agent браузера.
        min_delay (float): Мин. задержка между одинаковыми запросами в
            секундах.
        max_delay (float): Макс. задержка между одинаковыми запросами в
            секундах.
        """
        self._c = console
        self._s = session
        self._headers = {
            "friends": str(friends_header),
            "origin": "https://prod-app7801617-8a6f43695867.pages-ac.vk-apps.com",
            "referer": "https://prod-app7801617-8a6f43695867.pages-ac.vk-apps.com/",
            "user-agent": user_agent.strip(),
            "vk-auth": vk_auth.strip(),
        }
        self._MIN_DELAY = min_delay
        self._MAX_DELAY = max_delay

    async def get(self) -> Dict[str, Any]:
        return await self._req("get", json={"to": ""})

    async def privacy(self, hidden: str) -> Dict[str, Any]:
        """hidden: 0 или 1."""
        return await self._req("privacy", params={"hidden": hidden})

    async def contract(self) -> Dict[str, Any]:
        return await self._req("contract")

    async def attack(self, user_id: int) -> Dict[str, Any]:
        return await self._req("attack", json={"to": user_id})

    async def for_me(self) -> Dict[str, Any]:
        return await self._req("for_me")

    async def rating(self) -> Dict[str, Any]:
        return await self._req("rating")

    async def train(self) -> Dict[str, Any]:
        return await self._req("train")

    async def _req(
        self,
        endpoint: str,
        *,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Union[str, int]]] = None,
    ) -> Dict[str, Any]:
        try:
            async with self._s.request(
                "GET" if json is None else "POST",
                f"https://www.inbattle.space/{endpoint}",
                headers=self._headers,
                params=params,
                json=json,
            ) as req:
                r: Dict[str, Any] = await req.json()
        except Exception as e:
            self._c.print(f"{get_time()}[red]{endpoint}: {e}[/red]")
            sleep(uniform(self._MIN_DELAY, self._MAX_DELAY))
            return await self._req(endpoint, params=params, json=json)
        if "banned" in r:
            self._c.print(f"{get_time()}[red]Banned[/red]")
            sys.exit()
        error = r.get("error")
        if error is None:
            return r
        self._c.print(f"{get_time()}[red]{endpoint}: {error}[/red]")
        return {}

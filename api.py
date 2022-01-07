# -*- coding: utf-8 -*-
import sys
from random import uniform
from time import sleep, strftime, time
from typing import Any, Dict, Optional, Union

from requests import Session
from rich.console import Console


class Logger:
    def __init__(self, console: Console) -> None:
        self._c = console

    def print(self, *objects: Any) -> None:
        self._c.print(f"{strftime('%Y-%m-%d %H:%M:%S')} | ", *objects)


class VBitve:
    def __init__(
        self,
        session: Session,
        vk_auth: str,
        friends_header: str,
        user_agent: str,
        min_delay: float,
        max_delay: float,
        console: Optional[Console] = None,
    ) -> None:
        """
        vk_auth (str): vk_access_token_settings...
        user_agent (str): User agent браузера.
        min_delay (float): Мин. задержка между запросами в секундах.
        max_delay (float): Макс. задержка между запросами в секундах.
        """
        self.console = console or Console()
        self.logger = Logger(self.console)
        self._s = session
        origin = "https://prod-app7801617-8a6f43695867.pages-ac.vk-apps.com"
        self._headers = {
            "friends": str(friends_header),
            "origin": origin,
            "referer": f"{origin}/",
            "user-agent": user_agent.strip(),
            "vk-auth": vk_auth.strip(),
        }
        self._MIN_DELAY = min_delay
        self._MAX_DELAY = max_delay
        self._last_req_time: float = 0

    def get(self) -> Dict[str, Any]:
        return self._req("get", json={"to": ""})

    def privacy(self, hidden: str) -> Dict[str, Any]:
        """hidden: 0 или 1."""
        return self._req("privacy", params={"hidden": hidden})

    def contract(self) -> Dict[str, Any]:
        return self._req("contract")

    def attack(self, user_id: int) -> Dict[str, Any]:
        return self._req("attack", json={"to": user_id})

    def for_me(self) -> Dict[str, Any]:
        return self._req("for_me")

    def rating(self) -> Dict[str, Any]:
        return self._req("rating")

    def train(self) -> Dict[str, Any]:
        return self._req("train")

    def clan_me(self) -> Dict[str, Any]:
        return self._req("clan", params={"me": "1"})

    def clan(self, clan_id: str) -> Dict[str, Any]:
        return self._req("clan", params={"clan": clan_id})

    def _req(
        self,
        endpoint: str,
        *,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Union[str, int]]] = None,
    ) -> Dict[str, Any]:
        cur_time = time()
        to_sleep = (
            self._last_req_time
            + uniform(self._MIN_DELAY, self._MAX_DELAY)
            - cur_time
        )
        self._last_req_time = cur_time
        if to_sleep > 0:
            self._last_req_time += to_sleep
            sleep(to_sleep)
        try:
            with self._s.request(
                "GET" if json is None else "POST",
                f"https://www.inbattle.space/{endpoint}",
                headers=self._headers,
                params=params,
                json=json,
            ) as req:
                r: Dict[str, Any] = req.json()
        except Exception as e:
            self.logger.print(f"[red]{endpoint}: {e}")
            return self._req(endpoint, params=params, json=json)
        if "banned" in r:
            self.logger.print("[red]Banned")
            sys.exit()
        error = r.get("error")
        if error is None:
            return r
        self.logger.print(f"[red]{endpoint}: {error}")
        return {}

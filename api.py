# -*- coding: utf-8 -*-
import sys
from random import uniform
from time import sleep, strftime, time
from typing import Any, Dict, Optional, Union

from requests import Session
from rich.console import Console


class IncorrectToken(Exception):
    """Неверный токен."""


class IncorrectTokenType(Exception):
    """Токен неверного типа. Нужен VK Admin токен."""


class Logger:
    def __init__(self, console: Console) -> None:
        self._c = console

    def print(self, *objects: Any) -> None:
        self._c.print(f"{strftime('%Y-%m-%d %H:%M:%S')} | ", *objects)


class VBitve:
    def __init__(
        self,
        session: Session,
        vk_admin_token: str,
        vk_auth_header: str,
        friends_header: str,
        user_agent: str,
        console: Optional[Console] = None,
    ) -> None:
        """
        vk_admin_token (str): VK Admin токен с vkhost.github.io.
        vk_auth_header (str): vk_access_token_settings...
        user_agent (str): User agent браузера.
        """
        self._s = session
        with session.get(
            "https://api.vk.com/method/apps.get",
            params={
                "access_token": vk_admin_token.split("access_token=")[-1]
                .split("&expires_in")[0]
                .strip(),
                "v": "5.131",
                "app_id": "7801617",
                "platform": "web",
            },
        ) as res:
            r: Dict[str, Any] = res.json()
        response: Optional[Dict[str, Any]] = r.get("response")
        if not response:
            raise IncorrectToken("Неверный токен.")
        webview_url: Optional[str] = response["items"][0].get("webview_url")
        if not webview_url:
            raise IncorrectTokenType(
                "Токен неверного типа. Нужен VK Admin токен."
            )
        origin = webview_url.split("/index.html?")[0]
        self._headers = {
            "friends": str(friends_header),
            "origin": origin,
            "referer": f"{origin}/",
            "user-agent": user_agent.strip(),
            "vk-auth": vk_auth_header.strip(),
        }
        self.console = console or Console()
        self.logger = Logger(self.console)
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
        to_sleep = self._last_req_time + uniform(3, 5) - cur_time
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

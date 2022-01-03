#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from random import uniform
from time import time
from typing import Any, Dict, NoReturn

from aiohttp import ClientSession
from rich.console import Console
from rich.live import Live
from rich.table import Table

from api import VBitve, get_time
from config import (
    ATTACK,
    ATTACK_EXCLUDE,
    CONTRACT,
    FRIENDS_HEADER,
    MAX_DELAY,
    MIN_DELAY,
    TRAIN,
    USER_AGENT,
    VK_AUTH,
)


class Profile:
    def __init__(self, profile: Dict[str, Any]) -> None:
        self.update(profile)

    def update(self, profile: Dict[str, Any]) -> None:
        self.army_size = profile["army"]
        self.balance = profile["balance"]
        self.contract = profile["contract"]
        self.next_attack = profile.get("nextAttack", 0)
        self.next_contract = profile.get("nextContract", 0)
        self.next_train = profile.get("nextTrain", 0)
        self.power = profile["power"]
        self.train_cost = profile["trainCost"]


async def sleep_delay() -> None:
    await asyncio.sleep(uniform(MIN_DELAY, MAX_DELAY))


async def bot(
    client: VBitve, profile: Profile, console: Console, live: Live
) -> None:
    if ATTACK and profile.next_attack < time() * 1000:
        targets = await client.for_me()
        await sleep_delay()
        if targets:
            users = targets["items"]
            target = 0
            for user in users:
                target = user["id"]
                if target not in ATTACK_EXCLUDE:
                    break
            if target:
                attack = await client.attack(target)
                if attack:
                    profile.update(attack["new_user"])
                    text = attack["snackbar"]["text"].replace(
                        "Вы напали и украли:\n", "+"
                    )
                    console.print(f"{get_time()}Напал на {target}: {text}")
                await sleep_delay()
    cur_time = time() * 1000
    if (
        TRAIN
        and profile.balance >= profile.train_cost
        and profile.next_train < cur_time
    ):
        train = await client.train()
        if train:
            profile.update(train["new_user"])
            console.print(f"{get_time()}Тренирую армию -{profile.train_cost}$")
            live.update(get_table(profile), refresh=True)
        await sleep_delay()
    elif CONTRACT and profile.next_contract < cur_time:
        contract = await client.contract()
        if contract:
            profile.update(contract["new_user"])
            console.print(f"{get_time()}Беру контракт +{profile.contract}$")
            live.update(get_table(profile), refresh=True)
        await sleep_delay()
    time_to_wait = (
        int(
            min(
                profile.next_attack,
                max(profile.next_train, profile.next_contract),
            )
            / 1000
            - time()
        )
        + 1
    )
    console.print(
        get_time()
        + f"Жду {time_to_wait} секунд до окончания ближайшей перезарядки"
    )
    await asyncio.sleep(time_to_wait)


def get_table(profile: Profile) -> Table:
    table = Table(title="github.com/monosans/vk-vbitve-bot")
    for header, style in (
        ("Баланс", "cyan"),
        ("Размер армии", "magenta"),
        ("Сила армии", "green"),
    ):
        table.add_column(header, style=style)
    table.add_row(
        *map(str, (profile.balance, len(profile.army_size), profile.power))
    )
    return table


async def main() -> NoReturn:
    console = Console()
    async with ClientSession() as session:
        client = VBitve(
            console,
            session,
            VK_AUTH,
            FRIENDS_HEADER,
            USER_AGENT,
            MIN_DELAY,
            MAX_DELAY,
        )
        profile = Profile(await client.get())
        with Live(
            get_table(profile), console=console, auto_refresh=False
        ) as live:
            await sleep_delay()
            while True:
                await bot(client, profile, console, live)


if __name__ == "__main__":
    asyncio.run(main())

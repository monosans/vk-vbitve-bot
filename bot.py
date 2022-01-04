#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from random import uniform
from time import sleep, time
from typing import Any, Dict, List, NoReturn

from requests import Session
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
        self.army: List[Dict[str, Any]] = profile["army"]
        self.balance: int = profile["balance"]
        self.contract: int = profile["contract"]
        self.next_attack: int = profile.get("nextAttack", 0)
        self.next_contract: int = profile.get("nextContract", 0)
        self.next_train: int = profile.get("nextTrain", 0)
        self.power: int = profile["power"]
        self.train_cost: int = profile["trainCost"]
        self.cooldown = max(self.next_contract, self.next_train)
        self.full_cooldown = min(self.next_attack, self.cooldown)


def sleep_delay() -> None:
    sleep(uniform(MIN_DELAY, MAX_DELAY))


def bot(
    client: VBitve, profile: Profile, console: Console, live: Live
) -> None:
    if ATTACK and profile.next_attack < time() * 1000:
        targets = client.for_me()
        sleep_delay()
        if targets:
            users = targets["items"]
            target = 0
            for user in users:
                target = user["id"]
                if target not in ATTACK_EXCLUDE:
                    break
            if target:
                attack = client.attack(target)
                if attack:
                    profile.update(attack["new_user"])
                    text = attack["snackbar"]["text"].replace(
                        "Вы напали и украли:\n", "+"
                    )
                    console.print(f"{get_time()}Напал на {target}: {text}")
                sleep_delay()
    if profile.cooldown < time() * 1000:
        if TRAIN and profile.balance >= profile.train_cost:
            train = client.train()
            if train:
                profile.update(train["new_user"])
                console.print(
                    f"{get_time()}Тренирую армию -{profile.train_cost}$"
                )
                live.update(get_table(profile), refresh=True)
            sleep_delay()
        elif CONTRACT:
            contract = client.contract()
            if contract:
                profile.update(contract["new_user"])
                console.print(
                    f"{get_time()}Беру контракт +{profile.contract}$"
                )
                live.update(get_table(profile), refresh=True)
            sleep_delay()
    time_to_wait = int(profile.full_cooldown / 1000 - time()) + 1
    if time_to_wait > 0:
        console.print(
            get_time()
            + f"Жду {time_to_wait} секунд до окончания ближайшей перезарядки"
        )
        sleep(time_to_wait)


def get_table(profile: Profile) -> Table:
    table = Table(title="github.com/monosans/vk-vbitve-bot v20210105")
    for header, style in (
        ("Баланс", "cyan"),
        ("Размер армии", "magenta"),
        ("Сила армии", "green"),
    ):
        table.add_column(header, style=style, justify="center")
    table.add_row(
        *map(str, (profile.balance, len(profile.army), profile.power))
    )
    return table


def main() -> NoReturn:
    console = Console()
    with Session() as session:
        client = VBitve(
            console,
            session,
            VK_AUTH,
            FRIENDS_HEADER,
            USER_AGENT,
            MIN_DELAY,
            MAX_DELAY,
        )
        profile = Profile(client.get())
        with Live(
            get_table(profile), console=console, auto_refresh=False
        ) as live:
            sleep_delay()
            while True:
                bot(client, profile, console, live)


if __name__ == "__main__":
    main()

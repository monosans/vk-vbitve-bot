#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from random import choice
from time import sleep, time
from typing import Any, Callable, Dict, List, NoReturn

from requests import Session
from rich.live import Live
from rich.table import Table

from api import VBitve
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


def bot(
    client: VBitve, profile: Profile, live: Live, log: Callable[[Any], None]
) -> None:
    if ATTACK and profile.next_attack < time() * 1000:
        targets = client.for_me()
        if targets:
            users = [
                user
                for user in targets["items"]
                if user["id"] not in ATTACK_EXCLUDE
            ]
            if users:
                target = choice(users)["id"]
                attack = client.attack(target)
                if attack:
                    profile.update(attack["new_user"])
                    text = attack["snackbar"]["text"].split("\n")[-1]
                    log(f"Напал на id{target}: +{text}")
    if profile.cooldown < time() * 1000:
        if TRAIN and profile.balance >= profile.train_cost:
            train = client.train()
            if train:
                profile.update(train["new_user"])
                log(f"Тренирую армию -{profile.train_cost}$")
                live.update(get_table(profile), refresh=True)
        elif CONTRACT:
            contract = client.contract()
            if contract:
                profile.update(contract["new_user"])
                log(f"Беру контракт +{profile.contract}$")
                live.update(get_table(profile), refresh=True)
    time_to_wait = int(profile.full_cooldown / 1000 - time()) + 1
    if time_to_wait > 0:
        log(f"Жду {time_to_wait} секунд до окончания перезарядки")
        sleep(time_to_wait)


def get_table(profile: Profile) -> Table:
    table = Table(title="github.com/monosans/vk-vbitve-bot v20210105.1")
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
    with Session() as session:
        client = VBitve(
            session, VK_AUTH, FRIENDS_HEADER, USER_AGENT, MIN_DELAY, MAX_DELAY
        )
        profile = Profile(client.get())
        with Live(
            get_table(profile), console=client.console, auto_refresh=False
        ) as live:
            log = client.logger.print
            while True:
                bot(client, profile, live, log)


if __name__ == "__main__":
    main()

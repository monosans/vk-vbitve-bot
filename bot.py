#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from random import choice
from time import sleep, time
from typing import Any, Callable, Dict, List, NoReturn

from requests import Session
from rich.live import Live
from rich.table import Column, Table

from api import VBitve
from config import (
    ATTACK,
    ATTACK_EXCLUDE,
    CONTRACT,
    FRIENDS_HEADER,
    TRAIN,
    USER_AGENT,
    VK_ADMIN_TOKEN,
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

    @property
    def table(self) -> Table:
        table = Table(
            Column("Баланс", style="cyan", justify="center"),
            Column("Размер армии", style="magenta", justify="center"),
            Column("Сила армии", style="green", justify="center"),
            title="github.com/monosans/vk-vbitve-bot v20220108",
        )
        table.add_row(*map(str, (self.balance, len(self.army), self.power)))
        return table


def attack(
    target: int,
    client: VBitve,
    profile: Profile,
    live: Live,
    log: Callable[[Any], None],
) -> None:
    attack = client.attack(target)
    if attack:
        profile.update(attack["new_user"])
        live.update(profile.table, refresh=True)
        text = attack["snackbar"]["text"].split("\n")[-1]
        log(f"Напал на id{target}: +{text}")


def bot(
    client: VBitve, profile: Profile, live: Live, log: Callable[[Any], None]
) -> None:
    if ATTACK and profile.next_attack < time() * 1000:
        wars = client.clan_me().get("active_wars")
        if wars:
            war = choice(wars)
            try:
                enemy_clan = war["clan"]
            except KeyError:
                enemy_clan = war["attackedClan"]
            target_clan = client.clan(enemy_clan["id"])
            if target_clan:
                army = target_clan["army"]
                suitable_enemies = [
                    enemy for enemy in army if enemy["power"] < profile.power
                ]
                target = suitable_enemies[0] if suitable_enemies else army[-1]
                attack(target["id"], client, profile, live, log)
        else:
            users = [
                user
                for user in client.for_me().get("items", {})
                if user["id"] not in ATTACK_EXCLUDE
            ]
            if users:
                attack(choice(users)["id"], client, profile, live, log)
    if profile.cooldown < time() * 1000:
        if TRAIN and profile.balance >= profile.train_cost:
            train = client.train()
            if train:
                profile.update(train["new_user"])
                live.update(profile.table, refresh=True)
                log(f"Тренирую армию -{profile.train_cost}$")
        elif CONTRACT:
            contract = client.contract()
            if contract:
                profile.update(contract["new_user"])
                live.update(profile.table, refresh=True)
                log(f"Беру контракт +{profile.contract}$")
    time_to_wait = int(profile.full_cooldown / 1000 - time()) + 1
    if time_to_wait > 0:
        log(f"Жду {time_to_wait} секунд до окончания перезарядки")
        sleep(time_to_wait)


def main() -> NoReturn:
    with Session() as session:
        client = VBitve(session, VK_ADMIN_TOKEN, FRIENDS_HEADER, USER_AGENT)
        profile = Profile(client.get())
        with Live(
            profile.table, console=client.console, auto_refresh=False
        ) as live:
            log = client.logger.print
            while True:
                bot(client, profile, live, log)


if __name__ == "__main__":
    main()

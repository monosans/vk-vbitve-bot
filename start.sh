#!/bin/sh
python -m pip install -U 'aiohttp<4.0.0' 'rich<12.0.0'
cd vk-vbitve-bot
clear
python bot.py

#!/bin/sh
python -m pip install -U 'requests<3.0.0' 'rich<12.0.0'
cd vk-vbitve-bot
clear
python bot.py

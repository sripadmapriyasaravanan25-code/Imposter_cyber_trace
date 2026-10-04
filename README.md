# IMPOSTER: CYBER TRACE

A small 2D investigation game for a college Python assignment. You play a cyber investigator who must find which employee stole confidential data.

The project uses only **Python 3**, **Pygame**, and the **standard library**. It does not use the internet, APIs, or a database. All graphics are drawn with Pygame shapes and text.

## Description

Someone downloaded `CONFIDENTIAL_DATA.zip` from the company network. Five suspects are on the case file: **Alex, Maya, Ryan, Leo, and Nina**. Exactly one of them is the imposter.

You open **LOG**, **CHAT**, and **FILE** records, look for contradictions, and make an accusation before the 60-second timer ends.

Some evidence is planted to mislead you. The loudest alarm is not always the thief. You need to combine timestamps across login, chat, and file access.

This first version uses a **deterministic demo case**. The real imposter is always **Alex**, so the game is easy to present in class.

## Features

- Main menu with Start, How to Play, and Quit
- Five suspect cards with LOG / CHAT / FILE buttons
- 60-second countdown, evidence counter, and score
- Unique evidence tracking (re-opening a record is free)
- Accuse overlay with one button per suspect
- Win / lose result screen and Play Again
- Hover effects on buttons (rect collision)
- Blinking timer warning when time is low
- Evidence notification toast
- Dark neon cybersecurity UI drawn without image files
- Simple game state machine: `MENU`, `HOW_TO_PLAY`, `INVESTIGATION`, `EVIDENCE`, `ACCUSATION`, `RESULT`

## Technologies used

- Python 3
- Pygame (this project installs **pygame-ce**, the Community Edition — same `import pygame` API)
- Python standard library (`sys`, `math`)

## How to install

1. Install Python 3 from [python.org](https://www.python.org/) if it is not already installed.
2. Open a terminal in this project folder.
3. (Optional) create a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

If you are on Python 3.11–3.13 and prefer classic Pygame:

```bash
pip install pygame
```

## How to run

```bash
python main.py
```

A 1280×720 window should open. The game is meant for a normal Windows laptop.

## Controls

| Action | Control |
| --- | --- |
| Click buttons | Left mouse button |
| Close evidence / cancel accuse / leave How to Play | `Esc` |
| Quit from the menu | `Esc` or **QUIT** |
| Restart after a verdict | **PLAY AGAIN** |

## Game rules

- Starting score: **1000**
- Opening a **new** evidence item: **-25** points and evidence count +1
- Re-opening the same item: **0** points
- Correct accusation: **+500** plus leftover seconds × **10**
- Wrong accusation: **-300** (no time bonus)
- Timer stops when the case ends or when it reaches 0
- You can still accuse after the timer hits 0
- Exactly one imposter (Alex in this demo)

### Demo case (spoiler)

Alex says he left at 10 PM, but an office login at 23:42 is followed by a download of `CONFIDENTIAL_DATA.zip` at 23:45. Leo’s late VPN login looks worse at first, but he never accessed the file. Maya only viewed the zip. Ryan and Nina are consistent.

## Project structure

```
.
├── main.py             # Entire game: states, UI, case data, loop
├── requirements.txt    # pygame
└── README.md           # This file
```

`main.py` is organized so it is easy to explain:

- Constants for window size, colors, scoring, and states
- `EVIDENCE` dictionary holding the deterministic case
- `Button` class using `rect.collidepoint` for clicks and hover
- `Game` class with `handle_events`, `update`, and `draw`
- `Game.run()` as the 60 FPS main loop

## Assignment notes

No external image assets are required. No online services are required. Close the window or press Quit to exit.

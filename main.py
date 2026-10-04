"""
IMPOSTER: CYBER TRACE
A 2D cybersecurity investigation game built with Python 3 and Pygame.

The player reviews login, chat, and file evidence for five suspects
and must identify the real imposter. Exactly one suspect is guilty.

Run with: python main.py
"""

import sys
import math
import pygame


# ---------------------------------------------------------------------------
# Window and timing
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1280, 720
FPS = 60
TITLE = "IMPOSTER: CYBER TRACE"

# Game states (simple state machine used by Game.update / Game.draw)
MENU = "MENU"
HOW_TO_PLAY = "HOW_TO_PLAY"
INVESTIGATION = "INVESTIGATION"
EVIDENCE = "EVIDENCE"
ACCUSATION = "ACCUSATION"
RESULT = "RESULT"

# Scoring rules
START_SCORE = 1000
EVIDENCE_COST = 25
CORRECT_BONUS = 500
WRONG_PENALTY = 300
TIME_BONUS_PER_SECOND = 10
INVESTIGATION_SECONDS = 60

# Colors — dark background with neon cyber accents
BG = (6, 10, 18)
BG_PANEL = (12, 20, 34)
BG_PANEL_ALT = (16, 28, 46)
BG_CARD = (14, 24, 40)
CYAN = (0, 230, 255)
CYAN_DIM = (0, 140, 170)
GREEN = (80, 255, 170)
MAGENTA = (255, 70, 160)
ORANGE = (255, 170, 70)
YELLOW = (255, 220, 90)
WHITE = (230, 240, 255)
MUTED = (140, 160, 185)
RED = (255, 70, 90)
DANGER = (255, 50, 80)


# ---------------------------------------------------------------------------
# Deterministic case data (easy to demo in class)
# Real imposter: Alex
# The player must combine LOG + CHAT + FILE. Some clues are planted/misleading.
# ---------------------------------------------------------------------------
SUSPECTS = ["Alex", "Maya", "Ryan", "Leo", "Nina"]
IMPOSTER = "Alex"

EVIDENCE = {
    "Alex": {
        "LOG": {
            "title": "LOGIN LOG — ALEX",
            "lines": [
                "23:42  SUCCESS  Office LAN  (10.12.4.18)",
                "Session token issued. MFA skipped (remembered device).",
                "Previous logout recorded at 22:01.",
            ],
            "analysis": (
                "A successful office login at 23:42 is late, but a login alone "
                "is not proof. Compare this timestamp with Alex's chat and file access."
            ),
            "tag": "SUSPICIOUS TIME",
            "severity": "medium",
        },
        "CHAT": {
            "title": "INTERNAL CHAT — ALEX",
            "lines": [
                "Alex: I left the office at 10 PM. Laptop is at home.",
                "Alex: If anything looks weird overnight, it is not me.",
                "Maya: Copy. I am still wrapping reports.",
            ],
            "analysis": (
                "Alex claims to have left at 10:00 PM (22:00). That CONTRADICTS "
                "the 23:42 office login. Misleading planted line: 'if anything looks "
                "weird it is not me' — do not trust a statement without matching logs."
            ),
            "tag": "CONTRADICTION",
            "severity": "high",
        },
        "FILE": {
            "title": "FILE ACCESS — ALEX",
            "lines": [
                "23:45  OPEN     /secure/CONFIDENTIAL_DATA.zip",
                "23:46  DOWNLOAD /secure/CONFIDENTIAL_DATA.zip  (48.2 MB)",
                "23:47  COPY     to USB volume labeled 'BACKUP-A'",
            ],
            "analysis": (
                "Confidential data was opened AND downloaded three minutes after "
                "the late login. Combined with the 10 PM alibi, this is the theft "
                "window. Other suspects look noisy, but only Alex downloaded the zip."
            ),
            "tag": "DATA THEFT",
            "severity": "high",
        },
    },
    "Maya": {
        "LOG": {
            "title": "LOGIN LOG — MAYA",
            "lines": [
                "22:15  SUCCESS  Office LAN  (10.12.4.22)",
                "MFA approved from registered phone.",
                "Badge swipe at north door: 22:09.",
            ],
            "analysis": (
                "Maya's login matches her badge time. Late work is real, but it is "
                "not automatically theft. Check whether she downloaded the file."
            ),
            "tag": "LATE SHIFT",
            "severity": "low",
        },
        "CHAT": {
            "title": "INTERNAL CHAT — MAYA",
            "lines": [
                "Maya: Working late on the quarterly report.",
                "Maya: I only need read access to the finance folder.",
                "Ryan: Do not download the zip. Policy is view-only.",
            ],
            "analysis": (
                "Maya says she was working late, which matches her 22:15 login. "
                "This looks honest so far. The zip warning in chat is a planted "
                "red herring, not proof that Maya stole anything."
            ),
            "tag": "ALIBI MATCHES",
            "severity": "low",
        },
        "FILE": {
            "title": "FILE ACCESS — MAYA",
            "lines": [
                "22:20  VIEW  /secure/CONFIDENTIAL_DATA.zip  (preview only)",
                "22:21  VIEW  /reports/Q4_summary.xlsx",
                "No download event. No USB mount.",
            ],
            "analysis": (
                "Maya viewed the confidential file but did not download it. "
                "Suspicious at first glance, yet incomplete for theft. Compare "
                "with whoever actually copied CONFIDENTIAL_DATA.zip."
            ),
            "tag": "VIEW ONLY",
            "severity": "medium",
        },
    },
    "Ryan": {
        "LOG": {
            "title": "LOGIN LOG — RYAN",
            "lines": [
                "18:05  SUCCESS  Office LAN  (10.12.4.09)",
                "Normal business hours. MFA ok.",
                "Logout: 18:28.",
            ],
            "analysis": (
                "Standard end-of-day login. Nothing here points to a midnight theft. "
                "Still check chat and files so you are not missing a planted clue."
            ),
            "tag": "NORMAL",
            "severity": "low",
        },
        "CHAT": {
            "title": "INTERNAL CHAT — RYAN",
            "lines": [
                "Ryan: Heading out at 18:30. Standup notes are in the channel.",
                "Leo: All good. Have a good night.",
                "Ryan: Phone is on silent after that.",
            ],
            "analysis": (
                "Ryan's chat matches his logout. No contradiction. A clean record "
                "can still hide guilt, so confirm file access before clearing anyone."
            ),
            "tag": "CONSISTENT",
            "severity": "low",
        },
        "FILE": {
            "title": "FILE ACCESS — RYAN",
            "lines": [
                "18:12  OPEN  /projects/standup.md",
                "18:20  EDIT  /projects/ticket_queue.csv",
                "No access to /secure/ after 18:05.",
            ],
            "analysis": (
                "No suspicious file access. Ryan is a weak suspect unless another "
                "record contradicts this. Do not accuse based on 'least activity' either."
            ),
            "tag": "CLEAN",
            "severity": "low",
        },
    },
    "Leo": {
        "LOG": {
            "title": "LOGIN LOG — LEO",
            "lines": [
                "23:50  SUCCESS  Remote VPN  (unknown device fingerprint)",
                "Failed MFA at 23:48, then success with backup code.",
                "Source IP is a coffee-shop range, not the office LAN.",
            ],
            "analysis": (
                "This login looks very suspicious and was likely PLANTED to frame Leo. "
                "A weird login is not enough. Check whether Leo touched the stolen file."
            ),
            "tag": "PLANTED?",
            "severity": "high",
        },
        "CHAT": {
            "title": "INTERNAL CHAT — LEO",
            "lines": [
                "Leo: I think my account was compromised earlier tonight.",
                "Leo: I did not request a backup MFA code. Reset my access.",
                "IT-BOT: Ticket #441 opened. Session will be reviewed.",
            ],
            "analysis": (
                "Leo reports a compromised account. That can explain the 23:50 VPN "
                "login. If file logs show no confidential download on Leo, the late "
                "login is misleading evidence, not the theft itself."
            ),
            "tag": "COMPROMISE CLAIM",
            "severity": "medium",
        },
        "FILE": {
            "title": "FILE ACCESS — LEO",
            "lines": [
                "No direct access to CONFIDENTIAL_DATA.zip.",
                "23:51  DENIED  /secure/  (expired clearance)",
                "Session dropped by IT after ticket #441.",
            ],
            "analysis": (
                "Leo never reached the confidential file. The scary login was a decoy. "
                "The real imposter wants you to accuse the 'compromised' account."
            ),
            "tag": "NO THEFT",
            "severity": "low",
        },
    },
    "Nina": {
        "LOG": {
            "title": "LOGIN LOG — NINA",
            "lines": [
                "21:10  SUCCESS  Office LAN  (10.12.4.31)",
                "MFA ok. Known workstation NINA-WS.",
                "Logout: 22:40.",
            ],
            "analysis": (
                "Evening login on Nina's own workstation. Timing does not overlap "
                "the 23:45 download. Still verify chat and files."
            ),
            "tag": "NORMAL",
            "severity": "low",
        },
        "CHAT": {
            "title": "INTERNAL CHAT — NINA",
            "lines": [
                "Nina: Preparing the client presentation. Need the template.",
                "Maya: Template is in /shared/decks.",
                "Nina: Thanks. I will not touch the secure folder.",
            ],
            "analysis": (
                "Nina's story is about a presentation. Look at the file log: if she "
                "only opened a deck, this is consistent, not a confession."
            ),
            "tag": "MATCHES STORY",
            "severity": "low",
        },
        "FILE": {
            "title": "FILE ACCESS — NINA",
            "lines": [
                "21:18  OPEN  /shared/decks/ClientPitch_v3.pptx",
                "21:55  SAVE  /shared/decks/ClientPitch_v3.pptx",
                "No confidential zip activity.",
            ],
            "analysis": (
                "Opened a normal presentation file only. Nina is not the download "
                "source. Do not confuse 'was in the building' with 'stole the data'."
            ),
            "tag": "PRESENTATION",
            "severity": "low",
        },
    },
}


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def wrap_text(text, font, max_width):
    """Split a string into lines that fit inside max_width pixels."""
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_scanlines(surface, alpha=18):
    """Subtle CRT/scanline overlay for a cyber look."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(0, HEIGHT, 4):
        pygame.draw.line(overlay, (0, 255, 255, alpha), (0, y), (WIDTH, y))
    surface.blit(overlay, (0, 0))


def draw_grid(surface, t):
    """Animated background grid."""
    offset = int((t * 20) % 40)
    for x in range(-40 + offset, WIDTH, 40):
        pygame.draw.line(surface, (18, 36, 58), (x, 0), (x, HEIGHT))
    for y in range(-40 + offset // 2, HEIGHT, 40):
        pygame.draw.line(surface, (16, 30, 48), (0, y), (WIDTH, y))


# ---------------------------------------------------------------------------
# Button with hover + click collision (rect collidepoint)
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, rect, label, font, accent=CYAN, fill=BG_CARD):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.accent = accent
        self.fill = fill
        self.hover = False
        self.pulse = 0.0

    def handle_event(self, event):
        """Return True when this button is left-clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def update_hover(self, mouse_pos):
        self.hover = self.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        color = self.accent
        fill = tuple(min(255, c + 18) for c in self.fill) if self.hover else self.fill
        border_w = 3 if self.hover else 1
        pygame.draw.rect(surface, fill, self.rect, border_radius=10)
        pygame.draw.rect(surface, color, self.rect, width=border_w, border_radius=10)

        if self.hover:
            glow = pygame.Surface((self.rect.w + 12, self.rect.h + 12), pygame.SRCALPHA)
            pygame.draw.rect(
                glow,
                (*color[:3], 40),
                glow.get_rect(),
                border_radius=12,
            )
            surface.blit(glow, (self.rect.x - 6, self.rect.y - 6))

        text = self.font.render(self.label, True, WHITE if self.hover else color)
        surface.blit(text, text.get_rect(center=self.rect.center))


# ---------------------------------------------------------------------------
# Main game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        self.time_alive = 0.0

        self.font_xl = pygame.font.SysFont("consolas", 54, bold=True)
        self.font_lg = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_md = pygame.font.SysFont("consolas", 22, bold=True)
        self.font_sm = pygame.font.SysFont("consolas", 18)
        self.font_xs = pygame.font.SysFont("consolas", 15)

        self.state = MENU
        self.panel_alpha = 0
        self.notify_timer = 0.0
        self.notify_text = ""
        self.blink = 0.0

        self._build_menu_buttons()
        self.reset_case()

    def reset_case(self):
        """Start / restart a case. Imposter stays Alex (deterministic demo)."""
        self.score = START_SCORE
        self.time_left = float(INVESTIGATION_SECONDS)
        self.opened = set()  # unique evidence keys like ("Alex", "LOG")
        self.view_suspect = None
        self.view_kind = None
        self.accused = None
        self.correct = False
        self.final_score = START_SCORE
        self.time_bonus = 0
        self.timer_stopped = False
        self.panel_alpha = 0
        self.notify_timer = 0.0
        self._build_investigation_buttons()
        self._build_accusation_buttons()
        self._build_result_buttons()

    # ----- UI layout -------------------------------------------------------
    def _build_menu_buttons(self):
        cx = WIDTH // 2
        self.btn_start = Button((cx - 160, 340, 320, 54), "START GAME", self.font_md, CYAN)
        self.btn_how = Button((cx - 160, 410, 320, 54), "HOW TO PLAY", self.font_md, GREEN)
        self.btn_quit = Button((cx - 160, 480, 320, 54), "QUIT", self.font_md, MAGENTA)
        self.btn_how_back = Button((cx - 160, 620, 320, 48), "BACK TO MENU", self.font_md, CYAN)

    def _build_investigation_buttons(self):
        self.suspect_buttons = {}
        card_w, card_h = 220, 360
        gap = 18
        total = 5 * card_w + 4 * gap
        start_x = (WIDTH - total) // 2
        y = 150
        for i, name in enumerate(SUSPECTS):
            x = start_x + i * (card_w + gap)
            log_btn = Button((x + 16, y + 150, card_w - 32, 40), "LOG", self.font_sm, CYAN)
            chat_btn = Button((x + 16, y + 200, card_w - 32, 40), "CHAT", self.font_sm, GREEN)
            file_btn = Button((x + 16, y + 250, card_w - 32, 40), "FILE", self.font_sm, ORANGE)
            self.suspect_buttons[name] = {
                "rect": pygame.Rect(x, y, card_w, card_h),
                "LOG": log_btn,
                "CHAT": chat_btn,
                "FILE": file_btn,
            }
        self.btn_accuse = Button((WIDTH // 2 - 180, 540, 360, 52), "ACCUSE IMPOSTER", self.font_md, MAGENTA)
        self.btn_menu_from_inv = Button((24, 16, 140, 36), "MENU", self.font_xs, MUTED)

    def _build_accusation_buttons(self):
        self.accuse_name_buttons = []
        self.btn_cancel_accuse = Button((WIDTH // 2 - 140, 560, 280, 44), "CANCEL", self.font_md, MUTED)
        w, h = 200, 52
        gap = 16
        total = 5 * w + 4 * gap
        x0 = (WIDTH - total) // 2
        y = 300
        accents = [CYAN, GREEN, ORANGE, MAGENTA, YELLOW]
        for i, name in enumerate(SUSPECTS):
            btn = Button((x0 + i * (w + gap), y, w, h), name.upper(), self.font_md, accents[i])
            self.accuse_name_buttons.append((name, btn))

    def _build_result_buttons(self):
        self.btn_play_again = Button((WIDTH // 2 - 160, 560, 320, 50), "PLAY AGAIN", self.font_md, GREEN)
        self.btn_result_quit = Button((WIDTH // 2 - 160, 622, 320, 44), "QUIT", self.font_sm, MAGENTA)

    def _build_evidence_close(self):
        self.btn_close_evidence = Button((WIDTH // 2 - 120, 600, 240, 44), "CLOSE", self.font_md, CYAN)

    # ----- Evidence open ---------------------------------------------------
    def open_evidence(self, suspect, kind):
        key = (suspect, kind)
        first_time = key not in self.opened
        if first_time:
            self.opened.add(key)
            self.score = max(0, self.score - EVIDENCE_COST)
            self.notify_text = f"NEW EVIDENCE  +1   {suspect} / {kind}   -{EVIDENCE_COST} pts"
            self.notify_timer = 2.2
        else:
            self.notify_text = f"RE-OPENED  {suspect} / {kind}   (no extra cost)"
            self.notify_timer = 1.4
        self.view_suspect = suspect
        self.view_kind = kind
        self.panel_alpha = 0
        self._build_evidence_close()
        self.state = EVIDENCE

    def finish_case(self, accused):
        self.accused = accused
        self.correct = accused == IMPOSTER
        remaining = max(0, int(self.time_left))
        self.time_bonus = remaining * TIME_BONUS_PER_SECOND if self.correct else 0
        if self.correct:
            self.final_score = self.score + CORRECT_BONUS + self.time_bonus
        else:
            self.final_score = max(0, self.score - WRONG_PENALTY)
        self.score = self.final_score
        self.timer_stopped = True
        self.panel_alpha = 0
        self.state = RESULT

    # ----- Events ----------------------------------------------------------
    def handle_events(self):
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.state == EVIDENCE:
                    self.state = INVESTIGATION
                elif self.state == ACCUSATION:
                    self.state = INVESTIGATION
                elif self.state == HOW_TO_PLAY:
                    self.state = MENU
                elif self.state == MENU:
                    self.running = False
                continue

            if self.state == MENU:
                if self.btn_start.handle_event(event):
                    self.reset_case()
                    self.state = INVESTIGATION
                elif self.btn_how.handle_event(event):
                    self.state = HOW_TO_PLAY
                    self.panel_alpha = 0
                elif self.btn_quit.handle_event(event):
                    self.running = False

            elif self.state == HOW_TO_PLAY:
                if self.btn_how_back.handle_event(event):
                    self.state = MENU

            elif self.state == INVESTIGATION:
                self.btn_accuse.update_hover(mouse)
                self.btn_menu_from_inv.update_hover(mouse)
                if self.btn_menu_from_inv.handle_event(event):
                    self.state = MENU
                elif self.btn_accuse.handle_event(event):
                    self.state = ACCUSATION
                    self.panel_alpha = 0
                else:
                    for name, pack in self.suspect_buttons.items():
                        for kind in ("LOG", "CHAT", "FILE"):
                            pack[kind].update_hover(mouse)
                            if pack[kind].handle_event(event):
                                self.open_evidence(name, kind)

            elif self.state == EVIDENCE:
                if self.btn_close_evidence.handle_event(event):
                    self.state = INVESTIGATION

            elif self.state == ACCUSATION:
                if self.btn_cancel_accuse.handle_event(event):
                    self.state = INVESTIGATION
                else:
                    for name, btn in self.accuse_name_buttons:
                        if btn.handle_event(event):
                            self.finish_case(name)

            elif self.state == RESULT:
                if self.btn_play_again.handle_event(event):
                    self.reset_case()
                    self.state = INVESTIGATION
                elif self.btn_result_quit.handle_event(event):
                    self.running = False

        # Keep hover in sync even without motion events
        if self.state == MENU:
            self.btn_start.update_hover(mouse)
            self.btn_how.update_hover(mouse)
            self.btn_quit.update_hover(mouse)
        elif self.state == HOW_TO_PLAY:
            self.btn_how_back.update_hover(mouse)
        elif self.state == EVIDENCE:
            self.btn_close_evidence.update_hover(mouse)
        elif self.state == ACCUSATION:
            self.btn_cancel_accuse.update_hover(mouse)
            for _, btn in self.accuse_name_buttons:
                btn.update_hover(mouse)
        elif self.state == RESULT:
            self.btn_play_again.update_hover(mouse)
            self.btn_result_quit.update_hover(mouse)

    # ----- Update ----------------------------------------------------------
    def update(self, dt):
        self.time_alive += dt
        self.blink += dt
        self.panel_alpha = min(255, self.panel_alpha + int(dt * 900))
        if self.notify_timer > 0:
            self.notify_timer -= dt

        if self.state in (INVESTIGATION, EVIDENCE, ACCUSATION) and not self.timer_stopped:
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                self.timer_stopped = True
                self.notify_text = "TIME EXPIRED — make an accusation"
                self.notify_timer = 3.0

    # ----- Draw screens ----------------------------------------------------
    def draw_header_bar(self):
        bar = pygame.Rect(0, 0, WIDTH, 72)
        pygame.draw.rect(self.screen, (8, 14, 26), bar)
        pygame.draw.line(self.screen, CYAN_DIM, (0, 72), (WIDTH, 72), 2)

        title = self.font_md.render("IMPOSTER: CYBER TRACE", True, CYAN)
        self.screen.blit(title, (180, 22))

        # Timer
        secs = int(math.ceil(self.time_left))
        timer_color = RED if secs <= 10 else (ORANGE if secs <= 20 else GREEN)
        if secs <= 10 and int(self.blink * 4) % 2 == 0:
            timer_color = WHITE
        timer_label = self.font_lg.render(f"{secs:02d}s", True, timer_color)
        self.screen.blit(timer_label, (WIDTH - 140, 16))
        tcap = self.font_xs.render("TIMER", True, MUTED)
        self.screen.blit(tcap, (WIDTH - 140, 50))

        ev = self.font_md.render(f"EVIDENCE  {len(self.opened)}/15", True, YELLOW)
        self.screen.blit(ev, (520, 24))
        sc = self.font_md.render(f"SCORE  {self.score}", True, GREEN)
        self.screen.blit(sc, (780, 24))

    def draw_notification(self):
        if self.notify_timer <= 0:
            return
        alpha = 255 if self.notify_timer > 0.4 else int(255 * (self.notify_timer / 0.4))
        surf = pygame.Surface((720, 40), pygame.SRCALPHA)
        pygame.draw.rect(surf, (0, 40, 50, min(200, alpha)), surf.get_rect(), border_radius=8)
        pygame.draw.rect(surf, (*CYAN, alpha), surf.get_rect(), 1, border_radius=8)
        text = self.font_sm.render(self.notify_text, True, (*CYAN, alpha)[:3])
        # pygame font doesn't take per-pixel alpha easily; blit onto surf
        text = self.font_sm.render(self.notify_text, True, CYAN)
        surf.blit(text, text.get_rect(center=surf.get_rect().center))
        surf.set_alpha(alpha)
        self.screen.blit(surf, surf.get_rect(center=(WIDTH // 2, 100)))

    def draw_menu(self):
        # Title glow
        for i, a in enumerate((40, 80, 160, 255)):
            col = (0, min(255, 180 + i * 20), min(255, 220 + i * 10))
            title = self.font_xl.render("IMPOSTER: CYBER TRACE", True, col)
            r = title.get_rect(center=(WIDTH // 2, 170 - i))
            if a < 255:
                title.set_alpha(a)
            self.screen.blit(title, r)

        sub = self.font_lg.render("FIND THE IMPOSTER", True, MAGENTA)
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 240)))

        tag = self.font_sm.render("SECURE NODE  //  DATA THEFT CASE 01  //  5 SUSPECTS", True, MUTED)
        self.screen.blit(tag, tag.get_rect(center=(WIDTH // 2, 285)))

        self.btn_start.draw(self.screen)
        self.btn_how.draw(self.screen)
        self.btn_quit.draw(self.screen)

        foot = self.font_xs.render("Python  +  Pygame   |   College assignment demo   |   ESC to quit", True, MUTED)
        self.screen.blit(foot, foot.get_rect(center=(WIDTH // 2, HEIGHT - 36)))

    def draw_how_to_play(self):
        panel = pygame.Rect(140, 70, WIDTH - 280, 530)
        overlay = pygame.Surface((panel.w, panel.h), pygame.SRCALPHA)
        overlay.fill((10, 18, 32, min(self.panel_alpha, 230)))
        self.screen.blit(overlay, panel.topleft)
        pygame.draw.rect(self.screen, CYAN, panel, 2, border_radius=12)

        title = self.font_lg.render("HOW TO PLAY", True, CYAN)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 110)))

        steps = [
            "You are a cyber investigator. Someone stole CONFIDENTIAL_DATA.zip.",
            "Exactly ONE of the five suspects is the real imposter.",
            "Open LOG, CHAT, and FILE evidence on each suspect card.",
            "Each NEW evidence item costs 25 points. Re-opening is free.",
            "Some clues are planted / misleading. Do not accuse the noisiest log.",
            "Combine timestamps: a chat alibi can contradict a login time.",
            "You have 60 seconds. Leftover time becomes bonus points if you are right.",
            "Click ACCUSE IMPOSTER, choose a name, then review the case result.",
            "Correct accusation: +500. Wrong accusation: -300. Starting score: 1000.",
            "ESC closes panels. PLAY AGAIN resets the same demo case (imposter is fixed).",
        ]
        y = 155
        for i, line in enumerate(steps, 1):
            txt = self.font_sm.render(f"{i:02d}  {line}", True, WHITE)
            self.screen.blit(txt, (180, y))
            y += 36

        self.btn_how_back.draw(self.screen)

    def draw_investigation(self):
        self.draw_header_bar()
        self.btn_menu_from_inv.draw(self.screen)

        hint = self.font_xs.render(
            "Open LOG + CHAT + FILE. Look for contradictions, not just 'most suspicious'.",
            True,
            MUTED,
        )
        self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, 120)))

        for name, pack in self.suspect_buttons.items():
            rect = pack["rect"]
            opened_here = sum(1 for k in ("LOG", "CHAT", "FILE") if (name, k) in self.opened)
            border = CYAN if opened_here else MUTED
            pygame.draw.rect(self.screen, BG_CARD, rect, border_radius=14)
            pygame.draw.rect(self.screen, border, rect, 2, border_radius=14)

            # Avatar circle with initial
            cx, cy = rect.centerx, rect.y + 58
            pygame.draw.circle(self.screen, (20, 40, 60), (cx, cy), 34)
            pygame.draw.circle(self.screen, CYAN, (cx, cy), 34, 2)
            initial = self.font_lg.render(name[0], True, CYAN)
            self.screen.blit(initial, initial.get_rect(center=(cx, cy)))

            nm = self.font_md.render(name.upper(), True, WHITE)
            self.screen.blit(nm, nm.get_rect(center=(rect.centerx, rect.y + 112)))

            status = self.font_xs.render(f"FILES OPENED  {opened_here}/3", True, YELLOW if opened_here else MUTED)
            self.screen.blit(status, status.get_rect(center=(rect.centerx, rect.bottom - 28)))

            pack["LOG"].draw(self.screen)
            pack["CHAT"].draw(self.screen)
            pack["FILE"].draw(self.screen)

        self.btn_accuse.draw(self.screen)
        self.draw_notification()

        if self.time_left <= 0:
            warn = self.font_xs.render("TIMER STOPPED — accuse a suspect to close the case", True, RED)
            self.screen.blit(warn, warn.get_rect(center=(WIDTH // 2, 132)))

    def draw_evidence(self):
        self.draw_investigation()
        # Dim background
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, min(180, self.panel_alpha)))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(180, 90, WIDTH - 360, 540)
        pygame.draw.rect(self.screen, BG_PANEL, panel, border_radius=14)

        kind_colors = {"LOG": CYAN, "CHAT": GREEN, "FILE": ORANGE}
        accent = kind_colors.get(self.view_kind, CYAN)
        pygame.draw.rect(self.screen, accent, panel, 2, border_radius=14)

        data = EVIDENCE[self.view_suspect][self.view_kind]
        title = self.font_lg.render(data["title"], True, accent)
        self.screen.blit(title, (panel.x + 32, panel.y + 24))

        sev = data["severity"]
        sev_col = RED if sev == "high" else (ORANGE if sev == "medium" else GREEN)
        tag_rect = pygame.Rect(panel.right - 220, panel.y + 28, 188, 32)
        pygame.draw.rect(self.screen, (20, 20, 30), tag_rect, border_radius=6)
        pygame.draw.rect(self.screen, sev_col, tag_rect, 1, border_radius=6)
        tag = self.font_xs.render(data["tag"], True, sev_col)
        self.screen.blit(tag, tag.get_rect(center=tag_rect.center))

        # Raw evidence lines
        y = panel.y + 90
        box = pygame.Rect(panel.x + 32, y, panel.w - 64, 150)
        pygame.draw.rect(self.screen, (8, 12, 22), box, border_radius=8)
        pygame.draw.rect(self.screen, CYAN_DIM, box, 1, border_radius=8)
        ly = box.y + 16
        for line in data["lines"]:
            row = self.font_sm.render(line, True, WHITE)
            self.screen.blit(row, (box.x + 16, ly))
            ly += 40

        # Analyst note
        note_title = self.font_md.render("ANALYST NOTE  —  why this matters", True, YELLOW)
        self.screen.blit(note_title, (panel.x + 32, box.bottom + 24))
        ny = box.bottom + 60
        for wline in wrap_text(data["analysis"], self.font_sm, panel.w - 80):
            self.screen.blit(self.font_sm.render(wline, True, MUTED), (panel.x + 32, ny))
            ny += 26

        uniq = "COUNTED  (unique)" if (self.view_suspect, self.view_kind) in self.opened else ""
        meta = self.font_xs.render(
            f"Suspect: {self.view_suspect}   |   Channel: {self.view_kind}   |   {uniq}",
            True,
            MUTED,
        )
        self.screen.blit(meta, (panel.x + 32, panel.bottom - 88))

        self.btn_close_evidence.draw(self.screen)

    def draw_accusation(self):
        self.draw_investigation()
        dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, min(190, self.panel_alpha)))
        self.screen.blit(dim, (0, 0))

        panel = pygame.Rect(80, 140, WIDTH - 160, 480)
        pygame.draw.rect(self.screen, BG_PANEL, panel, border_radius=14)
        pygame.draw.rect(self.screen, MAGENTA, panel, 2, border_radius=14)

        title = self.font_lg.render("SELECT THE IMPOSTER", True, MAGENTA)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 190)))
        warn = self.font_sm.render(
            "This locks the case. Combine LOG + CHAT + FILE before you choose.",
            True,
            WHITE,
        )
        self.screen.blit(warn, warn.get_rect(center=(WIDTH // 2, 240)))

        for _, btn in self.accuse_name_buttons:
            btn.draw(self.screen)
        self.btn_cancel_accuse.draw(self.screen)

    def draw_result(self):
        panel = pygame.Rect(160, 70, WIDTH - 320, 620)
        pygame.draw.rect(self.screen, BG_PANEL, panel, border_radius=16)
        color = GREEN if self.correct else RED
        pygame.draw.rect(self.screen, color, panel, 2, border_radius=16)

        headline = "CASE SOLVED!" if self.correct else "WRONG SUSPECT!"
        h = self.font_xl.render(headline, True, color)
        self.screen.blit(h, h.get_rect(center=(WIDTH // 2, 130)))

        you = self.font_md.render(f"You accused:  {self.accused.upper()}", True, WHITE)
        self.screen.blit(you, you.get_rect(center=(WIDTH // 2, 195)))
        real = self.font_lg.render(f"Real imposter:  {IMPOSTER.upper()}", True, MAGENTA)
        self.screen.blit(real, real.get_rect(center=(WIDTH // 2, 245)))

        why = (
            "Alex claimed to leave at 10 PM, but logged in from the office at 23:42 "
            "and downloaded CONFIDENTIAL_DATA.zip at 23:45. Leo's scary VPN login was a decoy. "
            "Maya only viewed the file. Ryan and Nina's records stay consistent."
        )
        y = 300
        for line in wrap_text(why, self.font_sm, panel.w - 80):
            row = self.font_sm.render(line, True, MUTED)
            self.screen.blit(row, row.get_rect(center=(WIDTH // 2, y)))
            y += 26

        # Score breakdown box
        box = pygame.Rect(WIDTH // 2 - 280, y + 16, 560, 150)
        pygame.draw.rect(self.screen, (8, 14, 24), box, border_radius=10)
        pygame.draw.rect(self.screen, CYAN_DIM, box, 1, border_radius=10)

        lines = [
            f"Evidence discovered:     {len(self.opened)} / 15",
            f"Time remaining bonus:    +{self.time_bonus}" if self.correct else "Time remaining bonus:    +0  (wrong call)",
            f"Accusation:              {'+500' if self.correct else '-300'}",
            f"FINAL SCORE:             {self.final_score}",
        ]
        ly = box.y + 16
        for i, line in enumerate(lines):
            col = GREEN if i == 3 else WHITE
            font = self.font_md if i == 3 else self.font_sm
            self.screen.blit(font.render(line, True, col), (box.x + 28, ly))
            ly += 32

        self.btn_play_again.draw(self.screen)
        self.btn_result_quit.draw(self.screen)

    def draw(self):
        self.screen.fill(BG)
        draw_grid(self.screen, self.time_alive)
        draw_scanlines(self.screen, 10)

        if self.state == MENU:
            self.draw_menu()
        elif self.state == HOW_TO_PLAY:
            self.draw_how_to_play()
        elif self.state == INVESTIGATION:
            self.draw_investigation()
        elif self.state == EVIDENCE:
            self.draw_evidence()
        elif self.state == ACCUSATION:
            self.draw_accusation()
        elif self.state == RESULT:
            self.draw_result()

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


def main():
    Game().run()


if __name__ == "__main__":
    main()

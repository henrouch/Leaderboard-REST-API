from __future__ import annotations

import json
import math
import random
import time
from dataclasses import dataclass
from pathlib import Path

import pygame
import requests


pygame.init()

WIDTH, HEIGHT = 800, 600
Window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Aim Trainer")

TARGET_SIZE = 30
TARGET_INCREMENT = 1000
TARGET_EVENT = pygame.USEREVENT
TARGET_PADDING = 40
BG_COLOR = (0, 25, 40)
TIME_LIMIT = 30
LIVES = 3
TOP_BAR_HEIGHT = 50

TITLE_FONT = pygame.font.SysFont("comicsans", 34)
LABEL_FONT = pygame.font.SysFont("comicsans", 24)
SMALL_FONT = pygame.font.SysFont("comicsans", 18)
TINY_FONT = pygame.font.SysFont("comicsans", 16)

API_URL = "http://127.0.0.1:8000/scores"
LOGIN_URL = "http://127.0.0.1:8000/auth/login"
REGISTER_URL = "http://127.0.0.1:8000/auth/register"
ME_URL = "http://127.0.0.1:8000/auth/me"
SESSION_FILE = Path.home() / ".aimforge_session.json"


@dataclass
class Session:
    username: str
    access_token: str


@dataclass
class Button:
    rect: pygame.Rect
    text: str
    active: bool = False

    def draw(self, surface, hover: bool = False) -> None:
        background = (0, 229, 255, 48) if hover or self.active else (12, 30, 44)
        border = (0, 229, 255) if hover or self.active else (70, 120, 150)
        pygame.draw.rect(surface, background, self.rect, border_radius=8)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=8)
        label = SMALL_FONT.render(self.text, True, (225, 245, 255))
        label_rect = label.get_rect(center=self.rect.center)
        surface.blit(label, label_rect)


class TextInput:
    def __init__(self, rect: pygame.Rect, placeholder: str, secret: bool = False):
        self.rect = rect
        self.placeholder = placeholder
        self.secret = secret
        self.text = ""
        self.active = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            return self.active

        if event.type != pygame.KEYDOWN or not self.active:
            return False

        if event.key == pygame.K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key == pygame.K_RETURN:
            return True
        elif event.unicode and event.unicode.isprintable() and len(self.text) < 128:
            self.text += event.unicode
        return False

    def draw(self, surface) -> None:
        border = (0, 229, 255) if self.active else (80, 110, 130)
        pygame.draw.rect(surface, (7, 17, 27), self.rect, border_radius=8)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=8)

        display = self.text
        if self.secret:
            display = "•" * len(self.text)
        if not display:
            label = TINY_FONT.render(self.placeholder, True, (105, 150, 175))
        else:
            label = TINY_FONT.render(display, True, (225, 245, 255))
        surface.blit(label, (self.rect.x + 10, self.rect.y + 10))


class Target:
    COLOR = "red"
    SECOND_COLOR = "white"
    max_time = TARGET_INCREMENT / 1000

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = TARGET_SIZE
        self.creation_time = time.time()

    def draw(self, surface):
        pygame.draw.circle(surface, self.COLOR, (self.x, self.y), self.size)
        pygame.draw.circle(
            surface, self.SECOND_COLOR, (self.x, self.y), int(self.size * 0.8)
        )
        pygame.draw.circle(surface, self.COLOR, (self.x, self.y), int(self.size * 0.6))
        pygame.draw.circle(
            surface, self.SECOND_COLOR, (self.x, self.y), int(self.size * 0.4)
        )

    def collide(self, x, y):
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        return distance <= self.size

    def is_expired(self):
        return time.time() - self.creation_time >= self.max_time


def load_session() -> Session | None:
    if not SESSION_FILE.exists():
        return None
    try:
        payload = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        username = str(payload.get("username", "")).strip()
        token = str(payload.get("access_token", "")).strip()
        if username and token:
            return Session(username=username, access_token=token)
    except Exception:
        return None
    return None


def save_session(session: Session) -> None:
    SESSION_FILE.write_text(
        json.dumps(
            {"username": session.username, "access_token": session.access_token}
        ),
        encoding="utf-8",
    )


def clear_session() -> None:
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def auth_request(url: str, username: str, password: str) -> Session:
    response = requests.post(
        url,
        json={"username": username, "password": password},
        timeout=10,
    )
    if not response.ok:
        raise RuntimeError(
            response.text or f"Authentication failed ({response.status_code})"
        )

    data = response.json()
    session = Session(
        username=str(data["username"]), access_token=str(data["access_token"])
    )
    save_session(session)
    return session


def validate_session(session: Session | None) -> Session | None:
    if session is None:
        return None

    try:
        response = requests.get(
            ME_URL,
            headers={"Authorization": f"Bearer {session.access_token}"},
            timeout=6,
        )
        if response.ok:
            profile = response.json()
            refreshed = Session(
                username=str(profile["username"]), access_token=session.access_token
            )
            save_session(refreshed)
            return refreshed
    except Exception:
        pass

    clear_session()
    return None


def format_time(secs):
    milli = math.floor(int(secs * 1000 % 1000) / 100)
    seconds = int(round(secs % 60, 1))
    minutes = int(secs // 60)
    return f"{minutes:02d}:{seconds:02d}.{milli}"


def draw_background(surface):
    surface.fill(BG_COLOR)
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for x in range(0, WIDTH, 60):
        pygame.draw.line(overlay, (0, 229, 255, 14), (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, 60):
        pygame.draw.line(overlay, (0, 229, 255, 14), (0, y), (WIDTH, y), 1)
    surface.blit(overlay, (0, 0))


def draw_auth_badge(surface, session: Session | None):
    badge_rect = pygame.Rect(WIDTH - 178, 10, 168, 28)
    pygame.draw.rect(surface, (235, 245, 250), badge_rect, border_radius=6)
    pygame.draw.rect(surface, (0, 229, 255), badge_rect, width=1, border_radius=6)
    if session:
        label = TINY_FONT.render(session.username, True, (0, 40, 60))
    else:
        label = TINY_FONT.render("Login / Register", True, (0, 40, 60))
    surface.blit(label, label.get_rect(center=badge_rect.center))


def draw_menu(
    surface, selected_mode, session, username_input, password_input, info_text
):
    draw_background(surface)

    title = TITLE_FONT.render("AIMFORGE", True, (230, 250, 255))
    subtitle = SMALL_FONT.render("Desktop Aim Trainer", True, (0, 229, 255))
    surface.blit(title, (40, 54))
    surface.blit(subtitle, (42, 96))

    description = [
        "Choose a mode, log in from the top-right, and your scores will save automatically.",
        "If you stay logged out, you can still play, but score submission is disabled.",
    ]
    for index, line in enumerate(description):
        rendered = SMALL_FONT.render(line, True, (180, 205, 220))
        surface.blit(rendered, (42, 142 + index * 28))

    mode_panel = pygame.Rect(36, 220, 360, 240)
    pygame.draw.rect(surface, (10, 26, 40), mode_panel, border_radius=14)
    pygame.draw.rect(surface, (0, 229, 255), mode_panel, width=1, border_radius=14)
    surface.blit(SMALL_FONT.render("Game Mode", True, (0, 229, 255)), (58, 242))

    timed_button = Button(pygame.Rect(60, 288, 140, 44), "Timed", selected_mode == "T")
    lives_button = Button(pygame.Rect(220, 288, 140, 44), "Lives", selected_mode == "L")
    timed_button.draw(surface, timed_button.active)
    lives_button.draw(surface, lives_button.active)

    start_button = Button(pygame.Rect(60, 362, 300, 48), "Start Game")
    start_button.draw(surface)

    hints = [
        "Timed: survive until the clock runs out.",
        "Lives: lose after three misses.",
    ]
    for index, line in enumerate(hints):
        rendered = TINY_FONT.render(line, True, (150, 180, 195))
        surface.blit(rendered, (60, 424 + index * 20))

    auth_panel = pygame.Rect(444, 54, 320, 406)
    pygame.draw.rect(surface, (10, 26, 40), auth_panel, border_radius=14)
    pygame.draw.rect(surface, (0, 229, 255), auth_panel, width=1, border_radius=14)

    if session:
        surface.blit(SMALL_FONT.render("Signed In", True, (0, 229, 255)), (468, 76))
        surface.blit(
            TITLE_FONT.render(session.username, True, (230, 250, 255)), (468, 114)
        )
        surface.blit(
            SMALL_FONT.render(
                "Your login is stored locally on this machine.", True, (160, 190, 205)
            ),
            (468, 170),
        )
        logout_button = Button(pygame.Rect(468, 228, 274, 42), "Logout")
        logout_button.draw(surface)
        surface.blit(
            TINY_FONT.render(
                "You can play immediately using the saved session.",
                True,
                (140, 170, 190),
            ),
            (468, 286),
        )
        info_y = 324
    else:
        surface.blit(
            SMALL_FONT.render("Login / Register", True, (0, 229, 255)), (468, 76)
        )
        username_input.draw(surface)
        password_input.draw(surface)
        login_button = Button(pygame.Rect(468, 274, 122, 42), "Login")
        register_button = Button(pygame.Rect(620, 274, 122, 42), "Register")
        login_button.draw(surface)
        register_button.draw(surface)
        surface.blit(
            TINY_FONT.render(
                "Use the same username for the game and portal.", True, (140, 170, 190)
            ),
            (468, 330),
        )
        info_y = 366

    if info_text:
        rendered = SMALL_FONT.render(
            info_text,
            True,
            (255, 196, 102) if "failed" not in info_text.lower() else (255, 102, 102),
        )
        surface.blit(rendered, (468, info_y))

    draw_auth_badge(surface, session)

    return {
        "timed": timed_button.rect,
        "lives": lives_button.rect,
        "start": start_button.rect,
        "logout": pygame.Rect(468, 228, 274, 42) if session else None,
        "login": pygame.Rect(468, 274, 122, 42) if not session else None,
        "register": pygame.Rect(620, 274, 122, 42) if not session else None,
    }


def draw_hud(surface, mode, session, elapsed_time, remaining_time, hits, misses):
    pygame.draw.rect(surface, (165, 165, 165), (0, 0, WIDTH, TOP_BAR_HEIGHT))
    if mode == "T":
        time_label = LABEL_FONT.render(
            f"Time: {format_time(remaining_time)}", True, "black"
        )
    else:
        time_label = LABEL_FONT.render(
            f"Time: {format_time(elapsed_time)}", True, "black"
        )
    surface.blit(time_label, (8, 5))

    hits_label = LABEL_FONT.render(f"Hits: {hits}", True, "black")
    surface.blit(hits_label, (300, 5))

    if mode == "L":
        lives_label = LABEL_FONT.render(f"Lives: {LIVES - misses}", True, "black")
        surface.blit(lives_label, (470, 5))

    misses_label = LABEL_FONT.render(f"Misses: {misses}", True, "black")
    surface.blit(misses_label, (610, 5))
    draw_auth_badge(surface, session)


def draw_targets(surface, targets):
    draw_background(surface)
    for target in targets:
        target.draw(surface)


def draw_end_screen(surface, session, elapsed_time, hits, misses, submit_message):
    surface.fill(BG_COLOR)

    title = TITLE_FONT.render("Round Complete", True, (230, 250, 255))
    surface.blit(title, (250, 60))

    total = hits + misses
    accuracy = round((hits / total * 100), 2) if total > 0 else 0.0

    stats = [
        f"Hits: {hits}",
        f"Misses: {misses}",
        f"Accuracy: {accuracy}%",
        f"Time: {format_time(elapsed_time)}",
    ]
    for index, line in enumerate(stats):
        rendered = LABEL_FONT.render(line, True, "white")
        surface.blit(rendered, (280, 160 + index * 52))

    message = (
        submit_message
        if submit_message
        else (
            "Saved locally only. Log in next round to submit."
            if not session
            else "Score submitted."
        )
    )
    message_rendered = SMALL_FONT.render(
        message,
        True,
        (255, 196, 102) if "saved locally" in message.lower() else (0, 229, 255),
    )
    surface.blit(message_rendered, (210, 410))

    replay_button = Button(pygame.Rect(230, 470, 150, 46), "Play Again")
    menu_button = Button(pygame.Rect(420, 470, 150, 46), "Main Menu")
    replay_button.draw(surface)
    menu_button.draw(surface)

    draw_auth_badge(surface, session)

    return {"replay": replay_button.rect, "menu": menu_button.rect}


def send_score(
    session: Session | None, mode: str, hits: int, misses: int, elapsed_time: float
):
    if session is None:
        return False, "Log in to submit scores."

    total = hits + misses
    accuracy = round((hits / total * 100), 2) if total > 0 else 0.0
    data = {
        "username": session.username,
        "hits": hits,
        "misses": misses,
        "accuracy": accuracy,
        "time": round(elapsed_time, 2),
        "mode": mode,
    }

    try:
        response = requests.post(
            API_URL,
            json=data,
            headers={"Authorization": f"Bearer {session.access_token}"},
            timeout=10,
        )
        if response.status_code == 401:
            clear_session()
            return False, "Session expired. Log in again to submit scores."
        if response.status_code == 403:
            return False, "Login does not match the score username."
        response.raise_for_status()
        return True, "Score submitted successfully."
    except Exception as exc:
        return False, f"Score not submitted: {exc}"


def make_game_round(mode: str):
    return {
        "mode": mode,
        "targets": [],
        "hits": 0,
        "clicks": 0,
        "misses": 0,
        "start_time": time.time(),
        "done": False,
        "submit_message": "",
    }


def main():
    clock = pygame.time.Clock()
    pygame.time.set_timer(TARGET_EVENT, TARGET_INCREMENT)

    session = validate_session(load_session())
    state = "menu"
    selected_mode = "T"
    info_text = ""
    username_input = TextInput(pygame.Rect(468, 126, 274, 42), "Username")
    password_input = TextInput(pygame.Rect(468, 182, 274, 42), "Password", secret=True)

    round_data = make_game_round(selected_mode)
    menu_buttons = {}
    end_buttons = {}

    running = True
    while running:
        clock.tick(60)
        click_position = None

        elapsed_time = time.time() - round_data["start_time"]
        remaining_time = max(TIME_LIMIT - elapsed_time, 0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if state == "menu":
                username_input.handle_event(event)
                password_input.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                click_position = event.pos

            if state == "game":
                if event.type == TARGET_EVENT:
                    x = random.randint(TARGET_PADDING, WIDTH - TARGET_PADDING)
                    y = random.randint(
                        TARGET_PADDING + TOP_BAR_HEIGHT, HEIGHT - TARGET_PADDING
                    )
                    round_data["targets"].append(Target(x, y))

                if event.type == pygame.MOUSEBUTTONDOWN:
                    round_data["clicks"] += 1
                    hit = False
                    for target in round_data["targets"]:
                        if target.collide(*event.pos):
                            round_data["hits"] += 1
                            hit = True
                            break
                    if not hit:
                        round_data["misses"] += 1

            if state == "end":
                if event.type == pygame.MOUSEBUTTONDOWN and end_buttons:
                    if end_buttons["replay"].collidepoint(event.pos):
                        round_data = make_game_round(selected_mode)
                        state = "game"
                    elif end_buttons["menu"].collidepoint(event.pos):
                        round_data = make_game_round(selected_mode)
                        state = "menu"

        if state == "menu":
            menu_buttons = draw_menu(
                Window,
                selected_mode,
                session,
                username_input,
                password_input,
                info_text,
            )

            if click_position:
                if menu_buttons["timed"].collidepoint(click_position):
                    selected_mode = "T"
                    round_data["mode"] = selected_mode
                elif menu_buttons["lives"].collidepoint(click_position):
                    selected_mode = "L"
                    round_data["mode"] = selected_mode
                elif menu_buttons["start"].collidepoint(click_position):
                    round_data = make_game_round(selected_mode)
                    state = "game"
                    info_text = ""
                elif menu_buttons.get("logout") and menu_buttons["logout"].collidepoint(
                    click_position
                ):
                    clear_session()
                    session = None
                    info_text = "Logged out."
                    username_input.text = ""
                    password_input.text = ""
                elif menu_buttons.get("login") and menu_buttons["login"].collidepoint(
                    click_position
                ):
                    try:
                        session = auth_request(
                            LOGIN_URL,
                            username_input.text.strip(),
                            password_input.text,
                        )
                        info_text = "Logged in successfully."
                        username_input.text = ""
                        password_input.text = ""
                    except Exception as exc:
                        info_text = f"Login failed: {exc}"
                elif menu_buttons.get("register") and menu_buttons[
                    "register"
                ].collidepoint(click_position):
                    try:
                        session = auth_request(
                            REGISTER_URL,
                            username_input.text.strip(),
                            password_input.text,
                        )
                        info_text = "Registered and logged in."
                        username_input.text = ""
                        password_input.text = ""
                    except Exception as exc:
                        info_text = f"Register failed: {exc}"

        elif state == "game":
            expired = [
                target for target in round_data["targets"] if target.is_expired()
            ]
            round_data["misses"] += len(expired)
            round_data["targets"] = [
                target for target in round_data["targets"] if not target.is_expired()
            ]

            if selected_mode == "L" and round_data["misses"] >= LIVES:
                state = "end"
            elif selected_mode == "T" and remaining_time <= 0:
                state = "end"

            draw_targets(Window, round_data["targets"])
            draw_hud(
                Window,
                selected_mode,
                session,
                elapsed_time,
                remaining_time,
                round_data["hits"],
                round_data["misses"],
            )
            mode_text = "Timed" if selected_mode == "T" else "Lives"
            mode_label = SMALL_FONT.render(f"Mode: {mode_text}", True, (255, 255, 255))
            Window.blit(mode_label, (8, TOP_BAR_HEIGHT + 8))

        elif state == "end":
            if not round_data["done"]:
                if session:
                    success, message = send_score(
                        session,
                        "Timed" if selected_mode == "T" else "Lives",
                        round_data["hits"],
                        round_data["misses"],
                        TIME_LIMIT if selected_mode == "T" else elapsed_time,
                    )
                    round_data["submit_message"] = message
                    if not success and "session expired" in message.lower():
                        session = None
                else:
                    round_data["submit_message"] = (
                        "Log in from the menu to submit scores."
                    )
                round_data["done"] = True

            end_buttons = draw_end_screen(
                Window,
                session,
                TIME_LIMIT if selected_mode == "T" else elapsed_time,
                round_data["hits"],
                round_data["misses"],
                round_data["submit_message"],
            )

        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()

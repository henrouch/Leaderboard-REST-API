import math
import random
import time
import pygame
import requests


pygame.init()

WIDTH, HEIGHT = 800, 600
Window = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python Aim Trainer")
Size = 30
TARGET_INCREMENT = 1000
TARGET_EVENT = pygame.USEREVENT
TARGET_PADDING = 40
BG_COLOR = (0, 25, 40)
TIME_LIMIT = 30
LIVES = 3
TopBarHeight = 50
LABEL_FONT = pygame.font.SysFont("comicsans", 24)
API_URL = "http://127.0.0.1:8000/scores"

invalid = True
while invalid:
    Mode = input("What mode do you want? (Timed(T) or Lives(L)): ").strip().upper()
    if Mode == "T":
        print("You have 30 seconds")
        invalid = False
    elif Mode == "L":
        print("You have 3 lives")
        invalid = False
    else:
        print("Invalid mode. Please choose Timed (T) or Lives (L).")


class Target:
    COLOR = "red"
    SECOND_COLOR = "white"
    max_time = TARGET_INCREMENT / 1000

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = Size
        self.creation_time = time.time()

    def draw(self, Window):
        pygame.draw.circle(Window, self.COLOR, (self.x, self.y), self.size)
        pygame.draw.circle(Window, self.SECOND_COLOR, (self.x, self.y), self.size * 0.8)
        pygame.draw.circle(Window, self.COLOR, (self.x, self.y), self.size * 0.6)
        pygame.draw.circle(Window, self.SECOND_COLOR, (self.x, self.y), self.size * 0.4)

    def collide(self, x, y):
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        return distance <= self.size

    def is_expired(self):
        return time.time() - self.creation_time >= self.max_time


def draw(Window, targets):
    Window.fill(BG_COLOR)
    for target in targets:
        target.draw(Window)


def format_time(secs):
    milli = math.floor(int(secs * 1000 % 1000) / 100)
    seconds = int(round(secs % 60, 1))
    minutes = int(secs // 60)
    return f"{minutes:02d}:{seconds:02d}.{milli}"


def draw_top_bar(Window, elapsed_time, remaining_time, hits, misses):
    pygame.draw.rect(Window, "grey", (0, 0, WIDTH, TopBarHeight))
    if Mode == "T":
        time_label = LABEL_FONT.render(f"Time: {format_time(remaining_time)} ", 1, "black")
        Window.blit(time_label, (5, 5))
    elif Mode == "L":
        time_label = LABEL_FONT.render(f"Time: {format_time(elapsed_time)} ", 1, "black")
        Window.blit(time_label, (5, 5))

    hits_label = LABEL_FONT.render(f"Hits: {hits}", 1, "black")
    Window.blit(hits_label, (450, 5))

    if Mode == "L":
        lives_label = LABEL_FONT.render(f"Lives: {LIVES - misses}", 1, "black")
        Window.blit(lives_label, (250, 5))

    misses_label = LABEL_FONT.render(f"Misses: {misses}", 1, "black")
    Window.blit(misses_label, (600, 5))


def send_score(username, hits, misses, elapsed_time):
    total = hits + misses
    accuracy = round((hits / total * 100), 2) if total > 0 else 0.0

    data = {
        "username": username,
        "hits": hits,
        "misses": misses,
        "accuracy": accuracy,
        "time": round(elapsed_time, 2),
        "mode": Mode
    }

    try:
        response = requests.post(API_URL, json=data)
        print("Score sent:", response.json())
    except Exception as e:
        print("Error sending score:", e)


def end_screen(Window, elapsed_time, hits, misses, clicks):
    Window.fill(BG_COLOR)

    total = hits + misses

    accuracy = round((hits / total * 100), 2) if total > 0 else 0.0

    hits_label = LABEL_FONT.render(f"Hits: {hits}", 1, "white")
    Window.blit(hits_label, (300, 200))

    misses_label = LABEL_FONT.render(f"Misses: {misses}", 1, "white")
    Window.blit(misses_label, (300, 250))

    accuracy_label = LABEL_FONT.render(f"Accuracy: {accuracy}%", 1, "white")
    Window.blit(accuracy_label, (300, 300))

    elapsed_time_label = LABEL_FONT.render(f"Time: {format_time(elapsed_time)}", 1, "white")
    Window.blit(elapsed_time_label, (300, 350))

    pygame.display.update()

    username = input("Enter your username: ")
    send_score(username, hits, misses, elapsed_time)

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                run = False

    pygame.quit()


def main():
    run = True
    targets = []
    clock = pygame.time.Clock()

    hits = 0
    clicks = 0
    misses = 0
    start_time = time.time()

    pygame.time.set_timer(TARGET_EVENT, TARGET_INCREMENT)

    while run:
        clock.tick(60)
        click = False
        mouse_position = pygame.mouse.get_pos()
        elapsed_time = time.time() - start_time
        remaining_time = max(TIME_LIMIT - elapsed_time, 0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == TARGET_EVENT:
                x = random.randint(TARGET_PADDING, WIDTH - TARGET_PADDING)
                y = random.randint(TARGET_PADDING + TopBarHeight, HEIGHT - TARGET_PADDING)
                targets.append(Target(x, y))
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = True
                clicks += 1


        hit_targets = set()
        if click:
            hit = False
            for target in targets:
                if target.collide(*mouse_position):
                    hit_targets.add(id(target))
                    hits += 1
                    hit = True
                    break
            if not hit:
                misses += 1

        targets = [t for t in targets if id(t) not in hit_targets]

        expired = [t for t in targets if t.is_expired()]
        for t in expired:
            misses += 1
        targets = [t for t in targets if not t.is_expired()]


        if Mode == "L" and misses >= LIVES:
            end_screen(Window, elapsed_time, hits, misses, clicks)
            run = False
        if Mode == "T" and remaining_time <= 0:
            end_screen(Window, TIME_LIMIT, hits, misses, clicks)
            run = False

        draw(Window, targets)
        draw_top_bar(Window, elapsed_time, remaining_time, hits, misses)
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()


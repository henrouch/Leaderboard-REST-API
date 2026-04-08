import math
import random
import time
import pygame


pygame.init()

WIDTH, HEIGHT = 800, 600  # Defines the dimensions of the game window
Window = pygame.display.set_mode((WIDTH, HEIGHT))  # Initialize a Pygame window
pygame.display.set_caption("Python Aim Trainer")  # Sets a title for the Pygame window
Size = 30
TARGET_INCREMENT = 1000  # The number of milliseconds before another target is created
TARGET_EVENT = pygame.USEREVENT  # Aids in the creation of a custom event in the game
TARGET_PADDING = 40  # Number of pixels the targets are spaced from the edge of the screen
BG_COLOR = (0, 25, 40)  # Background color
TIME_LIMIT = 30
LIVES = 3
TopBarHeight = 50
LABEL_FONT = pygame.font.SysFont("comicsans", 24)


invalid = True
while invalid:
    Mode = input("What mode do you want? (Timed(T) or Lives(L)):").upper()
    if Mode == "T":
        print("You have 30 seconds")
        invalid = False
    elif Mode == "L":
        print("You have 3 lives")
        invalid = False
    else:
        print("Invalid mode. Please choose Timed (T) or Lives (L).")
        Mode = input("What mode do you want? (Timed(T) or Lives(L)): ").upper()


# Defines the properties and behavior of each target in the game.
class Target:
    COLOR = "red"
    SECOND_COLOR = "white"
    max_time = TARGET_INCREMENT / 1000

    # Initializes a new target object with specified position, size, and creation time.
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = Size
        self.creation_time = time.time()  # Time when target was created

    # Draw the target
    def draw(self, Window):
        pygame.draw.circle(Window, self.COLOR, (self.x, self.y), self.size)
        pygame.draw.circle(Window, self.SECOND_COLOR, (self.x, self.y), self.size * 0.8)
        pygame.draw.circle(Window, self.COLOR, (self.x, self.y), self.size * 0.6)
        pygame.draw.circle(Window, self.SECOND_COLOR, (self.x, self.y), self.size * 0.4)

    # Checks if a point (x, y) is within the target's size, indicating a collision.
    def collide(self, x, y):
        distance = math.sqrt((self.x - x) ** 2 + (self.y - y) ** 2)
        return distance <= self.size

    # Checks whether the target has been on the screen for longer than its maximum allowed time.
    def is_expired(self):
        return time.time() - self.creation_time >= self.max_time

    # Cover the window with a background color and then draws each target in the targets list.


def draw(Window, targets):
    Window.fill(BG_COLOR)
    for target in targets:
        target.draw(Window)


# Formats the given time in seconds into "mm:ss.milli" (minutes:seconds.milliseconds).
def format_time(secs):
    milli = math.floor(
        int(secs * 1000 % 1000) / 100)  # Extracts the milliseconds (first 3 digits after the decimal point and rounds it to the nearest millisecond).
    seconds = int(round(secs % 60, 1))  # Extracts the seconds part (rounding to the nearest second).
    minutes = int(secs // 60)  # Extracts the minutes part.
    return f"{minutes:02d}:{seconds:02d}.{milli}"  # Returns the formatted time as "mm:ss.milli" (e.g., 02:15.3).Using :02d ensures that minutes and seconds are always two digit


# Draws the top bar of the window, displaying the game’s time, hits, lives, and misses based on the current mode.
def draw_top_bar(Window, elapsed_time, remaining_time, hits, misses):
    pygame.draw.rect(Window, "grey", (0, 0, WIDTH, TopBarHeight))  # Top bar background
    if Mode == "T":
        time_label = LABEL_FONT.render(f"Time: {format_time(remaining_time)} ", 1,
                                       "black")  # The 1 is an antialiasing flag and it helps make the text look smoother
        Window.blit(time_label, (5, 5))
    elif Mode == "L":
        time_label = LABEL_FONT.render(f"Time: {format_time(elapsed_time)} ", 1, "black")
        Window.blit(time_label, (5, 5))

    hits_label = LABEL_FONT.render(f"Hits: {hits}", 1, "black")
    Window.blit(hits_label, (450, 5))

    if Mode == "L":
        lives_label = LABEL_FONT.render(f"Lives: {LIVES - misses}", 1, "black")
        Window.blit(lives_label, (250, 5))
    else:
        lives_label = LABEL_FONT.render("", 1, "black")
        Window.blit(lives_label, (250, 5))

    misses_label = LABEL_FONT.render(f"Misses: {misses}", 1, "black")
    Window.blit(misses_label, (600, 5))

def send_score(username, hits, misses, elapsed_time):
    if hits + misses > 0:
        accuracy = round((hits / (hits + misses) * 100), 2)
    else:
        accuracy = 0

    data = {
        "username": username,
        "hits": hits,
        "misses": misses,
        "accuracy": accuracy,
        "time": round(elapsed_time, 2)
    }


# This function displays the end screen showing the user's performance metrics such as hits, misses, accuracy, and elapsed time.
def end_screen(Window, elapsed_time, hits, misses, clicks):
    Window.fill(BG_COLOR)

    hits_label = LABEL_FONT.render(f"Hits: {hits}", 1, "white")
    Window.blit(hits_label, (300, 200))

    misses_label = LABEL_FONT.render(f"Misses: {misses}", 1, "white")
    Window.blit(misses_label, (300, 250))

    accuracy = round((hits / (hits + misses) * 100), 2)
    accuracy_label = LABEL_FONT.render(f"Accuracy: {accuracy}%", 1, "white")
    Window.blit(accuracy_label, (300, 300))

    elapsed_time_label = LABEL_FONT.render(f"Time: {format_time(elapsed_time)}", 1, "white")
    Window.blit(elapsed_time_label, (300, 350))

    username = input("Enter your username: ")
    send_score(username, hits, misses, elapsed_time)

    pygame.display.update()

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

    pygame.time.set_timer(TARGET_EVENT,
                          TARGET_INCREMENT)  # Tells Pygame to trigger the custom event thus create a target everytime the custom event is triggered

    while run:
        clock.tick(60)
        click = False
        mouse_position = pygame.mouse.get_pos()  # Get mouse position
        elapsed_time = time.time() - start_time
        remaining_time = max(TIME_LIMIT - elapsed_time, 0)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == TARGET_EVENT:  # Trigger new target
                x = random.randint(TARGET_PADDING, WIDTH - TARGET_PADDING)
                y = random.randint(TARGET_PADDING + TopBarHeight, HEIGHT - TARGET_PADDING)
                target = Target(x, y)
                targets.append(target)
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = True
                clicks += 1

        # Remove expired targets and count misses for disappearing targets
        for target in targets:
            if target.is_expired():  # Target has disappeared
                targets.remove(target)
                if Mode == "L" or Mode =="T":  # Only count misses in Lives Mode
                    misses += 1

        for target in targets:
            if click and target.collide(*mouse_position):
                targets.remove(target)
                hits += 1
            elif click and not target.collide(*mouse_position):
                if Mode == "L" or Mode == "T":
                    misses += 1

        # Check for game-ending conditions
        if Mode == "L" and misses >= LIVES:
            end_screen(Window, elapsed_time, hits, misses, clicks)
            run = False
        if Mode == "T":
            if remaining_time <= 0:  # End game if time runs out
                end_screen(Window, TIME_LIMIT, hits, misses, clicks)
                run = False

        # Draw the screen
        draw(Window, targets)
        draw_top_bar(Window, elapsed_time, remaining_time, hits, misses)
        pygame.display.update()

    pygame.quit()


if __name__ == "__main__":
    main()

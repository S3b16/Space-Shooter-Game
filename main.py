import pygame
import random
import math
import time
import pygame.gfxdraw  # Add this import for drawing transparent rectangles
import json

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer

# Set up the game window
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Space Shooter")

# Fullscreen flag
fullscreen = False

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Load background image
background = pygame.image.load('galaxy.png')
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Load sounds
laser_sound = pygame.mixer.Sound('laser.wav')
background_music = pygame.mixer.Sound('background.wav')
explosion_sound = pygame.mixer.Sound('explosion.wav')

# PowerUp class
class PowerUp(pygame.sprite.Sprite):
    def __init__(self, power_type):
        super().__init__()
        self.power_type = power_type
        if power_type == 'triple':
            self.image = pygame.image.load('gold.png')
        elif power_type == 'spread':
            self.image = pygame.image.load('silver.png')
        else:  # invincible
            self.image = pygame.image.load('bronze.png')
        self.image = pygame.transform.scale(self.image, (30, 30))  # Adjust size as needed
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.bottom = 0  # Start just above the top of the screen
        self.speedy = 2  # Adjust speed as needed

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('ship.png')
        self.image = pygame.transform.scale(self.image, (50, 50))  # Adjust size as needed
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.velocity_x = 0
        self.velocity_y = 0
        self.acceleration = 0.5
        self.max_speed = 5
        self.friction = 0.9
        self.triple_shot = False
        self.triple_shot_end = 0
        self.spread_shot = False
        self.spread_shot_end = 0
        self.invincible = False
        self.invincible_end = 0
        self.lives = 3  # Add this line to give the player 3 lives
        self.original_image = self.image.copy()  # Store the original image

        # Load thruster effect
        self.thruster_image = pygame.image.load('effect.png')
        self.thruster_image = pygame.transform.scale(self.thruster_image, (30, 30))  # Adjust size as needed
        self.thruster_rect = self.thruster_image.get_rect()
        self.is_moving = False

        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = 250  # Delay between shots in milliseconds

    def update(self):
        # Get the pressed keys
        keys = pygame.key.get_pressed()
        
        # Apply acceleration based on key presses
        if keys[pygame.K_LEFT]:
            self.velocity_x -= self.acceleration
        if keys[pygame.K_RIGHT]:
            self.velocity_x += self.acceleration
        if keys[pygame.K_UP]:
            self.velocity_y -= self.acceleration
        if keys[pygame.K_DOWN]:
            self.velocity_y += self.acceleration
        
        # Apply friction
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction
        
        # Limit speed
        speed = math.sqrt(self.velocity_x**2 + self.velocity_y**2)
        if speed > self.max_speed:
            factor = self.max_speed / speed
            self.velocity_x *= factor
            self.velocity_y *= factor
        
        # Update position
        self.rect.x += int(self.velocity_x)
        self.rect.y += int(self.velocity_y)
        
        # Constrain to screen
        self.constrain_to_screen()

        # Check if moving
        self.is_moving = self.velocity_x != 0 or self.velocity_y != 0

        # Update thruster position
        self.thruster_rect.centerx = self.rect.centerx
        self.thruster_rect.top = self.rect.bottom

        # Check if power-ups have expired
        current_time = time.time()
        if self.triple_shot and current_time > self.triple_shot_end:
            self.triple_shot = False
        if self.spread_shot and current_time > self.spread_shot_end:
            self.spread_shot = False
        if self.invincible and current_time > self.invincible_end:
            self.invincible = False

        # Shooting
        if keys[pygame.K_SPACE]:
            self.shoot()

    def constrain_to_screen(self):
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > screen.get_width():
            self.rect.right = screen.get_width()
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > screen.get_height():
            self.rect.bottom = screen.get_height()

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            if self.spread_shot:
                self.shoot_spread()
            elif self.triple_shot:
                self.shoot_triple()
            else:
                self.shoot_single()

    def shoot_single(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)
        laser_sound.play()

    def shoot_triple(self):
        bullet1 = Bullet(self.rect.left, self.rect.top)
        bullet2 = Bullet(self.rect.centerx, self.rect.top)
        bullet3 = Bullet(self.rect.right, self.rect.top)
        all_sprites.add(bullet1, bullet2, bullet3)
        bullets.add(bullet1, bullet2, bullet3)
        laser_sound.play()

    def shoot_spread(self):
        angles = [-30, -15, 0, 15, 30]
        for angle in angles:
            bullet = SpreadBullet(self.rect.centerx, self.rect.top, angle)
            all_sprites.add(bullet)
            bullets.add(bullet)
        laser_sound.play()

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.is_moving:
            surface.blit(self.thruster_image, self.thruster_rect)

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type):
        super().__init__()
        self.enemy_type = enemy_type
        if enemy_type == 'normal':
            self.image = pygame.image.load('enemy.png')
        else:  # alien
            self.image = pygame.image.load('alien.png')
        self.image = pygame.transform.scale(self.image, (30, 30))  # Adjust size as needed
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.randrange(1, 8)
        self.speedx = random.randrange(-3, 3)
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = random.randint(1000, 3000)  # Random delay between shots
        self.collision_rect = self.rect.inflate(-10, -10)  # Smaller collision box

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WIDTH + 20:
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 8)

        # Shooting logic
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now
            self.shoot_delay = random.randint(1000, 3000)  # Reset the delay

        self.collision_rect.center = self.rect.center  # Update collision box position

    def shoot(self):
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom)
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)

    def draw_collision_box(self, surface):
        # Draw a semi-transparent red rectangle for the collision box
        s = pygame.Surface((self.collision_rect.width, self.collision_rect.height), pygame.SRCALPHA)
        pygame.gfxdraw.box(s, s.get_rect(), (255, 0, 0, 128))
        surface.blit(s, self.collision_rect)

# EnemyBullet class
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load('red_missile.png')
        self.image = pygame.transform.scale(self.image, (10, 20))  # Adjust size as needed
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speedy = 5

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load('blue_missile.png')
        self.image = pygame.transform.scale(self.image, (10, 30))  # Adjust size as needed
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10
        self.trail_timer = 0
        self.trail_delay = 2  # Adjust this to control trail density

    def update(self):
        self.rect.y += self.speedy
        self.trail_timer += 1
        if self.trail_timer >= self.trail_delay:
            self.create_trail()
            self.trail_timer = 0
        if self.rect.bottom < 0:
            self.kill()

    def create_trail(self):
        trail = BulletTrail(self.rect.centerx, self.rect.bottom)
        all_sprites.add(trail)
        bullet_trails.add(trail)

# SpreadBullet class
class SpreadBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.image.load('blue_missile.png')
        self.image = pygame.transform.scale(self.image, (10, 30))
        self.original_image = self.image
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speed = 10
        self.angle = math.radians(angle)
        self.image = pygame.transform.rotate(self.original_image, -math.degrees(self.angle))

    def update(self):
        self.rect.x += self.speed * math.sin(self.angle)
        self.rect.y -= self.speed * math.cos(self.angle)
        if self.rect.bottom < 0 or self.rect.top > HEIGHT or self.rect.left < 0 or self.rect.right > WIDTH:
            self.kill()

# BulletTrail class
class BulletTrail(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.image.load('effects.png')
        self.image = pygame.transform.scale(self.image, (20, 20))  # Adjust size as needed
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.alpha = 255
        self.fade_speed = 15

    def update(self):
        self.alpha -= self.fade_speed
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.alpha)

# Create sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()  # New group for enemy bullets
powerups = pygame.sprite.Group()
bullet_trails = pygame.sprite.Group()

# Create player
player = Player()
all_sprites.add(player)

# Score and Lives
score = 0
font = pygame.font.Font(None, 36)

# Start playing background music
background_music.play(-1)  # -1 means loop indefinitely

# Add a global variable to control collision box visibility
show_collision_boxes = False

# Function to handle screen resizing
def handle_resize(width, height):
    global WIDTH, HEIGHT
    WIDTH = width
    HEIGHT = height
    # Resize the background
    global background
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
    # Reposition the player
    player.rect.bottom = HEIGHT - 10
    player.rect.centerx = WIDTH // 2

# Function to load high scores
def load_high_scores():
    try:
        with open('high_scores.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Function to save high scores
def save_high_scores(scores):
    with open('high_scores.json', 'w') as f:
        json.dump(scores, f)

# Function to update high scores
def update_high_scores(score):
    scores = load_high_scores()
    scores.append({"score": score, "date": time.strftime("%Y-%m-%d %H:%M:%S")})
    scores.sort(key=lambda x: x["score"], reverse=True)
    scores = scores[:5]  # Keep only top 5 scores
    save_high_scores(scores)

# Function to display high scores
def display_high_scores(screen):
    scores = load_high_scores()
    y = 100
    screen.blit(font.render("High Scores:", True, WHITE), (WIDTH // 2 - 50, y))
    y += 50
    for i, score in enumerate(scores, 1):
        text = f"{i}. {score['score']} - {score['date']}"
        screen.blit(font.render(text, True, WHITE), (WIDTH // 2 - 100, y))
        y += 30

# Constants for minimap
MINIMAP_SIZE = 100
MINIMAP_MARGIN = 10
MINIMAP_ALPHA = 128  # Transparency of the minimap

# Function to draw the minimap
def draw_minimap(screen, player, enemies, powerups):
    # Create a surface for the minimap
    minimap = pygame.Surface((MINIMAP_SIZE, MINIMAP_SIZE))
    minimap.fill((50, 50, 50))  # Dark gray background
    
    # Calculate scale factors
    scale_x = MINIMAP_SIZE / WIDTH
    scale_y = MINIMAP_SIZE / HEIGHT
    
    # Draw player (white dot)
    pygame.draw.circle(minimap, WHITE, 
                       (int(player.rect.centerx * scale_x), 
                        int(player.rect.centery * scale_y)), 2)
    
    # Draw enemies (red dots)
    for enemy in enemies:
        pygame.draw.circle(minimap, RED, 
                           (int(enemy.rect.centerx * scale_x), 
                            int(enemy.rect.centery * scale_y)), 1)
    
    # Draw powerups (yellow dots)
    for powerup in powerups:
        pygame.draw.circle(minimap, YELLOW, 
                           (int(powerup.rect.centerx * scale_x), 
                            int(powerup.rect.centery * scale_y)), 1)
    
    # Draw border around minimap
    pygame.draw.rect(minimap, WHITE, minimap.get_rect(), 1)
    
    # Create a transparent surface
    transparent_surface = pygame.Surface((MINIMAP_SIZE, MINIMAP_SIZE), pygame.SRCALPHA)
    transparent_surface.fill((255, 255, 255, MINIMAP_ALPHA))
    
    # Blit the minimap onto the transparent surface
    transparent_surface.blit(minimap, (0, 0))
    
    # Blit the transparent surface onto the main screen
    screen.blit(transparent_surface, (screen.get_width() - MINIMAP_SIZE - MINIMAP_MARGIN, 
                                      screen.get_height() - MINIMAP_SIZE - MINIMAP_MARGIN))

# Game loop
running = True
game_over = False
show_high_scores = False
clock = pygame.time.Clock()

# Add these variables after initializing pygame
powerup_spawn_time = 0
powerup_spawn_delay = 10  # Spawn a power-up every 10 seconds

while running:
    if game_over:
        # Update high scores
        update_high_scores(score)
        
        # Display game over screen and high scores
        screen.fill(BLACK)
        game_over_text = font.render("Game Over! Press R to restart or H for high scores", True, WHITE)
        screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))
        
        if show_high_scores:
            display_high_scores(screen)
        
        pygame.display.flip()

        # Wait for player input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Reset game state
                    player.lives = 3
                    score = 0
                    game_over = False
                    show_high_scores = False
                    # Clear all sprites and recreate the player
                    all_sprites.empty()
                    enemies.empty()
                    bullets.empty()
                    enemy_bullets.empty()
                    powerups.empty()
                    player = Player()
                    all_sprites.add(player)
                elif event.key == pygame.K_h:
                    show_high_scores = not show_high_scores
        continue

    # Keep loop running at the right speed
    clock.tick(60)
    
    # Process input (events)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                show_collision_boxes = not show_collision_boxes  # Toggle collision box visibility
            elif event.key == pygame.K_MINUS:
                # Reduce collision box size
                for enemy in enemies:
                    enemy.collision_rect = enemy.collision_rect.inflate(-2, -2)
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                # Increase collision box size
                for enemy in enemies:
                    enemy.collision_rect = enemy.collision_rect.inflate(2, 2)
            elif event.key == pygame.K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                handle_resize(screen.get_width(), screen.get_height())
        elif event.type == pygame.VIDEORESIZE:
            if not fullscreen:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                handle_resize(event.w, event.h)

    # Update
    all_sprites.update()
    enemy_bullets.update()
    bullet_trails.update()

    # Spawn enemies
    if random.random() < 0.02:
        enemy_type = random.choice(['normal', 'alien'])
        enemy = Enemy(enemy_type)
        all_sprites.add(enemy)
        enemies.add(enemy)  

    # Spawn power-ups consistently
    current_time = time.time()
    if current_time - powerup_spawn_time > powerup_spawn_delay:
        powerup_spawn_time = current_time
        power_types = ['triple', 'spread', 'invincible']
        for power_type in power_types:
            powerup = PowerUp(power_type)
            all_sprites.add(powerup)
            powerups.add(powerup)

    # Check for collisions (using groupcollide for efficiency)
    # Player bullets hitting enemies
    hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
    for hit in hits:
        score += 10
        explosion_sound.play()
        enemy = Enemy(random.choice(['normal', 'alien']))
        all_sprites.add(enemy)
        enemies.add(enemy)

    # Enemy bullets hitting player bullets (they cancel out)
    pygame.sprite.groupcollide(bullets, enemy_bullets, True, True)

    # Player getting hit by enemy bullets
    if not player.invincible:
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
        if hits:
            explosion_sound.play()
            player.lives -= 1
            if player.lives <= 0:
                game_over = True
            else:
                player.rect.centerx = WIDTH // 2
                player.rect.bottom = HEIGHT - 10

    # Player colliding with enemies
    if not player.invincible:
        hits = pygame.sprite.spritecollide(player, enemies, False, pygame.sprite.collide_circle)
        if hits:
            explosion_sound.play()
            player.lives -= 1
            if player.lives <= 0:
                game_over = True
            else:
                player.rect.centerx = WIDTH // 2
                player.rect.bottom = HEIGHT - 10
                for enemy in hits:
                    enemy.kill()

    # Player collecting powerups
    hits = pygame.sprite.spritecollide(player, powerups, True)
    for hit in hits:
        if hit.power_type == 'triple':
            player.triple_shot = True
            player.triple_shot_end = time.time() + 5
        elif hit.power_type == 'spread':
            player.spread_shot = True
            player.spread_shot_end = time.time() + 5
        elif hit.power_type == 'invincible':
            player.invincible = True
            player.invincible_end = time.time() + 3

    # Draw / render
    screen.blit(background, (0, 0))  # Draw the background
    for sprite in all_sprites:
        if isinstance(sprite, Player):
            sprite.draw(screen)
        else:
            screen.blit(sprite.image, sprite.rect)
    enemy_bullets.draw(screen)  # Ensure enemy bullets are drawn
    powerups.draw(screen)  # Ensure power-ups are drawn
    bullet_trails.draw(screen)
    
    # Draw score and lives
    score_text = font.render(f"Score: {score}", True, WHITE)
    lives_text = font.render(f"Lives: {player.lives}", True, WHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (10, 50))

    # Visual indicator for active power-ups
    if player.triple_shot:
        pygame.draw.circle(screen, GREEN, (WIDTH - 20, 20), 10)
    if player.spread_shot:
        pygame.draw.circle(screen, YELLOW, (WIDTH - 40, 20), 10)
    if player.invincible:
        pygame.draw.circle(screen, RED, (WIDTH - 60, 20), 10)

    # Draw enemy collision boxes if enabled
    if show_collision_boxes:
        for enemy in enemies:
            enemy.draw_collision_box(screen)

    # Draw minimap
    draw_minimap(screen, player, enemies, powerups)

    # Flip the display
    pygame.display.flip()

# Quit the game
pygame.quit()
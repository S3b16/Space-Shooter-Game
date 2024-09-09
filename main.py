import pygame
import random
import math
import time

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer

# Set up the game window
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")

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
    def __init__(self, color, power_type):
        super().__init__()
        self.image = pygame.Surface((30, 30))  # Increased from 20x20 to 30x30
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = -self.rect.height
        self.speedy = 1  # Decreased from 2 to 1
        self.power_type = power_type

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('arcade.png')
        self.image = pygame.transform.scale(self.image, (50, 50))  # Adjust size as needed
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.speed = 5
        self.triple_shot = False
        self.triple_shot_end = 0
        self.spread_shot = False
        self.spread_shot_end = 0
        self.invincible = False
        self.invincible_end = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < HEIGHT:
            self.rect.y += self.speed

        # Check if power-ups have expired
        current_time = time.time()
        if self.triple_shot and current_time > self.triple_shot_end:
            self.triple_shot = False
        if self.spread_shot and current_time > self.spread_shot_end:
            self.spread_shot = False
        if self.invincible and current_time > self.invincible_end:
            self.invincible = False

    def shoot(self):
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
        self.speedy = random.uniform(0.5, 3)  # Start with slower speeds
        self.speedx = random.uniform(-1, 1)
        self.movement_type = random.choice(['straight', 'zigzag', 'swoop'])
        self.angle = 0
        self.amplitude = random.randrange(20, 50)
        self.frequency = random.uniform(0.02, 0.05)
        self.acceleration = random.uniform(0.001, 0.005)  # Speed increase per frame
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = random.randint(1000, 3000)  # Random delay between shots

    def update(self):
        # Gradually increase speed  
        self.speedy += self.acceleration
        self.speedx += self.acceleration * 0.5  # Increase horizontal speed more slowly

        if self.movement_type == 'straight':
            self.rect.y += self.speedy
            self.rect.x += self.speedx
        elif self.movement_type == 'zigzag':
            self.rect.y += self.speedy
            self.rect.x += self.amplitude * math.sin(self.angle) * (self.speedx / 2)
            self.angle += self.frequency
        elif self.movement_type == 'swoop':
            self.rect.y += self.speedy
            self.rect.x += self.amplitude * math.sin(self.angle) * self.speedx
            self.angle += self.frequency
            self.speedy += 0.05  # Additional acceleration for swoop

        # Cap the maximum speed
        max_speed = 8
        self.speedy = min(self.speedy, max_speed)
        self.speedx = min(max(self.speedx, -max_speed), max_speed)

        # Wrap around screen edges
        if self.rect.top > HEIGHT + 10 or self.rect.left < -25 or self.rect.right > WIDTH + 20:
            self.reset()

        # Shooting logic
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.shoot()
            self.last_shot = now
            self.shoot_delay = random.randint(1000, 3000)  # Reset the delay

    def reset(self):
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.uniform(0.5, 3)  # Reset to initial slower speed
        self.speedx = random.uniform(-1, 1)
        self.movement_type = random.choice(['straight', 'zigzag', 'swoop'])
        self.angle = 0
        self.amplitude = random.randrange(20, 50)
        self.frequency = random.uniform(0.02, 0.05)
        self.acceleration = random.uniform(0.001, 0.005)
        self.enemy_type = random.choice(['normal', 'alien'])
        if self.enemy_type == 'normal':
            self.image = pygame.image.load('enemy.png')
        else:  # alien
            self.image = pygame.image.load('alien.png')
        self.image = pygame.transform.scale(self.image, (30, 30))  # Adjust size as needed

    def shoot(self):
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom)
        all_sprites.add(bullet)
        enemy_bullets.add(bullet)

# EnemyBullet class
class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 20))  # Increased size from (5, 10) to (10, 20)
        self.image.fill(RED)
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
        self.image = pygame.image.load('bullet.png')
        self.image = pygame.transform.scale(self.image, (10, 20))  # Adjust size as needed
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()

# SpreadBullet class
class SpreadBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        self.image = pygame.image.load('bullet.png')
        self.image = pygame.transform.scale(self.image, (10, 20))
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speed = 10
        self.angle = math.radians(angle)

    def update(self):
        self.rect.x += self.speed * math.sin(self.angle)
        self.rect.y -= self.speed * math.cos(self.angle)
        if self.rect.bottom < 0 or self.rect.top > HEIGHT or self.rect.left < 0 or self.rect.right > WIDTH:
            self.kill()

# Create sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
enemy_bullets = pygame.sprite.Group()  # New group for enemy bullets
powerups = pygame.sprite.Group()

# Create player
player = Player()
all_sprites.add(player)

# Score
score = 0
font = pygame.font.Font(None, 36)

# Start playing background music
background_music.play(-1)  # -1 means loop indefinitely

# Game loop
running = True
clock = pygame.time.Clock()

while running:
    # Keep loop running at the right speed
    clock.tick(60)
    
    # Process input (events)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    # Update
    all_sprites.update()

    # Spawn enemies
    if random.random() < 0.02:
        enemy_type = random.choice(['normal', 'alien'])
        enemy = Enemy(enemy_type)
        all_sprites.add(enemy)
        enemies.add(enemy)  

    # Spawn power-ups
    if random.random() < 0.003:  # Adjust this value to change power-up frequency
        power_type = random.choice(['triple', 'spread', 'invincible'])
        if power_type == 'triple':
            color = GREEN
        elif power_type == 'spread':
            color = YELLOW
        else:  # invincible
            color = RED
        powerup = PowerUp(color, power_type)
        all_sprites.add(powerup)
        powerups.add(powerup)

    # Check for bullet-enemy collisions
    hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
    for hit in hits:
        score += 10
        explosion_sound.play()  # Play explosion sound
        enemy = Enemy(random.choice(['normal', 'alien']))
        all_sprites.add(enemy)
        enemies.add(enemy)

    # Check for bullet-enemy bullet collisions
    pygame.sprite.groupcollide(bullets, enemy_bullets, True, True)

    # Check for player-enemy bullet collisions
    if not player.invincible:
        hits = pygame.sprite.spritecollide(player, enemy_bullets, True)
        if hits:
            explosion_sound.play()  # Play explosion sound
            running = False

    # Check for player-enemy collisions
    if not player.invincible:
        hits = pygame.sprite.spritecollide(player, enemies, False)
        if hits:
            explosion_sound.play()  # Play explosion sound
            running = False

    # Check for player-powerup collisions
    hits = pygame.sprite.spritecollide(player, powerups, True)
    for hit in hits:
        if hit.power_type == 'triple':
            player.triple_shot = True
            player.triple_shot_end = time.time() + 5  # Triple Shot lasts for 5 seconds
        elif hit.power_type == 'spread':
            player.spread_shot = True
            player.spread_shot_end = time.time() + 5  # Spread Shot lasts for 5 seconds
        elif hit.power_type == 'invincible':
            player.invincible = True
            player.invincible_end = time.time() + 3  # Invincibility lasts for 3 seconds

    # Draw / render
    screen.blit(background, (0, 0))  # Draw the background
    all_sprites.draw(screen)
    enemy_bullets.draw(screen)  # Ensure enemy bullets are drawn
    powerups.draw(screen)  # Ensure power-ups are drawn
    
    # Draw score
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    # Visual indicator for active power-ups
    if player.triple_shot:
        pygame.draw.circle(screen, GREEN, (WIDTH - 20, 20), 10)
    if player.spread_shot:
        pygame.draw.circle(screen, YELLOW, (WIDTH - 40, 20), 10)
    if player.invincible:
        pygame.draw.circle(screen, RED, (WIDTH - 60, 20), 10)

    # Flip the display
    pygame.display.flip()

# Quit the game
pygame.quit()  
import os
import sys
import math
import random
import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

def draw_text_center(surface, text, size, color, y_offset=0):
    font = pygame.font.SysFont("arial", size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 + y_offset))
    surface.blit(text_surface, text_rect)

class ObjectPool:
    """Object pooling for particles and sparks to reduce memory allocation"""
    def __init__(self, obj_class, initial_size=50):
        self.obj_class = obj_class
        self.available = []
        self.in_use = []
        
        # Pre-allocate objects
        for _ in range(initial_size):
            obj = obj_class.__new__(obj_class)
            self.available.append(obj)
    
    def get(self, *args, **kwargs):
        if self.available:
            obj = self.available.pop()
            obj.__init__(*args, **kwargs)
        else:
            obj = self.obj_class(*args, **kwargs)
        
        self.in_use.append(obj)
        return obj
    
    def release(self, obj):
        if obj in self.in_use:
            self.in_use.remove(obj)
            self.available.append(obj)
    
    def update_and_render(self, display, offset):
        """Update all objects and automatically release dead ones"""
        for obj in self.in_use[:]:  # Copy list to avoid modification during iteration
            kill = obj.update()
            obj.render(display, offset=offset)
            if kill:
                self.release(obj)

class Game:
    def __init__(self, level_id=0, fullscreen=False):
        pygame.init()
        pygame.display.set_caption('Ninja Game - Optimized')
        self.fullscreen = fullscreen
        
        # Initialize display with better error handling
        try:
            if fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
            else:
                self.screen = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
        except pygame.error as e:
            print(f"Display initialization failed: {e}")
            self.screen = pygame.display.set_mode((640, 480))
        
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()
        self.movement = [False, False]
        self.paused = False
        
        # Load assets with error handling
        self.load_assets()
        self.load_sounds()
        
        # Initialize object pools for better performance
        self.particle_pool = ObjectPool(Particle, 100)
        self.spark_pool = ObjectPool(Spark, 50)
        
        # Compatibility attributes for old code (if any scripts still reference them)
        self.sparks = []
        self.particles = []
        
        # Game state
        try:
            self.clouds = Clouds(self.assets.get('clouds', []), count=16)
        except:
            self.clouds = None
            
        self.player = Player(self, (50, 50), (8, 15))
        self.tilemap = Tilemap(self, tile_size=16)
        self.level = level_id
        self.total_levels = 4  # Updated to reflect actual number of levels
        self.screenshake = 0
        
        # Performance tracking
        self.frame_count = 0
        self.fps_counter = 0
        self.last_fps_update = pygame.time.get_ticks()
        
        # Load the initial level
        self.load_level(self.level)
    
    def load_assets(self):
        """Load game assets with error handling"""
        try:
            self.assets = {
                'decor': load_images('tiles/decor'),
                'grass': load_images('tiles/grass'),
                'large_decor': load_images('tiles/large_decor'),
                'stone': load_images('tiles/stone'),
                'player': load_image('entities/player.png'),
                'background': load_image('background.png'),
                'clouds': load_images('clouds'),
                'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
                'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
                'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
                'player/run': Animation(load_images('entities/player/run'), img_dur=4),
                'player/jump': Animation(load_images('entities/player/jump')),
                'player/slide': Animation(load_images('entities/player/slide')),
                'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
                'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
                'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
                'gun': load_image('gun.png'),
                'projectile': load_image('projectile.png'),
            }
        except Exception as e:
            print(f"Error loading assets: {e}")
            # Create minimal fallback assets
            self.assets = {}
    
    def load_sounds(self):
        """Load sound effects with error handling"""
        try:
            self.sfx = {
                'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
                'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
                'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
                'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
                'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
            }
            
            # Set volumes
            self.sfx['ambience'].set_volume(0.2)
            self.sfx['shoot'].set_volume(0.4)
            self.sfx['hit'].set_volume(0.8)
            self.sfx['dash'].set_volume(0.3)
            self.sfx['jump'].set_volume(0.7)
        except Exception as e:
            print(f"Error loading sounds: {e}")
            self.sfx = {}
    
    def load_level(self, map_id):
        """Load level from file only - no auto generation"""
        level_loaded = False
        
        # Try to load from file
        try:
            self.tilemap.load(f'data/maps/{map_id}.json')
            level_loaded = True
            print(f"Successfully loaded level {map_id}")
        except FileNotFoundError:
            print(f"Level {map_id}.json not found")
        except Exception as e:
            print(f"Error loading level {map_id}: {e}")
        
        # If loading failed, try to load level 0 as fallback
        if not level_loaded and map_id != 0:
            try:
                self.tilemap.load('data/maps/0.json')
                level_loaded = True
                print("Loaded fallback level 0")
            except:
                print("Could not load fallback level 0")
        
        # If still no level loaded, create empty level
        if not level_loaded:
            print("Creating empty level")
            self.tilemap.tilemap = {}
            self.tilemap.offgrid_tiles = []
            # Add basic player spawn
            self.tilemap.offgrid_tiles.append({
                "type": "spawners",
                "variant": 0,
                "pos": [80, 100]
            })
        
        self.setup_level()
    
    def setup_level(self):
        """Setup level entities after loading tilemap"""
        # Find leaf spawners
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))
        
        # Setup enemies and player
        self.enemies = []
        player_spawned = False
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = list(spawner['pos'])  # Ensure it's a list
                self.player.air_time = 0
                player_spawned = True
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))
        
        # If no player spawn found, place at default position
        if not player_spawned:
            self.player.pos = [80, 100]
            self.player.air_time = 0
        
        # Reset game state
        self.projectiles = []
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        
        # Clear object pools
        self.particle_pool.available.extend(self.particle_pool.in_use)
        self.particle_pool.in_use.clear()
        self.spark_pool.available.extend(self.spark_pool.in_use)
        self.spark_pool.in_use.clear()
    
    def pause_menu(self):
        """Enhanced pause menu with modern UI"""
        try:
            from UI import create_enhanced_pause_menu
            result = create_enhanced_pause_menu(self)
            if result == 'main_menu':
                return 'main_menu'
            elif result == 'resume':
                return 'resume'
            else:
                return self.pause_menu()
        except ImportError:
            # Fallback simple pause menu
            return self.simple_pause_menu()
    
    def simple_pause_menu(self):
        """Simple fallback pause menu"""
        paused = True
        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        paused = False
                    elif event.key == pygame.K_q:
                        return 'main_menu'
            
            self.screen.fill((0, 0, 0))
            draw_text_center(self.screen, "PAUSED", 48, (255, 255, 255), -50)
            draw_text_center(self.screen, "ESC - Resume", 24, (255, 255, 255), 0)
            draw_text_center(self.screen, "Q - Main Menu", 24, (255, 255, 255), 30)
            pygame.display.update()
            self.clock.tick(60)
        
        return 'resume'
    
    def update_fps_counter(self):
        """Update FPS counter for performance monitoring"""
        current_time = pygame.time.get_ticks()
        self.frame_count += 1
        
        if current_time - self.last_fps_update >= 1000:
            self.fps_counter = self.frame_count
            self.frame_count = 0
            self.last_fps_update = current_time
    
    def spawn_particle(self, particle_type, pos, **kwargs):
        """Optimized particle spawning using object pool"""
        return self.particle_pool.get(self, particle_type, pos, **kwargs)
    
    def spawn_spark(self, pos, angle, speed):
        """Optimized spark spawning using object pool"""
        return self.spark_pool.get(pos, angle, speed)
    
    def run(self):
        # Load and play music
        try:
            pygame.mixer.music.load('data/music.wav')
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
            if 'ambience' in self.sfx:
                self.sfx['ambience'].play(-1)
        except:
            pass  # Continue without music if files not found
        
        running = True
        while running:
            # Clear screen
            self.screen.fill((0, 0, 0))
            self.display.fill((0, 0, 0, 0))
            
            if 'background' in self.assets:
                self.display_2.blit(self.assets['background'], (0, 0))
            
            # Update performance counter
            self.update_fps_counter()
            
            # Game logic
            self.screenshake = max(0, self.screenshake - 1)
            
            # Level progression
            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    if self.level >= self.total_levels - 1:
                        # Victory condition - could return to main menu or show victory screen
                        print("Game Complete!")
                        running = False
                    else:
                        self.level += 1
                        self.load_level(self.level)
            
            if self.transition < 0:
                self.transition += 1
            
            # Death handling
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)
            
            # Camera follow
            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            # Spawn particles (optimized)
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.spawn_particle('leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20))
            
            # Update and render
            if self.clouds:
                self.clouds.update()
                self.clouds.render(self.display_2, offset=render_scroll)
            
            self.tilemap.render(self.display, offset=render_scroll)
            
            # Update enemies
            for enemy in self.enemies[:]:  # Copy list to avoid modification issues
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)
            
            # Update player
            if not self.dead:
                self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset=render_scroll)
            
            # Update projectiles
            projectiles_to_remove = []
            for projectile in self.projectiles:
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                
                if 'projectile' in self.assets:
                    img = self.assets['projectile']
                    self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0],
                                          projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
                
                # Projectile collision
                if self.tilemap.solid_check(projectile[0]):
                    projectiles_to_remove.append(projectile)
                    for i in range(4):
                        self.spawn_spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random())
                elif projectile[2] > 360:
                    projectiles_to_remove.append(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        projectiles_to_remove.append(projectile)
                        self.dead += 1
                        if 'hit' in self.sfx:
                            self.sfx['hit'].play()
                        self.screenshake = max(16, self.screenshake)
                        
                        # Death effects
                        for i in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.spawn_spark(self.player.rect().center, angle, 2 + random.random())
                            self.spawn_particle('particle', self.player.rect().center,
                                              velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                       math.sin(angle + math.pi) * speed * 0.5],
                                              frame=random.randint(0, 7))
            
            # Remove projectiles after iteration
            for projectile in projectiles_to_remove:
                self.projectiles.remove(projectile)            
            # Update object pools (particles and sparks)
            self.particle_pool.update_and_render(self.display, render_scroll)
            self.spark_pool.update_and_render(self.display, render_scroll)
            
            # Create silhouette effect
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset)
            
            # Apply leaf movement
            for particle in self.particle_pool.in_use:
                if hasattr(particle, 'type') and particle.type == 'leaf':
                    if hasattr(particle, 'animation') and hasattr(particle.animation, 'frame'):
                        particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        result = self.pause_menu()
                        if result == 'main_menu':
                            return
                    elif event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    elif event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    elif event.key == pygame.K_UP:
                        if self.player.jump():
                            if 'jump' in self.sfx:
                                self.sfx['jump'].play()
                    elif event.key == pygame.K_x:
                        self.player.dash()
                    elif event.key == pygame.K_F11:  # Toggle fullscreen
                        self.fullscreen = not self.fullscreen
                        if self.fullscreen:
                            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        else:
                            self.screen = pygame.display.set_mode((1080, 720), pygame.RESIZABLE)
                
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    elif event.key == pygame.K_RIGHT:
                        self.movement[1] = False
            
            # Transition effect
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255),
                                 (self.display.get_width() // 2, self.display.get_height() // 2),
                                 (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
            
            self.display_2.blit(self.display, (0, 0))
            
            # Enhanced scaling with better performance
            screen_size = self.screen.get_size()
            aspect_ratio = 320 / 240
            screen_aspect = screen_size[0] / screen_size[1]
            
            if screen_aspect > aspect_ratio:
                scaled_height = screen_size[1]
                scaled_width = int(scaled_height * aspect_ratio)
                offset_x = (screen_size[0] - scaled_width) // 2
                offset_y = 0
            else:
                scaled_width = screen_size[0]
                scaled_height = int(scaled_width / aspect_ratio)
                offset_x = 0
                offset_y = (screen_size[1] - scaled_height) // 2
            
            # Use faster scaling for better performance
            scaled_display = pygame.transform.scale(self.display_2, (scaled_width, scaled_height))
            
            # Apply screenshake
            screenshake_offset = (0, 0)
            if self.screenshake > 0:
                screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,
                                    random.random() * self.screenshake - self.screenshake / 2)
            
            self.screen.blit(scaled_display, (offset_x + screenshake_offset[0], offset_y + screenshake_offset[1]))
            
            # Draw FPS counter (optional, for debugging)
            if hasattr(self, 'fps_counter'):
                font = pygame.font.SysFont("arial", 24)
                fps_text = font.render(f"FPS: {self.fps_counter}", True, (255, 255, 0))
                self.screen.blit(fps_text, (10, 10))
            
            pygame.display.update()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
    
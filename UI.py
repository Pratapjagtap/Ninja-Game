import pygame 
import sys
import math
import random
from pygame.locals import *
from game import Game

pygame.init()
pygame.mixer.init()

class UITheme:
    """Modern UI theme with cyberpunk/ninja aesthetics"""
    # Colors
    PRIMARY = (0, 255, 157)  # Bright cyan-green
    SECONDARY = (255, 0, 128)  # Hot pink
    ACCENT = (255, 215, 0)  # Gold
    BACKGROUND = (10, 15, 30)  # Dark blue
    SURFACE = (20, 25, 40)  # Slightly lighter
    TEXT_PRIMARY = (255, 255, 255)
    TEXT_SECONDARY = (180, 180, 200)
    SHADOW = (0, 0, 0, 100)
    GLOW = (0, 255, 157, 50)
    
    # Gradients
    BUTTON_GRADIENT = [(40, 45, 70), (60, 70, 100)]
    HOVER_GRADIENT = [(80, 90, 130), (100, 110, 150)]

class ParticleSystem:
    """Animated background particles for visual flair"""
    def __init__(self, screen_size):
        self.particles = []
        self.screen_size = screen_size
        for _ in range(50):
            self.add_particle()
    
    def add_particle(self):
        self.particles.append({
            'pos': [random.randint(0, self.screen_size[0]), random.randint(0, self.screen_size[1])],
            'vel': [random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5)],
            'size': random.randint(1, 3),
            'color': random.choice([UITheme.PRIMARY, UITheme.SECONDARY, UITheme.ACCENT]),
            'alpha': random.randint(30, 100)
        })
    
    def update(self):
        for particle in self.particles:
            particle['pos'][0] += particle['vel'][0]
            particle['pos'][1] += particle['vel'][1]
            
            # Wrap around screen
            if particle['pos'][0] < 0: particle['pos'][0] = self.screen_size[0]
            if particle['pos'][0] > self.screen_size[0]: particle['pos'][0] = 0
            if particle['pos'][1] < 0: particle['pos'][1] = self.screen_size[1]
            if particle['pos'][1] > self.screen_size[1]: particle['pos'][1] = 0
    
    def draw(self, surface):
        for particle in self.particles:
            color = (*particle['color'], particle['alpha'])
            s = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (particle['size'], particle['size']), particle['size'])
            surface.blit(s, particle['pos'], special_flags=pygame.BLEND_ADD)

class AnimatedButton:
    """Modern animated button with hover effects"""
    def __init__(self, text, rect, font, action=None):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.original_rect = pygame.Rect(rect)
        self.font = font
        self.action = action
        self.hover = False
        self.selected = False
        self.glow_size = 0
        self.pulse = 0
    
    def update(self, mouse_pos, dt):
        self.hover = self.rect.collidepoint(mouse_pos)
        self.pulse += dt * 0.003
        
        # Smooth glow animation
        target_glow = 20 if self.hover or self.selected else 0
        self.glow_size += (target_glow - self.glow_size) * dt * 0.01
        
        # Subtle hover scaling
        target_scale = 1.05 if self.hover or self.selected else 1.0
        current_scale = self.rect.width / self.original_rect.width
        new_scale = current_scale + (target_scale - current_scale) * dt * 0.01
        
        self.rect.width = int(self.original_rect.width * new_scale)
        self.rect.height = int(self.original_rect.height * new_scale)
        self.rect.center = self.original_rect.center
    
    def draw(self, surface):
        # Draw glow effect
        if self.glow_size > 0:
            glow_rect = self.rect.inflate(self.glow_size * 2, self.glow_size * 2)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, UITheme.GLOW, glow_surf.get_rect(), border_radius=15)
            surface.blit(glow_surf, glow_rect, special_flags=pygame.BLEND_ADD)
        
        # Draw button background with gradient effect
        color = UITheme.HOVER_GRADIENT[0] if self.hover or self.selected else UITheme.BUTTON_GRADIENT[0]
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        
        # Draw border
        border_color = UITheme.PRIMARY if self.hover or self.selected else UITheme.TEXT_SECONDARY
        pygame.draw.rect(surface, border_color, self.rect, 3, border_radius=12)
        
        # Draw text with subtle pulse effect
        text_color = UITheme.PRIMARY if self.hover or self.selected else UITheme.TEXT_PRIMARY
        pulse_offset = math.sin(self.pulse) * 2 if self.selected else 0
        
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.centery + pulse_offset))
        
        # Add text shadow
        shadow_surface = self.font.render(self.text, True, (0, 0, 0))
        shadow_rect = text_rect.copy()
        shadow_rect.x += 2
        shadow_rect.y += 2
        surface.blit(shadow_surface, shadow_rect)
        surface.blit(text_surface, text_rect)

class ModernUI:
    def __init__(self):
        pygame.display.set_caption('NINJA GAME - ENHANCED UI')
        
        # Try different display modes with fallbacks
        try:
            self.screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
        except pygame.error:
            try:
                self.screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
            except pygame.error:
                self.screen = pygame.display.set_mode((640, 480))
        
        self.clock = pygame.time.Clock()
        self.fullscreen = False
        
        # Better font loading with fallbacks
        try:
            self.title_font = pygame.font.SysFont("arial", 72, bold=True)
            self.button_font = pygame.font.SysFont("arial", 36, bold=True)
            self.small_font = pygame.font.SysFont("arial", 24)
        except:
            self.title_font = pygame.font.Font(None, 72)
            self.button_font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        
        # Particle system
        self.particles = ParticleSystem(self.screen.get_size())
        
        # Load assets with fallbacks
        self.load_assets()
    
    def load_assets(self):
        """Load game assets with fallback generation"""
        try:
            self.background = pygame.image.load("data/images/background.png").convert()
        except:
            self.background = self.create_gradient_background()
        
        try:
            self.hover_sound = pygame.mixer.Sound("data/sfx/ambience.wav")
            self.click_sound = pygame.mixer.Sound("data/sfx/shoot.wav")
            self.hover_sound.set_volume(0.3)
            self.click_sound.set_volume(0.5)
        except:
            self.hover_sound = None
            self.click_sound = None
    
    def create_gradient_background(self):
        """Create a beautiful gradient background that scales properly"""
        # Always create at a reasonable size first
        bg = pygame.Surface((1024, 768))
        for y in range(bg.get_height()):
            ratio = y / bg.get_height()
            r = int(10 + ratio * 20)
            g = int(15 + ratio * 25)
            b = int(30 + ratio * 40)
            pygame.draw.line(bg, (r, g, b), (0, y), (bg.get_width(), y))
        return bg
    
    def draw_animated_background(self):
        """Draw animated background with proper scaling"""
        # Scale background to fit current screen size
        current_size = self.screen.get_size()
        if self.background.get_size() != current_size:
            bg_scaled = pygame.transform.scale(self.background, current_size)
        else:
            bg_scaled = self.background
        
        self.screen.blit(bg_scaled, (0, 0))
        
        # Add dark overlay
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((*UITheme.BACKGROUND, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Draw particles
        self.particles.update()
        self.particles.draw(self.screen)
        
        # Add scanline effect
        for y in range(0, self.screen.get_height(), 4):
            pygame.draw.line(self.screen, (255, 255, 255, 5),
                           (0, y), (self.screen.get_width(), y))
    
    def draw_title(self, text, y_offset=0, glow=True):
        """Draw animated title with proper positioning"""
        sw, sh = self.screen.get_size()
        
        if glow:
            # Glow effect
            glow_surface = self.title_font.render(text, True, UITheme.PRIMARY)
            for offset in [(2, 2), (-2, 2), (2, -2), (-2, -2), (4, 4), (-4, 4), (4, -4), (-4, -4)]:
                glow_rect = glow_surface.get_rect(center=(sw // 2 + offset[0], sh // 4 + y_offset + offset[1]))
                self.screen.blit(glow_surface, glow_rect, special_flags=pygame.BLEND_ADD)
        
        # Main title - properly centered
        title_surface = self.title_font.render(text, True, UITheme.ACCENT)
        title_rect = title_surface.get_rect(center=(sw // 2, sh // 4 + y_offset))
        self.screen.blit(title_surface, title_rect)
    
    def main_menu(self):
        """Enhanced main menu with proper responsive positioning"""
        selected = 0
        
        # Get screen dimensions for proper positioning
        sw, sh = self.screen.get_size()
        
        # Calculate button dimensions and positions dynamically
        button_width = 200
        button_height = 50
        button_spacing = 70
        start_y = sh // 2 - 50  # Center vertically
        
        buttons = [
            AnimatedButton("START GAME",
                         (sw // 2 - button_width // 2, start_y, button_width, button_height),
                         self.button_font),
            AnimatedButton("SELECT LEVEL",
                         (sw // 2 - button_width // 2, start_y + button_spacing, button_width, button_height),
                         self.button_font),
            AnimatedButton("OPTIONS",
                         (sw // 2 - button_width // 2, start_y + button_spacing * 2, button_width, button_height),
                         self.button_font),
            AnimatedButton("QUIT GAME",
                         (sw // 2 - button_width // 2, start_y + button_spacing * 3, button_width, button_height),
                         self.button_font)
        ]
        
        last_hover = -1
        time_accumulator = 0
        
        while True:
            dt = self.clock.tick(60)
            time_accumulator += dt
            
            # Update screen size in case of resize
            sw, sh = self.screen.get_size()
            
            self.draw_animated_background()
            
            # Animated title with pulse - positioned relative to screen size
            pulse = math.sin(time_accumulator * 0.003) * 10
            self.draw_title("NINJA GAME", pulse)
            
            # Update button positions if screen was resized
            start_y = sh // 2 - 50
            for i, button in enumerate(buttons):
                new_x = sw // 2 - button_width // 2
                new_y = start_y + i * button_spacing
                button.original_rect = pygame.Rect(new_x, new_y, button_width, button_height)
                if not button.hover:  # Don't update if mouse is hovering to prevent jitter
                    button.rect = pygame.Rect(new_x, new_y, button_width, button_height)
            
            # Update and draw buttons
            mouse_pos = pygame.mouse.get_pos()
            for i, button in enumerate(buttons):
                button.selected = (i == selected)
                button.update(mouse_pos, dt)
                button.draw(self.screen)
                
                # Play hover sound
                if button.hover and last_hover != i:
                    if self.hover_sound:
                        self.hover_sound.play()
                    last_hover = i
            
            if not any(button.hover for button in buttons):
                last_hover = -1
            
            # Handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == VIDEORESIZE:
                    # Handle window resize
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                    self.particles = ParticleSystem(self.screen.get_size())
                    
                if event.type == KEYDOWN:
                    if event.key in [K_DOWN, K_s]:
                        selected = (selected + 1) % len(buttons)
                    elif event.key in [K_UP, K_w]:
                        selected = (selected - 1) % len(buttons)
                    elif event.key == K_RETURN:
                        self.handle_menu_selection(selected)
                    elif event.key == K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                        
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    for i, button in enumerate(buttons):
                        if button.hover:
                            if self.click_sound:
                                self.click_sound.play()
                            self.handle_menu_selection(i)
            
            pygame.display.flip()
    
    def handle_menu_selection(self, selection):
        """Handle menu selection"""
        if selection == 0:  # Start Game
            self.launch_game(0, self.fullscreen)
        elif selection == 1:  # Select Level
            self.select_level_menu()
        elif selection == 2:  # Options
            self.options_menu()
        elif selection == 3:  # Quit
            pygame.quit()
            sys.exit()
    
    def select_level_menu(self):
        """Enhanced level selection with visual map"""
        # Available levels (including 3.json)
        available_levels = [0, 1, 2, 3]  # Added level 3 (3.json)
        total_levels = len(available_levels)
        unlocked_levels = total_levels  # All levels unlocked for now
        selected = 0
        time_accumulator = 0
        
        # Create level nodes in a more interesting pattern - adapt to screen size
        level_nodes = []
        sw, sh = self.screen.get_size()
        center_x, center_y = sw // 2, sh // 2
        radius = min(sw, sh) // 4  # Adaptive radius
        
        for i in range(total_levels):
            angle = (i / total_levels) * 2 * math.pi - math.pi / 2
            x = center_x + math.cos(angle) * radius
            y = center_y + math.sin(angle) * radius * 0.6
            level_nodes.append((x, y))
        
        while True:
            dt = self.clock.tick(60)
            time_accumulator += dt
            
            self.draw_animated_background()
            self.draw_title("SELECT LEVEL", glow=False)
            
            sw, sh = self.screen.get_size()
            
            # Draw connections between levels
            for i in range(len(level_nodes) - 1):
                if i < unlocked_levels - 1:
                    color = UITheme.PRIMARY
                    pygame.draw.line(self.screen, color, level_nodes[i], level_nodes[i + 1], 3)
            
            # Draw level nodes
            for i, (x, y) in enumerate(level_nodes):
                is_unlocked = i < unlocked_levels
                is_selected = i == selected
                
                # Node glow effect for selected
                if is_selected:
                    glow_radius = 40 + math.sin(time_accumulator * 0.005) * 10
                    glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, UITheme.GLOW, (glow_radius, glow_radius), glow_radius)
                    self.screen.blit(glow_surf, (x - glow_radius, y - glow_radius), special_flags=pygame.BLEND_ADD)
                
                # Draw node
                if is_unlocked:
                    color = UITheme.ACCENT if is_selected else UITheme.PRIMARY
                    pygame.draw.circle(self.screen, color, (int(x), int(y)), 20)
                    pygame.draw.circle(self.screen, UITheme.TEXT_PRIMARY, (int(x), int(y)), 20, 3)
                else:
                    pygame.draw.circle(self.screen, UITheme.TEXT_SECONDARY, (int(x), int(y)), 15)
                
                # Draw level number (show actual level ID)
                level_text = self.small_font.render(str(available_levels[i]), True,
                                                  UITheme.BACKGROUND if is_unlocked else UITheme.TEXT_SECONDARY)
                level_rect = level_text.get_rect(center=(int(x), int(y)))
                self.screen.blit(level_text, level_rect)
            
            # Instructions
            instructions = [
                "Arrow Keys: Navigate | Enter: Select Level | ESC: Back",
                f"Levels Available: {unlocked_levels}/{total_levels}"
            ]
            
            for i, instruction in enumerate(instructions):
                text = self.small_font.render(instruction, True, UITheme.TEXT_SECONDARY)
                text_rect = text.get_rect(center=(sw // 2, sh - 60 + i * 25))
                self.screen.blit(text, text_rect)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        return
                    elif event.key in [K_RIGHT, K_d]:
                        selected = (selected + 1) % total_levels
                    elif event.key in [K_LEFT, K_a]:
                        selected = (selected - 1) % total_levels
                    elif event.key in [K_RETURN, K_SPACE]:
                        if selected < unlocked_levels:
                            self.launch_game(available_levels[selected], self.fullscreen)
                            return
                
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    for i, (x, y) in enumerate(level_nodes):
                        if math.sqrt((mouse_pos[0] - x)**2 + (mouse_pos[1] - y)**2) <= 25:
                            selected = i
                            if i < unlocked_levels:
                                if self.click_sound:
                                    self.click_sound.play()
                                self.launch_game(available_levels[i], self.fullscreen)
                                return
            
            pygame.display.flip()
    
    def options_menu(self):
        """Enhanced options menu"""
        selected = 0
        
        # Get screen dimensions for proper positioning
        sw, sh = self.screen.get_size()
        button_width = 200
        button_height = 50
        button_spacing = 70
        start_y = sh // 2 - 50
        
        buttons = [
            AnimatedButton(f"FULLSCREEN: {'ON' if self.fullscreen else 'OFF'}",
                         (sw // 2 - button_width // 2, start_y, button_width, button_height), 
                         self.button_font),
            AnimatedButton("BACK", 
                         (sw // 2 - button_width // 2, start_y + button_spacing, button_width, button_height), 
                         self.button_font)
        ]
        
        while True:
            dt = self.clock.tick(60)
            
            self.draw_animated_background()
            self.draw_title("OPTIONS", glow=False)
            
            # Update and draw buttons
            mouse_pos = pygame.mouse.get_pos()
            for i, button in enumerate(buttons):
                button.selected = (i == selected)
                button.update(mouse_pos, dt)
                button.draw(self.screen)
            
            # Handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == KEYDOWN:
                    if event.key in [K_DOWN, K_s]:
                        selected = (selected + 1) % len(buttons)
                    elif event.key in [K_UP, K_w]:
                        selected = (selected - 1) % len(buttons)
                    elif event.key == K_RETURN:
                        if selected == 0:  # Toggle fullscreen
                            self.toggle_fullscreen()
                            buttons[0].text = f"FULLSCREEN: {'ON' if self.fullscreen else 'OFF'}"
                        elif selected == 1:  # Back
                            return
                    elif event.key == K_ESCAPE:
                        return
                
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    for i, button in enumerate(buttons):
                        if button.hover:
                            if self.click_sound:
                                self.click_sound.play()
                            if i == 0:
                                self.toggle_fullscreen()
                                buttons[0].text = f"FULLSCREEN: {'ON' if self.fullscreen else 'OFF'}"
                            elif i == 1:
                                return
            
            pygame.display.flip()
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode with proper error handling"""
        self.fullscreen = not self.fullscreen
        
        try:
            if self.fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
            else:
                self.screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
            
            # Update particle system for new screen size
            self.particles = ParticleSystem(self.screen.get_size())
            self.background = pygame.transform.scale(self.background, self.screen.get_size())
        except pygame.error:
            print("Failed to toggle fullscreen, reverting...")
            self.fullscreen = False
            self.screen = pygame.display.set_mode((1024, 768), pygame.RESIZABLE)
    
    def launch_game(self, level_id, fullscreen_state):
        """Launch the game with specified level"""
        try:
            game = Game(level_id, fullscreen_state)
            game.run()
        except Exception as e:
            print(f"Error launching game: {e}")
            # Return to main menu on error

# Enhanced pause menu for integration with game.py
def create_enhanced_pause_menu(game_instance):
    """Create enhanced pause menu that can be integrated into game.py"""
    screen = game_instance.screen
    selected = 0
    time_accumulator = 0
    
    # Create particle system for pause menu
    particles = ParticleSystem(screen.get_size())
    
    # Fonts
    title_font = pygame.font.Font(None, 48)
    button_font = pygame.font.Font(None, 28)  # Smaller font for buttons
    
    # Determine available options based on current level
    available_levels = [0, 1, 2, 3]  # Include level 3 (3.json)
    max_level = max(available_levels)
    
    if hasattr(game_instance, 'level') and game_instance.level < max_level:
        options = ["Resume Game", "Toggle Fullscreen", "Next Level", "Main Menu", "Quit Game"]
    else:
        options = ["Resume Game", "Toggle Fullscreen", "Main Menu", "Quit Game"]
    
    buttons = []
    sw, sh = screen.get_size()
    
    # Calculate dynamic menu box size based on number of options
    button_height = 40
    button_spacing = 50
    button_width = 200
    title_height = 60
    padding = 30
    
    menu_height = title_height + len(options) * button_spacing + padding * 2
    menu_width = button_width + padding * 2
    
    # Center the menu box
    menu_x = sw // 2 - menu_width // 2
    menu_y = sh // 2 - menu_height // 2
    
    # Position buttons within the menu box
    start_y = menu_y + title_height + padding
    
    for i, option in enumerate(options):
        button_x = menu_x + padding
        button_y = start_y + i * button_spacing
        rect = pygame.Rect(button_x, button_y, button_width, button_height)
        buttons.append(AnimatedButton(option, rect, button_font))
    
    clock = pygame.time.Clock()
    
    while True:
        dt = clock.tick(60)
        time_accumulator += dt
        
        # Draw game background (blurred/darkened)
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        # Draw particles
        particles.update()
        particles.draw(screen)
        
        # Draw pause menu box with proper size
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        pygame.draw.rect(screen, UITheme.SURFACE, menu_rect, border_radius=15)
        pygame.draw.rect(screen, UITheme.PRIMARY, menu_rect, 3, border_radius=15)
        
        # Draw title centered in menu box
        title_surface = title_font.render("PAUSED", True, UITheme.ACCENT)
        title_rect = title_surface.get_rect(center=(menu_x + menu_width // 2, menu_y + title_height // 2))
        screen.blit(title_surface, title_rect)
        
        # Update and draw buttons
        mouse_pos = pygame.mouse.get_pos()
        for i, button in enumerate(buttons):
            button.selected = (i == selected)
            button.update(mouse_pos, dt)
            button.draw(screen)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_w, pygame.K_UP]:
                    selected = (selected - 1) % len(options)
                elif event.key in [pygame.K_s, pygame.K_DOWN]:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return handle_pause_selection(selected, options, game_instance, available_levels)
                elif event.key == pygame.K_ESCAPE:
                    return 'resume'
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, button in enumerate(buttons):
                    if button.hover:
                        return handle_pause_selection(i, options, game_instance, available_levels)
        
        pygame.display.flip()

def handle_pause_selection(selected, options, game_instance, available_levels):
    """Handle pause menu selection"""
    option = options[selected]
    
    if option == "Resume Game":
        return 'resume'
    elif option == "Toggle Fullscreen":
        game_instance.fullscreen = not game_instance.fullscreen
        try:
            if game_instance.fullscreen:
                game_instance.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
            else:
                game_instance.screen = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
        except:
            game_instance.fullscreen = False
            game_instance.screen = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
        return None  # Continue pause menu
    elif option == "Next Level":
        if hasattr(game_instance, 'level'):
            current_index = available_levels.index(game_instance.level) if game_instance.level in available_levels else 0
            if current_index < len(available_levels) - 1:
                game_instance.level = available_levels[current_index + 1]
                game_instance.load_level(game_instance.level)
        return 'resume'
    elif option == "Main Menu":
        pygame.mixer.music.stop()
        return 'main_menu'
    elif option == "Quit Game":
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    ui = ModernUI()
    ui.main_menu() 

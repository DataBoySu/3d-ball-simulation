"""GPU Particle Simulation Visualizer."""

import time
import random
from typing import Optional, Tuple, List
import numpy as np
from . import ui_components  # Import UI rendering functions
from . import event_handler  # Import event handling


class ParticleVisualizer:
    
    def __init__(self, window_size: Tuple[int, int] = None, max_render_particles: int = None):
        # Load defaults from shared config when not explicitly provided
        if window_size is None:
            try:
                from . import config
                window_size = config.WINDOW_SIZE
            except Exception:
                window_size = (1600, 1000)

        if max_render_particles is None:
            try:
                from . import config
                max_render_particles = config.MAX_RENDER_PARTICLES
            except Exception:
                max_render_particles = 2000

        self.window_size = window_size
        self.max_render_particles = max_render_particles
        self.running = False
        self.pygame = None
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.colors = []
        self.particle_sizes = []
        self.slider_multiplier = 1
        self.multiplier_levels = [1, 10, 100, 1000]
        self.multiplier_button = {
            'pos': (0, 0),
            'width': 80,
            'height': 30,
            'label': 'x1'
        }
        self.sliders = {
            'gravity': {'value': 500.0, 'min': 0.0, 'max': 10000.0, 'pos': (0, 0), 'width': 220, 'label': 'Big Ball Gravity'},
            'small_ball_speed': {'value': 300.0, 'min': 50.0, 'max': 600.0, 'pos': (0, 0), 'width': 220, 'label': 'Small Ball Speed'},
            'initial_balls': {'value': 1.0, 'min': 1.0, 'max': 10.0, 'pos': (0, 0), 'width': 220, 'label': 'Initial Balls', 'is_int': True, 'base_max': 10.0}
        }
        self.dragging_slider = None
        
        self.max_balls_cap = {
            'pos': (0, 0),
            'width': 100,
            'height': 30,
            'value': '100000',
            'active': False,
            'label': 'Max Cap'
        }
        
        self.split_enabled = False
        self.split_button = {
            'pos': (0, 0),
            'width': 160,
            'height': 30,
            'label': 'Ball Splitting: OFF'
        }
        
        self._init_pygame()
        self._layout_controls()
    
    def _init_pygame(self):
        try:
            # Insert our shim for `pygame.pkgdata` so pygame doesn't import
            # the deprecated `pkg_resources` API and emit a deprecation warning.
            import sys
            try:
                from .pygame_pkgdata_fix import pygame_pkgdata_module
                sys.modules.setdefault('pygame.pkgdata', pygame_pkgdata_module)
            except Exception:
                # If the shim cannot be imported for any reason, continue; pygame
                # will fall back to its bundled behavior (may emit a warning).
                pass

            import pygame
            self.pygame = pygame
            pygame.init()
            self.screen = pygame.display.set_mode(self.window_size)
            pygame.display.set_caption("GPU Particle Simulation - Benchmark Visualization")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 20)
            self.running = True
            
            for _ in range(self.max_render_particles):
                color = (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(100, 255)
                )
                self.colors.append(color)
                self.particle_sizes.append(random.randint(3, 8))
                
        except ImportError:
            self.running = False
            print("[WARNING] pygame not installed - visualization disabled")
            print("Install with: pip install pygame")


    def _layout_controls(self):
        """Compute positions for sliders and controls so they align neatly.

        This uses the current `self.window_size` to distribute controls
        horizontally with consistent spacing and vertical alignment.
        """
        margin = 40
        spacing = 18
        slider_width = 300
        control_y = max(40, self.window_size[1] - 80)

        x = margin
        order = ['gravity', 'small_ball_speed', 'initial_balls']
        for key in order:
            s = self.sliders.get(key)
            if s is None:
                continue
            s['pos'] = (x, control_y)
            s['width'] = slider_width
            x += slider_width + spacing

        # Max cap input
        self.max_balls_cap['pos'] = (x, control_y)
        self.max_balls_cap['width'] = 120
        x += self.max_balls_cap['width'] + spacing

        # Multiplier
        self.multiplier_button['pos'] = (x, control_y)
        self.multiplier_button['width'] = 60
        self.multiplier_button['height'] = 30
        x += self.multiplier_button['width'] + spacing

        # Split button
        self.split_button['pos'] = (x, control_y)
        self.split_button['width'] = 140
        self.split_button['height'] = 30
    
    def is_available(self) -> bool:
        return self.running and self.pygame is not None
    
    def render_frame(
        self,
        positions: np.ndarray,
        masses: np.ndarray,
        colors: np.ndarray,
        glows: np.ndarray,
        influence_boundaries: list,
        total_particles: int,
        active_particles: int,
        fps: float = 0,
        gpu_util: float = 0,
        elapsed_time: float = 0
    ):
        if not self.is_available():
            return
        
        self.screen.fill((5, 5, 15))
        
        scale_x = self.window_size[0] / 1000.0
        scale_y = self.window_size[1] / 800.0
        
        for bx, by, bradius in influence_boundaries:
            screen_x = int(bx * scale_x)
            screen_y = int(by * scale_y)
            screen_radius = max(10, int(bradius * min(scale_x, scale_y)))
            
            if screen_radius > 5:
                self.pygame.draw.circle(
                    self.screen,
                    (255, 255, 255),
                    (screen_x, screen_y),
                    screen_radius,
                    3
                )
            
            ball_radius = int(36 * min(scale_x, scale_y))
            self.pygame.draw.circle(
                self.screen,
                (200, 200, 200),
                (screen_x, screen_y),
                ball_radius,
                1
            )
        
        blur_surface = self.pygame.Surface(self.window_size, self.pygame.SRCALPHA)
        blur_surface.fill((5, 5, 15, 8))
        self.screen.blit(blur_surface, (0, 0), special_flags=self.pygame.BLEND_RGBA_SUB)
        
        num_particles = len(positions)
        for i in range(num_particles):
            x = int(positions[i, 0] * scale_x)
            y = int(positions[i, 1] * scale_y)
            
            mass = masses[i]
            if colors is not None and i < len(colors):
                if len(colors.shape) == 2 and colors.shape[1] == 3:
                    rgb = colors[i]
                    base_color = (int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                else:
                    color_state = colors[i]
                    base_color = (int(180 + 75 * color_state), int(180 - 180 * color_state), int(200 - 200 * color_state))
            else:
                base_color = (180, 180, 200)
            
            glow_intensity = glows[i] if glows is not None and i < len(glows) else 0.0
            
            if mass >= 1000:
                radius = 36
            else:
                radius = 8
            
            base_glow = (
                min(255, int(base_color[0] * 1.3)),
                min(255, int(base_color[1] * 1.3)),
                min(255, int(base_color[2] * 1.3))
            )
            
            glow_radius = radius + int(3 + 5 * glow_intensity)
            glow_r = min(255, int(base_glow[0] * (0.8 + 0.4 * glow_intensity)))
            glow_g = min(255, int(base_glow[1] * (0.8 + 0.4 * glow_intensity)))
            glow_b = min(255, int(base_glow[2] * (0.8 + 0.4 * glow_intensity)))
            
            self.pygame.draw.circle(self.screen, (glow_r, glow_g, glow_b), (x, y), glow_radius)
            self.pygame.draw.circle(self.screen, base_color, (x, y), radius)
        
        # Draw modern UI panels and controls
        stats_data = {
            'total_particles': total_particles,
            'active_particles': active_particles,
            'rendered_particles': num_particles,
            'fps': fps,
            'gpu_util': gpu_util,
            'elapsed_time': elapsed_time,
            'backend_multiplier': 1
        }
        ui_components.draw_stats(self.screen, self.font, self.window_size, stats_data)

        self._draw_sliders()
        self._draw_text_input()
        self._draw_multiplier_button()
        self._draw_toggle_button()
        
        self.pygame.display.flip()
        self.clock.tick()  # Unlimited FPS - no artificial cap
    
    def _draw_stats(
        self,
        total_particles: int,
        active_particles: int,
        rendered_particles: int,
        fps: float,
        gpu_util: float,
        elapsed_time: float
    ):
        backend_mult = int(self.sliders.get('backend_multiplier', {}).get('value', 1))
        stats_data = {
            'total_particles': total_particles,
            'active_particles': active_particles,
            'rendered_particles': rendered_particles,
            'fps': fps,
            'gpu_util': gpu_util,
            'elapsed_time': elapsed_time,
            'backend_multiplier': backend_mult
        }
        ui_components.draw_stats(self.screen, self.font, self.window_size, stats_data)
    
    def _draw_sliders(self):
        ui_components.draw_sliders(self.pygame, self.screen, self.small_font, self.sliders, self.dragging_slider)
    
    def _draw_toggle_button(self):
        ui_components.draw_toggle_button(self.pygame, self.screen, self.small_font, self.split_button, self.split_enabled)
    
    def _draw_text_input(self):
        ui_components.draw_text_input(self.pygame, self.screen, self.font, self.small_font, self.max_balls_cap)
    
    def _draw_multiplier_button(self):
        ui_components.draw_multiplier_button(self.pygame, self.screen, self.small_font, self.multiplier_button)
    
    def _handle_slider_click(self, pos):
        mx, my = pos
        for key, slider in self.sliders.items():
            x, y = slider['pos']
            width = slider['width']
            if x <= mx <= x + width and y - 12 <= my <= y + 32:
                self.dragging_slider = key
                self._update_slider_value(key, mx)
                break
    
    def _handle_slider_drag(self, pos):
        if self.dragging_slider:
            self._update_slider_value(self.dragging_slider, pos[0])
    
    def _update_slider_value(self, key, mouse_x):
        slider = self.sliders[key]
        x = slider['pos'][0]
        width = slider['width']
        
        mouse_x = max(x, min(mouse_x, x + width))
        normalized = (mouse_x - x) / width
        value = slider['min'] + normalized * (slider['max'] - slider['min'])
        
        import math
        if math.isnan(value) or math.isinf(value):
            value = slider['min']
        
        if slider.get('is_int', False):
            value = round(value)
        
        slider['value'] = value
    
    def get_slider_values(self):
        import math
        values = {}
        for key, slider in self.sliders.items():
            val = slider['value']
            if math.isnan(val) or math.isinf(val):
                val = slider['min']
                slider['value'] = val
            values[key] = val
        
        max_cap = int(self.max_balls_cap['value']) if self.max_balls_cap['value'] else 100000
        values['max_balls_cap'] = max_cap
        
        values['backend_multiplier'] = 1
        values['big_ball_count'] = 3
        
        return values
    
    def get_split_enabled(self):
        return self.split_enabled
    
    def get_max_balls_cap(self):
        return self.max_balls_cap['value']
    
    def get_spawn_requests(self):
        if not hasattr(self, 'spawn_requests'):
            return []
        requests = self.spawn_requests[:]
        self.spawn_requests.clear()
        return requests
    
    def close(self):
        # Ensure pygame subsystems are quit regardless of current `running` state.
        try:
            if self.pygame:
                try:
                    # Try to quit the display first
                    if hasattr(self.pygame, 'display'):
                        try:
                            self.pygame.display.quit()
                        except Exception:
                            pass
                finally:
                    try:
                        self.pygame.quit()
                    except Exception:
                        pass
        except Exception:
            # Swallow any exceptions during shutdown to avoid hanging the process
            pass
        self.running = False


def create_visualizer(enabled: bool = False, **kwargs) -> Optional[ParticleVisualizer]:
    if not enabled:
        return None
    
    viz = ParticleVisualizer(**kwargs)
    if not viz.is_available():
        return None
    
    return viz

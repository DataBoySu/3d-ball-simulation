"""Modern UI component rendering for particle visualizer.

This replaces the older blocky UI with sleeker panels, rounded sliders
and updated buttons while keeping the same function signatures used by
`visualizer.py` so integration is minimal.
"""

import math


def _rounded_rect(surface, rect, color, radius=8):
    try:
        import pygame
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    except Exception:
        surface.fill(color, rect)


def draw_stats(screen, font, window_size, stats_data):
    padding = 12
    w = 300
    h = 160
    x = window_size[0] - w - padding
    y = padding

    panel = screen.subsurface((x, y, w, h)).copy()
    panel.fill((20, 24, 28, 180))
    screen.blit(panel, (x, y))

    title = font.render("Simulation Stats", True, (230, 230, 230))
    screen.blit(title, (x + 14, y + 10))

    backend_mult = stats_data.get('backend_multiplier', 1)
    total_computed = stats_data['total_particles'] * backend_mult

    lines = [
        f"Active: {stats_data['active_particles']:,} / {stats_data['total_particles']:,}",
        f"Rendered: {stats_data['rendered_particles']:,}",
        f"Backend: {backend_mult}x  Total: {total_computed:,}",
        f"FPS: {stats_data['fps']:.1f}",
        f"GPU: {stats_data['gpu_util']:.0f}%",
        f"Time: {stats_data['elapsed_time']:.1f}s",
    ]

    oy = y + 40
    for line in lines:
        text = font.render(line, True, (200, 200, 200))
        screen.blit(text, (x + 14, oy))
        oy += 22


def draw_sliders(pygame, screen, small_font, sliders, dragging_slider):
    for key, slider in sliders.items():
        x, y = slider['pos']
        width = slider['width']
        height = 18

        # Panel label
        label_text = slider.get('label', key)
        label = small_font.render(label_text, True, (230, 230, 230))
        screen.blit(label, (x, y - 28))

        # Track
        track_rect = (x, y, width, height)
        _rounded_rect(screen, track_rect, (42, 46, 52), radius=10)

        # Draw tick marks (5 divisions)
        ticks = 5
        for i in range(ticks + 1):
            tx = x + int(i * (width / ticks))
            pygame.draw.line(screen, (70, 75, 80), (tx, y + height + 4), (tx, y + height + 10), 1)
            # label min/max only
            if i == 0:
                min_label = small_font.render(str(slider.get('min', '')), True, (150, 150, 150))
                screen.blit(min_label, (tx - 2, y + height + 12))
            elif i == ticks:
                max_label = small_font.render(str(slider.get('max', '')), True, (150, 150, 150))
                w_lab = max_label.get_width()
                screen.blit(max_label, (tx - w_lab + 2, y + height + 12))

        # Filled portion
        normalized = 0.0
        try:
            normalized = (slider['value'] - slider['min']) / max(1e-9, (slider['max'] - slider['min']))
            normalized = max(0.0, min(1.0, normalized))
        except Exception:
            normalized = 0.0

        filled_w = int(width * normalized)
        if filled_w > 0:
            _rounded_rect(screen, (x, y, filled_w, height), (60, 140, 220), radius=10)

        # Handle with subtle shadow
        handle_x = x + filled_w
        handle_radius = 11
        pygame.draw.circle(screen, (20, 24, 28), (handle_x, y + height // 2), handle_radius + 4)
        pygame.draw.circle(screen, (235, 235, 235), (handle_x, y + height // 2), handle_radius)

        # Value box
        val = slider['value']
        if slider.get('is_int', False):
            val_str = f"{int(val)}"
        else:
            val_str = f"{val:.1f}"

        vb_w, vb_h = 64, 20
        vb_x = x + width + 12
        vb_y = y - 1
        _rounded_rect(screen, (vb_x, vb_y, vb_w, vb_h), (28, 32, 36), radius=6)
        vb_text = small_font.render(val_str, True, (220, 220, 220))
        screen.blit(vb_text, (vb_x + 8, vb_y + 2))


def draw_text_input(pygame, screen, font, small_font, text_input_data):
    x, y = text_input_data['pos']
    width, height = text_input_data['width'], text_input_data['height']

    bg_color = (36, 40, 46) if text_input_data['active'] else (28, 32, 36)
    _rounded_rect(screen, (x, y, width, height), bg_color, radius=6)
    pygame.draw.rect(screen, (60, 70, 80), (x, y, width, height), 1, border_radius=6)

    label = small_font.render(text_input_data['label'], True, (180, 180, 180))
    screen.blit(label, (x, y - 20))

    value = text_input_data['value'] or ''
    value_text = font.render(value, True, (230, 230, 230))
    screen.blit(value_text, (x + 8, y + (height - value_text.get_height()) // 2))


def draw_multiplier_button(pygame, screen, font, button_data):
    x, y = button_data['pos']
    width, height = button_data['width'], button_data['height']
    label = button_data.get('label', '')

    _rounded_rect(screen, (x, y, width, height), (34, 40, 48), radius=8)
    pygame.draw.rect(screen, (70, 100, 160), (x, y, width, height), 2, border_radius=8)

    txt = font.render(label, True, (220, 220, 220))
    rect = txt.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(txt, rect)


def draw_toggle_button(pygame, screen, font, button_data, enabled):
    x, y = button_data['pos']
    width, height = button_data['width'], button_data['height']
    label_on = button_data.get('label', 'Toggle')

    base = (90, 180, 120) if enabled else (100, 110, 140)
    _rounded_rect(screen, (x, y, width, height), base, radius=8)
    pygame.draw.rect(screen, (30, 30, 30), (x, y, width, height), 2, border_radius=8)

    label_text = "Ball Splitting: ON" if enabled else "Ball Splitting: OFF"
    txt = font.render(label_text, True, (18, 18, 18) if enabled else (230, 230, 230))
    rect = txt.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(txt, rect)

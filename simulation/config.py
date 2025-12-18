"""Shared configuration for the simulation UI and renderer.

Keep global UI settings here so multiple modules can import the same
values (window size, defaults) without hardcoding them in several files.
"""

# Default window size used by visualizers
WINDOW_SIZE = (1600, 1000)

# Default maximum number of particles to render on-screen
MAX_RENDER_PARTICLES = 2000

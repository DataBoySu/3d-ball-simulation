"""Backend stress multiplier for GPU workloads."""

from . import gpu_setup


class BackendStressManager:
    
    def __init__(self):
        self._backend_arrays = []
        self._backend_multiplier = 1
        self._method = None
        self._library = None  # cp or torch
    
    def initialize(self, method: str, library, particle_count: int, backend_multiplier: int):
        self._method = method
        self._library = library
        self._backend_multiplier = backend_multiplier
        self._backend_arrays = []
        
        if backend_multiplier > 1:
            for i in range(backend_multiplier - 1):  # -1 because main arrays count as 1x
                if method == 'cupy':
                    backend_gpu, _ = gpu_setup.setup_cupy_arrays(particle_count, library)
                elif method == 'torch':
                    backend_gpu, _ = gpu_setup.setup_torch_arrays(particle_count, library)
                else:
                    continue
                self._backend_arrays.append(backend_gpu)
            
            total_particles = backend_multiplier * particle_count
            print(f"[Backend Stress] Initialized {backend_multiplier}x multiplier ({total_particles:,} total particles on GPU)")
    
    def update_multiplier(self, new_multiplier: int, particle_count: int):
        if new_multiplier < 1:
            new_multiplier = 1
        if new_multiplier > 100:
            new_multiplier = 100
        
        old_multiplier = self._backend_multiplier
        self._backend_multiplier = new_multiplier
        
        self._backend_arrays = []
        
        if new_multiplier > 1 and self._method and self._library:
            for i in range(new_multiplier - 1):
                if self._method == 'cupy':
                    backend_gpu, _ = gpu_setup.setup_cupy_arrays(particle_count, self._library)
                elif self._method == 'torch':
                    backend_gpu, _ = gpu_setup.setup_torch_arrays(particle_count, self._library)
                else:
                    continue
                self._backend_arrays.append(backend_gpu)
            
            total_particles = new_multiplier * particle_count
            print(f"[Backend Stress] Updated multiplier: {old_multiplier}x → {new_multiplier}x ({total_particles:,} total particles)")
    
    def run_physics(self, physics_module, params, library):
        if not self._backend_arrays:
            return
        
        for backend_gpu in self._backend_arrays:
            if self._method == 'cupy':
                physics_module.run_particle_physics_cupy(backend_gpu, params, library)
            elif self._method == 'torch':
                physics_module.run_particle_physics_torch(backend_gpu, params, library)
    
    def get_multiplier(self) -> int:
        return self._backend_multiplier
    
    def get_array_count(self) -> int:
        return len(self._backend_arrays)

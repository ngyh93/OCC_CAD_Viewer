import os


PERFORMANCE_SETTINGS = {
    # linear_def: Controls mesh density. Smaller value = finer mesh, better quality but slower.
    # angular_def: Controls angular precision. Smaller value = better curved surface representation.
    'mesh_quality': {
        'small': {'linear_def': 0.1, 'angular_def': 0.5},    # For models < 100mm
        'medium': {'linear_def': 1.0, 'angular_def': 5.0},     # For models 100-500mm
        'large': {'linear_def': 5.0, 'angular_def': 10.0},      # For models > 500mm but within a moderate range
        'very_large': {'linear_def': 10, 'angular_def': 50}  # For models that are very large
    },
    'batch_processing': {
        'batch_size': 5000,
        'num_processes': max(os.cpu_count() - 2, 1),
        'chunk_size': 100
    },
    'feature_limits': {
        'max_attempts_per_feature': 10,    
        'max_concurrent_features': 20     
    }
}

# If you have plenty of RAM and prefer simplicity, 
# --> a large batch_size (or even processing everything in one batch) can be fine.
# If you have limited RAM or want frequent checkpoints, 
# --> smaller batches (e.g., 500 or 1000) can help.

# If each shape generation is roughly the same complexity, 
# --> a larger chunk_size (like 50 or 100) is often fine.
# If tasks vary widely in how long they take, 
# --> a smaller chunk_size can avoid idle workers and improve overall throughput.

# max_attempts_per_feature
# Increase if you want higher success rates for tricky features (but more CPU time).
# Decrease if you want fewer tries per feature and can tolerate some generation failures.

# max_concurrent_features
# If your shapes are large or you see out-of-memory errors, lower this.
# If you want more complexity and have plenty of memory, you can increase it.
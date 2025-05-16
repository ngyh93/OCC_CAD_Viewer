import psutil
import time
from functools import wraps

def monitor_resources():
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = psutil.cpu_percent(interval=0.1)
    return memory_mb, cpu_percent

def performance_monitor(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_mem, start_cpu = monitor_resources()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_mem, end_cpu = monitor_resources()
        
        print(f"\nPerformance Statistics for {func.__name__}:")
        print(f"Time taken: {end_time - start_time:.2f} seconds")
        print(f"Memory usage: {end_mem - start_mem:.2f} MB")
        print(f"CPU usage: {end_cpu - start_cpu:.2f}%")
        
        return result
    return wrapper

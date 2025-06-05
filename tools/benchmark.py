import subprocess
import time
import os
import shutil


def time_check_nocache(args, count: int):
    args = args.split(" ")
    
    if args[1] == "anifetch.py":
        args.append("--force-render")
    
    st = time.time()
    for _ in range(count):
        subprocess.call(args)
    return time.time() - st


def time_check_cache(args, count: int):
    args = args.split(" ")
    subprocess.call(args)  # gen cache

    st = time.time()
    for _ in range(count):
        subprocess.call(args)
    return time.time() - st


count = 10
common_args = "-f example.mp4 -W 60 -H 30 -r 10 --benchmark"

print("NEOFETCH")

neofetch = time_check_cache("neofetch", count)

print("FASTFETCH")

fastfetch = time_check_cache("fastfetch --logo none", count)

print("ANIFETCH NOCACHE (Neofetch)")

anifetch_nocache_neo = time_check_nocache(f"python3 anifetch.py {common_args}", count)

print("ANIFETCH CACHED (Neofetch)")

anifetch_cached_neo = time_check_cache(f"python3 anifetch.py {common_args}", count)

print("ANIFETCH NOCACHE (Fastfetch)")

anifetch_nocache_fast = time_check_nocache(f"python3 anifetch.py {common_args} -ff", count)

print("ANIFETCH CACHED (Fastfetch)")

anifetch_cached_fast = time_check_cache(f"python3 anifetch.py {common_args} -ff", count)


print("Neofetch")
print(neofetch)
print("Fastfetch")
print(fastfetch)

print("Anifetch(No Cache)(neofetch)")
print(anifetch_nocache_neo)
print("Anifetch(Cached)(neofetch)")
print(anifetch_cached_neo)

print("Anifetch(No Cache)(fastfetch)")
print(anifetch_nocache_fast)
print("Anifetch(Cached)(fastfetch)")
print(anifetch_cached_fast)

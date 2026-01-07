#!/usr/bin/env python3
# matrix.py — lluvia de caracteres estilo "Matrix" en la terminal (inofensivo)

import random
import shutil
import time
import sys

def get_terminal_size():
    cols, rows = shutil.get_terminal_size((80, 24))
    return cols, rows

def main(speed=0.05):
    cols, rows = get_terminal_size()
    drops = [0] * cols
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*+-=[]{};:,.<>/?"
    try:
        while True:
            line = []
            for i in range(cols):
                if drops[i] == 0 and random.random() < 0.02:
                    drops[i] = 1
                if drops[i] > 0:
                    c = random.choice(chars)
                    # green characters using ANSI
                    line.append(f"\x1b[32m{c}\x1b[0m")
                    drops[i] += 1
                    if drops[i] > rows + random.randint(0, rows//2):
                        drops[i] = 0
                else:
                    line.append(" ")
            sys.stdout.write("".join(line) + "\n")
            sys.stdout.flush()
            time.sleep(speed)
    except KeyboardInterrupt:
        print("\n¡Listo! (Ctrl+C para salir)")

if __name__ == "__main__":
    main()

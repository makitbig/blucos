"""Blue cosmos background for the Blucos website: nebula clouds in the brand blues, a star field, and the
curve of a blue planet glowing at the bottom. Procedural (numpy + Pillow), no outside images.
Usage: python3 tools/make-cosmos.py assets/art   (writes cosmos-wide.webp and cosmos-tall.webp)"""
import sys
import numpy as np
from PIL import Image, ImageFilter

out = sys.argv[1]
rng = np.random.default_rng(7)


def noise(h, w, octaves=6, base=3):
    """Fractal value noise in 0..1: random grids upscaled smoothly and summed."""
    acc = np.zeros((h, w), np.float32); amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = base * 2 ** o + 1, int((base * 2 ** o) * w / h) + 1
        g = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * np.asarray(g, np.float32) / 255; tot += amp; amp *= 0.55
    acc /= tot
    return (acc - acc.min()) / (acc.max() - acc.min())


def render(w, h, planet_cx, planet_cy, planet_r, name):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    # deep space: navy to near-black, lighter toward the upper middle
    d = np.hypot((x - w * 0.55) / w, (y - h * 0.25) / h)
    sky = np.zeros((h, w, 3), np.float32)
    top, bot = np.array([22, 44, 120]), np.array([4, 7, 26])
    t = np.clip(d * 1.4, 0, 1)[..., None]
    sky += top * (1 - t) + bot * t
    # nebula: two noise fields, blue-cyan and violet, shaped by a soft diagonal band
    band = np.exp(-((y / h - 0.35 - (x / w - 0.5) * 0.35) ** 2) / 0.06)
    n1 = noise(h, w) ** 2.2 * band
    n2 = noise(h, w, base=2) ** 2.6 * np.exp(-((x / w - 0.25) ** 2 + (y / h - 0.3) ** 2) / 0.08)
    sky += n1[..., None] * np.array([40, 140, 255]) * 0.9
    sky += n2[..., None] * np.array([120, 70, 220]) * 0.7
    sky += (noise(h, w, base=6) ** 6 * band)[..., None] * np.array([150, 220, 255]) * 0.6
    # planet: a big blue sphere rising from the bottom, lit from the top left, with a thin cyan rim
    pd = np.hypot(x - planet_cx, y - planet_cy)
    inside = pd < planet_r
    # dark night side inside, a lit band near the edge (atmosphere seen from orbit), slight surface texture
    depth = np.clip((planet_r - pd) / (planet_r * 0.22), 0, 1)
    limb = (1 - depth) ** 2.2
    tex = noise(h, w, octaves=5, base=4)
    body = (np.array([6, 18, 66])[None, None] * (0.85 + 0.3 * tex[..., None])
            + limb[..., None] * np.array([40, 120, 230])[None, None])
    sky = np.where(inside[..., None], body, sky)
    rim = np.exp(-((pd - planet_r) ** 2) / (2 * (planet_r * 0.0035) ** 2))
    halo = np.exp(-np.clip(pd - planet_r, 0, None) / (planet_r * 0.045)) * (pd >= planet_r)
    sky += (rim * 0.9)[..., None] * np.array([150, 225, 255]) + (halo * 0.38)[..., None] * np.array([50, 140, 255])
    img = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8))
    # stars: many faint, a few bright with a soft glow; none on the planet
    stars = Image.new('RGB', (w, h)); px = stars.load()
    for _ in range(int(w * h / 900)):
        sx, sy = rng.integers(0, w), rng.integers(0, h)
        if np.hypot(sx - planet_cx, sy - planet_cy) < planet_r * 1.02: continue
        b = int(rng.choice([90, 130, 180, 230], p=[0.5, 0.3, 0.15, 0.05]))
        tint = rng.choice([0, 1, 2], p=[0.7, 0.2, 0.1])
        px[sx, sy] = (b, b, b) if tint == 0 else ((b, b, 255) if tint == 1 else (255, min(255, b + 20), b))
    glow = stars.filter(ImageFilter.GaussianBlur(1.6))
    big = Image.new('RGB', (w, h)); bp = big.load()
    for _ in range(int(w * h / 60000)):
        sx, sy = rng.integers(4, w - 4), rng.integers(4, int(h * 0.75))
        if np.hypot(sx - planet_cx, sy - planet_cy) < planet_r * 1.1: continue
        for dx in range(-1, 2):
            for dy in range(-1, 2): bp[sx + dx, sy + dy] = (255, 255, 255)
    bigglow = big.filter(ImageFilter.GaussianBlur(5))
    a = np.asarray(img, np.float32) + np.asarray(stars, np.float32) + np.asarray(glow, np.float32) * 1.5 + np.asarray(bigglow, np.float32) * 3 + np.asarray(big, np.float32) * 0.6
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    img.save(f'{out}/{name}.webp', 'WEBP', quality=80, method=6)


render(1920, 1080, planet_cx=1920 * 0.62, planet_cy=1080 * 1.95, planet_r=1080 * 1.12, name='cosmos-wide')
render(900, 1500, planet_cx=900 * 0.6, planet_cy=1500 * 1.55, planet_r=1500 * 0.68, name='cosmos-tall')

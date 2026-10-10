"""Small, reproducible demo catalogue used by the local API."""
from .core import Image
from .main import IMAGES


SEED_IMAGES = [
    ("fox-01", "red fox", "animal", ("orange fur", "wild", "forest"), "A red fox standing in a forest", 0.96),
    ("fox-02", "red fox", "animal", ("orange fur", "wild", "woodland"), "A red fox in woodland", 0.94),
    ("wolf-01", "wolf", "animal", ("gray fur", "wild", "forest"), "A gray wolf in a forest", 0.95),
    ("wolf-02", "wolf", "animal", ("gray fur", "wild"), "A wolf standing outdoors", 0.93),
    ("dog-01", "dog", "animal", ("pet", "brown fur"), "A brown dog outdoors", 0.95),
    ("dog-02", "dog", "animal", ("pet", "black fur"), "A black dog in a park", 0.94),
    ("bear-01", "bear", "animal", ("wild", "forest"), "A bear in a forest", 0.92),
    ("bear-02", "bear", "animal", ("wild", "brown fur"), "A brown bear outdoors", 0.91),
    ("deer-01", "deer", "animal", ("wild", "forest"), "A deer in a forest", 0.93),
    ("deer-02", "deer", "animal", ("wild", "grass"), "A deer standing in grass", 0.92),
    ("cat-01", "cat", "animal", ("pet", "white fur"), "A white cat sitting indoors", 0.96),
    ("bird-01", "bird", "animal", ("wings", "blue feathers"), "A small blue bird on a branch", 0.90),
]


def seed() -> int:
    """Replace the in-memory catalogue with known demo records."""
    IMAGES.clear()
    IMAGES.extend(Image(*row) for row in SEED_IMAGES)
    return len(IMAGES)


if __name__ == "__main__":
    print(f"Seeded {seed()} demo images")

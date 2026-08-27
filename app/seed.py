from .main import IMAGES
from .core import Image


SEED_IMAGES = [
    ("fox-01", "red fox", "animal", ("orange fur", "wild", "forest"), "A red fox standing in a forest", 0.96),
    ("fox-02", "red fox", "animal", ("orange fur", "wild"), "A red fox in woodland", 0.94),
    ("wolf-01", "wolf", "animal", ("gray fur", "wild", "forest"), "A gray wolf in a forest", 0.95),
    ("wolf-02", "wolf", "animal", ("gray fur", "wild"), "A wolf standing outdoors", 0.93),
    ("dog-01", "dog", "animal", ("pet", "brown fur"), "A brown dog outdoors", 0.95),
    ("dog-02", "dog", "animal", ("pet", "black fur"), "A black dog in a park", 0.94),
    ("bear-01", "bear", "animal", ("wild", "forest"), "A bear in a forest", 0.92),
    ("bear-02", "bear", "animal", ("wild", "brown fur"), "A brown bear outdoors", 0.91),
    ("deer-01", "deer", "animal", ("wild", "forest"), "A deer in a forest", 0.93),
    ("deer-02", "deer", "animal", ("wild", "grass"), "A deer standing in grass", 0.92),
]


def seed() -> None:
    IMAGES.clear()
    IMAGES.extend(Image(*row) for row in SEED_IMAGES)
    print(f"Seeded {len(IMAGES)} images")


if __name__ == "__main__":
    seed()

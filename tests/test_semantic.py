from app import semantic
from app.core import Image


def test_semantic_ranker_keeps_subject_mismatch_guard(monkeypatch):
    images = [
        Image('fox-test', 'red fox', 'animal', ('orange fur',), 'Fox in a forest', 0.95),
        Image('wolf-test', 'wolf', 'animal', ('gray fur',), 'Wolf in a forest', 0.95),
    ]
    monkeypatch.setattr(semantic, '_embed_batch', lambda texts: [[1.0, 0.0], [0.9, 0.1], [0.95, 0.05]])
    ranked = semantic.rank_with_semantic_embeddings('red fox in woodland', images, threshold=0.5)
    by_id = {item.image_id: item for item in ranked}
    assert by_id['fox-test'].decision == 'accepted'
    assert by_id['wolf-test'].decision == 'rejected'
    assert 'subject mismatch' in by_id['wolf-test'].reason.lower()

import pytest

from bookworm.concurrency import QueueProcess


def _produce_sqrts(numbers):
    from math import sqrt

    for num in numbers:
        yield int(sqrt(num))


def test_queue_process():
    expected = {1, 2, 3, 4, 5}
    valid_input = [1, 4, 9, 16, 25]
    process = QueueProcess(target=_produce_sqrts, args=(valid_input,))
    assert set(process) == expected

    # Test with invalid input
    invalid_input = (-16, -4, -1)
    process_iterator = iter(QueueProcess(target=_produce_sqrts, args=(invalid_input,)))
    with pytest.raises(ValueError):
        next(process_iterator)

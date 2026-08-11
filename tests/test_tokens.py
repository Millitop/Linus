from app.utils.tokens import generate_card_token, generate_retrieval_pin


def test_generate_card_token_is_unique_and_nonempty():
    tokens = {generate_card_token() for _ in range(50)}
    assert len(tokens) == 50
    assert all(len(t) > 20 for t in tokens)


def test_generate_retrieval_pin_length():
    pin = generate_retrieval_pin(6)
    assert len(pin) == 6
    assert pin.isdigit()

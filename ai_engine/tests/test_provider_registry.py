from app.services.providers import lookup


def test_lookup_converge_ict_returns_support_email() -> None:
    info = lookup("Converge ICT")
    assert info is not None
    assert info.support_email == "support@converge.com.ph"


def test_lookup_converge_ict_lowercase_exact_match() -> None:
    info = lookup("converge ict")
    assert info is not None
    assert info.name == "Converge ICT"


def test_lookup_converge_partial_match() -> None:
    info = lookup("Converge")
    assert info is not None
    assert info.name == "Converge ICT"


def test_lookup_unknown_provider_returns_none() -> None:
    assert lookup("Unknown Provider XYZ") is None


def test_lookup_none_returns_none() -> None:
    assert lookup(None) is None

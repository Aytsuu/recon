from app.repositories.memory import InMemoryCaseRepository

_repository: InMemoryCaseRepository | None = None


def get_case_repository() -> InMemoryCaseRepository:
    global _repository
    if _repository is None:
        _repository = InMemoryCaseRepository()
    return _repository


def reset_case_repository() -> InMemoryCaseRepository:
    global _repository
    _repository = InMemoryCaseRepository()
    return _repository

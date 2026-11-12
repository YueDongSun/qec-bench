"""Format-demo payload for ``example_000_smoke``.

Not a physical result. See ``docs/adr/0002-task-format.md``.
"""

FORMAT_DEMO_TOKEN: int = 1


def payload() -> dict[str, int]:
    """Return the object the format demo writes to ``output.json``.

    ``demo_token`` is a dimensionless scaffold token, not an observable.
    Units and conventions for real tasks are specified in ``spec/SCIENCE.md``.
    """
    return {"demo_token": FORMAT_DEMO_TOKEN}

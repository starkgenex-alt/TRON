import pytest

try:
    import transformers  # type: ignore
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

if HAS_TRANSFORMERS:
    from tron_ii.adapters.transformers_adapter import TransformersAdapter


def test_transformers_adapter_requires_transformers_installed():
    if not HAS_TRANSFORMERS:
        with pytest.raises(ImportError):
            from tron_ii.adapters.transformers_adapter import TransformersAdapter
            TransformersAdapter()
    else:
        adapter = TransformersAdapter()
        assert adapter.name == "transformers"


def test_transformers_adapter_rejects_missing_model():
    if not HAS_TRANSFORMERS:
        pytest.skip("transformers is not installed")

    adapter = TransformersAdapter()
    with pytest.raises(ValueError):
        adapter.train(dataset={"model": None}, config={})


def test_transformers_adapter_accepts_model_without_dataset():
    if not HAS_TRANSFORMERS:
        pytest.skip("transformers is not installed")

    adapter = TransformersAdapter()
    mock_model = object()  # Any object with model attribute
    result = adapter.train(dataset={"model": mock_model}, config={})
    assert result["capability_gain"] == 0.8
    assert result["cost"] == 1.0


def test_transformers_adapter_respects_config():
    if not HAS_TRANSFORMERS:
        pytest.skip("transformers is not installed")

    adapter = TransformersAdapter()
    result = adapter.train(
        dataset={"model": object()},
        config={"capability_gain": 0.5, "cost": 2.0}
    )
    assert result["capability_gain"] == 0.5
    assert result["cost"] == 2.0

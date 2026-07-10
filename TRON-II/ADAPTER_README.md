SB3 Adapter Example

To run the small Stable-Baselines3 demo (optional):

1. Create and activate a virtual environment.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Unix
source .venv/bin/activate
```

2. Install the demo dependencies:

```bash
pip install -r requirements-sb3.txt
```

3. Run the example:

```bash
python -m tron_ii.adapters.sb3_example
```

The script runs a short training session and saves `sb3_demo_model.zip` in the current folder.

## Supported adapters

- `sb3`: Stable-Baselines3 training integration.
- `scikit-learn`: Optional adapter via `SklearnAdapter` if scikit-learn is installed.
- `transformers`: Optional adapter via `TransformerAdapter` if Hugging Face Transformers is installed.

If optional dependencies are missing, TRON-II will still operate using dummy adapters or raise a meaningful error for unavailable integrations.

# Release v0.1.3

Published to PyPI as `tron-client-py`.

- PyPI: https://pypi.org/project/tron-client-py/0.1.3/
- Summary: First published release under the name `tron-client-py` after PyPI name restrictions prevented using `tronclient`.

Notes:
- Install: `pip install tron-client-py`
- The package import path remains `import tron`.
- During local verification, `pip` downgraded `pydantic` to 1.10.26 to satisfy pinned dependencies; this may conflict with other global packages (e.g., `ollama`). Use a virtual environment for project isolation.

Next steps:
- Push the tag and commit to GitHub (if desired): `git push origin main --tags`
- Create a GitHub Release using the tag and these notes.
- Optionally publish a small shim package named `tronclient` if you want `pip install tronclient` to work (may be blocked by PyPI rules).
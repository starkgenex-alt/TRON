Examples

Simple demo showing how to run TRON remote functions locally.

Run:

```bash
pip install tron-client-py
python examples/simple_inference.py
```

This example uses `tron.ensure_server()` to auto-start a local runtime for development. Replace with your deployed TRON server URL in production using `tron.config(url)`. 

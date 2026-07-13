import queue_server


def test_build_launch_context_includes_layers_and_install_command():
    queue_server.workers = {
        "worker-1": {
            "name": "worker-1",
            "status": "idle",
            "metadata": {"core": True, "tronii": True, "vgpu": True},
        }
    }

    info = queue_server.build_launch_context()

    assert info["layers"]["core"] is True
    assert info["layers"]["tronii"] is True
    assert info["layers"]["vgpu"] is True
    assert "TRON_MASTER_URL" in info["install_command"]
    assert "curl" in info["install_command"]

"""Tests for TRON-II DePIN integration."""
import pytest
from tron_ii.depin import DePINClient
from tron_ii.cli import parse_args


def test_depin_client_requires_requests(monkeypatch):
    monkeypatch.setitem(__import__('sys').modules, 'requests', None)
    client = DePINClient('http://localhost:9001')
    with pytest.raises(RuntimeError, match='requests is required'):  # type: ignore
        client.submit_job('ai_task', {'foo': 'bar'})


def test_parse_args_depin_flags():
    args = parse_args([
        '--depin-master-url', 'http://example.com:9001',
        '--depin-priority', '5',
        '--depin-requires-gpu',
    ])
    assert args.depin_master_url == 'http://example.com:9001'
    assert args.depin_priority == 5
    assert args.depin_requires_gpu is True

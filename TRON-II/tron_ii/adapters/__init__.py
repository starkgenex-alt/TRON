"""Adapters package for integrating external OSS libraries as hybrids."""

from .ray_adapter import RayAdapter
from .sb3_adapter import SB3Adapter

try:
    from .transformers_adapter import TransformersAdapter
    __all__ = ["SB3Adapter", "RayAdapter", "TransformersAdapter"]
except ImportError:
    __all__ = ["SB3Adapter", "RayAdapter"]


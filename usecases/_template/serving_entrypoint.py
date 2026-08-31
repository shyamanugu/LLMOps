"""Reference serving entrypoint — copy this into a real usecase's own
folder, replacing 10-serving-hosting's empty-registry `main.py`. Registers
this usecase's actual pipeline(s) so `POST /pipelines/{name}/run` has
something real to dispatch to; this becomes the real Container image's
entrypoint (see platform/services/10-serving-hosting/README.md).
"""
from serving.app import create_app
from serving.pipeline_registry import PipelineRegistry

from .pipeline import build_pipeline

registry = PipelineRegistry()
registry.register(build_pipeline())

app = create_app(registry)

"""The reusable LLMOps framework (called the 'platform' in the v2 deck).

Build once, reuse for every use case. One readable Python file per component:
    config, model_management, prompt_management, guardrails, observability, rag, tools,
    evaluation, pipeline.

Note: this folder is named 'framework' rather than 'platform' because 'platform' is the name of a
Python standard-library module — reusing it would shadow the standard library and break imports.
"""

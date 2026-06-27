# Local Demo Testing Guidelines

AegisQA local demos should use sanitized ticket fixtures and local providers only. A demo workflow is valid when it can load a structured ticket, generate coverage, produce Robot Framework automation, validate artifacts, execute with either Robot or a controlled mock adapter, investigate evidence, generate a report, and archive memory.

Use deterministic demo mode for PM presentations when Ollama is not available. Use Ollama mode when the local machine has the configured chat and embedding models installed.

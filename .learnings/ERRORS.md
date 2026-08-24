## [ERR-20260823-001] apply_patch

**Logged**: 2026-08-23T00:00:00+03:00
**Priority**: low
**Status**: resolved
**Area**: docs

### Summary
A broad notebook patch failed because its serialized traceback context did not match exactly.

### Error
```
apply_patch verification failed: Failed to find expected lines in notebook/RAG.ipynb
```

### Context
- Attempted to replace the entire stored error output while updating the dotenv cell.
- The notebook's JSON escaping made the patch context brittle.

### Suggested Fix
Use narrower source-only patches for notebook JSON, then validate with `python -m json.tool`.

### Metadata
- Reproducible: yes
- Related Files: notebook/RAG.ipynb

### Resolution
- **Resolved**: 2026-08-23T00:00:00+03:00
- **Notes**: Switched to a narrow source-cell edit.

---

## [ERR-20260824-001] uv_add_structlog

**Logged**: 2026-08-24T00:00:00+03:00
**Priority**: medium
**Status**: resolved
**Area**: config

### Summary
`uv add structlog` could not build the editable project because the declared `llmops` package did not exist.

### Error
```
Expected a Python module at: src/llmops/__init__.py
```

### Context
- `pyproject.toml` uses the `uv_build` backend and exposes `llmops = "llmops:main"`.
- The configured source package directory was missing.

### Suggested Fix
Restore `src/llmops/__init__.py` with the declared `main` entry point before adding dependencies.

### Metadata
- Reproducible: yes
- Related Files: pyproject.toml, src/llmops/__init__.py

### Resolution
- **Resolved**: 2026-08-24T00:00:00+03:00
- **Notes**: Added the missing package module and then added `structlog` through uv.

---

## [ERR-20260824-002] pyright_check

**Logged**: 2026-08-24T00:00:00+03:00
**Priority**: low
**Status**: pending
**Area**: tests

### Summary
The repository environment does not expose the `pyright` CLI for static verification.

### Error
```
/bin/bash: line 1: pyright: command not found
```

### Context
- Attempted to verify `multi_doc_chat/utils/file_io.py` after a Pylance type fix.

### Suggested Fix
Install or expose Pyright in the development environment, then run `pyright multi_doc_chat/utils/file_io.py`.

### Metadata
- Reproducible: yes
- Related Files: multi_doc_chat/utils/file_io.py

---

## [ERR-20260824-003] upload_helper_runtime_test

**Logged**: 2026-08-24T00:00:00+03:00
**Priority**: low
**Status**: pending
**Area**: tests

### Summary
The direct runtime test could not import the module because `structlog` is absent from the active interpreter.

### Error
```
ModuleNotFoundError: No module named 'structlog'
```

### Context
- Importing `multi_doc_chat.utils.file_io` loads the project's custom logger, which requires `structlog`.

### Suggested Fix
Use the project-managed environment with dependencies installed before running the runtime test.

### Metadata
- Reproducible: yes
- Related Files: multi_doc_chat/utils/file_io.py, multi_doc_chat/logger/cutom_logger.py

---

## [ERR-20260824-004] evaluation_notebook_validation

**Logged**: 2026-08-24T00:00:00+03:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
The new evaluation-path strings in the notebook were missing their closing quotes.

### Error
```
SyntaxError: unterminated string literal (detected at line 8)
```

### Context
- Validating the edited third cell by executing its JSON source exposed invalid Python before notebook use.

### Suggested Fix
Validate notebook cells after source edits and ensure JSON-escaped Python string literals retain both quotes.

### Metadata
- Reproducible: yes
- Related Files: notebook/Evaluations.ipynb

### Resolution
- **Resolved**: 2026-08-24T00:00:00+03:00
- **Notes**: Restored both closing quotes and re-ran validation.

---

"""
Skills registry — auto-discovers skill packages and collects their tools and prompts.

Each skill is a Python package in this directory with:
- TOOLS: list of @tool decorated functions
- PROMPT: str with instructions for the agent about this skill
"""
import importlib
import pkgutil


def load_all_skills():
    """Scan skills/ subpackages, collect TOOLS and PROMPT from each."""
    tools, prompts = [], []
    for importer, name, ispkg in pkgutil.iter_modules(__path__):
        if ispkg:
            mod = importlib.import_module(f".{name}", __package__)
            tools.extend(getattr(mod, "TOOLS", []))
            prompt = getattr(mod, "PROMPT", "")
            if prompt:
                prompts.append(prompt)
    return tools, "\n\n".join(prompts)

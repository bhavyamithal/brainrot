"""Content generation package for brainrot platform.

This package provides script generation with template-based content creation
for short-form video production.

Classes:
    ScriptTemplate: Template definition for script generation
    ScriptGenerator: Main generator with LLM integration

Template Types:
    - news_synthesis: Tech news summary with analysis
    - explainer: Concept explanation with examples
"""

from brainrot.content.script_generator import ScriptGenerator, ScriptTemplate

__all__ = ["ScriptGenerator", "ScriptTemplate"]

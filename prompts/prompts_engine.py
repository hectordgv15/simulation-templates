from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import frontmatter
from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    meta,
)


class PromptOrchestrator:
    """
    Manages Jinja2 prompt templates.

    Features:
    - Loads template content from a configured templates directory.
    - Renders prompts with provided variables (`kwargs`).
    - Extracts frontmatter metadata and detects undeclared variables used by the template.
    """

    _env: Environment | None = None

    @classmethod
    def _get_env(cls, templates_dir: str = "prompts/templates") -> Environment:
        """
        Return (and cache) a configured Jinja2 Environment.

        Notes:
        - Uses StrictUndefined so rendering fails fast when a required variable is missing.
        - Caches the environment to avoid recreating it on every call.
        """
        templates_path = Path(__file__).parent.parent / templates_dir

        if cls._env is None:
            cls._env = Environment(
                loader = FileSystemLoader(templates_path),
                undefined = StrictUndefined,
            )

        return cls._env

    @staticmethod
    def _load_post(template_name: str) -> frontmatter.Post:
        """
        Load a `.j2` template and return a `frontmatter.Post` object (content, metadata).

        Args:
            template_name: Template name without extension.

        Raises:
            FileNotFoundError: If the template cannot be found by the configured loader.
        """
        env = PromptOrchestrator._get_env()
        template_path = f"{template_name}.j2"

        _, filename, _ = env.loader.get_source(env, template_path)

        try:
            with open(filename, "r", encoding = "utf-8") as file:
                return frontmatter.load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Template not found: '{template_path}' in the configured templates directory."
            ) from e

    @staticmethod
    def get_prompt(template_name: str, **kwargs: Any) -> str:
        """
        Render the given template with the provided variables.

        Args:
            template_name: Template name without extension.
            **kwargs: Variables available to the Jinja2 renderer.

        Returns:
            The rendered prompt as a string.

        Raises:
            ValueError: If Jinja2 raises a rendering error.
        """
        env = PromptOrchestrator._get_env()
        post = PromptOrchestrator._load_post(template_name) 

        jinja_template = env.from_string(post.content)

        try:
            return jinja_template.render(**kwargs)
        except TemplateError as e:
            raise ValueError(
                f"Error rendering template '{template_name}': {e}"
            ) from e

    @staticmethod
    def get_template_info(template_name: str) -> Dict[str, Any]:
        """
        Return template metadata and a list of variables referenced by the template.

        It parses the template content and finds undeclared variables (placeholders that
        must be provided at render time).

        Returns:
            A dict with:
            - name: template name
            - description: from frontmatter (or default)
            - author: from frontmatter (or default)
            - variables: sorted list of undeclared variables used in the template
            - frontmatter: the full metadata dict
        """
        env = PromptOrchestrator._get_env()
        post = PromptOrchestrator._load_post(template_name)

        ast = env.parse(post.content)
        variables = sorted(meta.find_undeclared_variables(ast))

        return {
            "name": template_name,
            "description": post.metadata.get("description", "No description provided"),
            "author": post.metadata.get("author", "Unknown"),
            "variables": variables,
            "frontmatter": post.metadata,
        }

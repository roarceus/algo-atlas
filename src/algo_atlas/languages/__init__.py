"""Language support registry for AlgoAtlas."""

from typing import Optional

from algo_atlas.languages.base import LanguageInfo, LanguageSupport, SyntaxResult, TestResult

# Registry of language slug -> LanguageSupport instance
_registry: dict[str, LanguageSupport] = {}

# Default language slug
_default_slug: str = "python3"


def register(language: LanguageSupport) -> None:
    """Register a language support instance.

    Args:
        language: LanguageSupport instance to register.
    """
    info = language.info()
    for slug in info.leetcode_slugs:
        _registry[slug] = language
    # Also register by primary slug
    _registry[info.slug] = language


def get_language(slug: str) -> Optional[LanguageSupport]:
    """Get a language support instance by slug.

    Args:
        slug: Language slug (e.g. "python3", "javascript").

    Returns:
        LanguageSupport instance or None if not found.
    """
    _ensure_registered()
    return _registry.get(slug)


def get_language_by_extension(extension: str) -> Optional[LanguageSupport]:
    """Get a language support instance by file extension.

    Args:
        extension: File extension including dot (e.g. ".py", ".js").

    Returns:
        LanguageSupport instance or None if not found.
    """
    _ensure_registered()
    for lang in _registry.values():
        if lang.info().file_extension == extension:
            return lang
    return None


def list_languages() -> list[LanguageInfo]:
    """List all registered languages.

    Returns:
        List of LanguageInfo for all registered languages (deduplicated).
    """
    _ensure_registered()
    seen: set[str] = set()
    result: list[LanguageInfo] = []
    for lang in _registry.values():
        info = lang.info()
        if info.slug not in seen:
            seen.add(info.slug)
            result.append(info)
    return result


def default_language() -> LanguageSupport:
    """Get the default language support instance.

    Returns:
        The default LanguageSupport (Python).
    """
    lang = get_language(_default_slug)
    if lang is None:
        raise RuntimeError(f"Default language '{_default_slug}' is not registered")
    return lang


def _ensure_registered() -> None:
    """Lazily register built-in languages on first access."""
    if _registry:
        return
    # Import here to avoid circular imports
    from algo_atlas.languages.python import PythonLanguage
    from algo_atlas.languages.javascript import JavaScriptLanguage
    from algo_atlas.languages.typescript import TypeScriptLanguage
    register(PythonLanguage())
    register(JavaScriptLanguage())
    register(TypeScriptLanguage())


__all__ = [
    "LanguageInfo",
    "LanguageSupport",
    "SyntaxResult",
    "TestResult",
    "register",
    "get_language",
    "get_language_by_extension",
    "list_languages",
    "default_language",
]

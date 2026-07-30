"""AI pipeline package.

Import submodules directly (e.g. `from ai.prompt_builder import build_prompt`)
to avoid eagerly loading torch / OpenCV during lightweight unit tests.
"""

__all__ = ["build_prompt", "ImageGenerator", "apply_pencil_sketch"]


def __getattr__(name: str):
    if name == "build_prompt":
        from .prompt_builder import build_prompt

        return build_prompt
    if name == "ImageGenerator":
        from .image_generator import ImageGenerator

        return ImageGenerator
    if name == "apply_pencil_sketch":
        from .sketch_processor import apply_pencil_sketch

        return apply_pencil_sketch
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

"""Shared rich-text field configuration (django-prose-editor)."""

from typing import Any

from django_prose_editor.fields import ProseEditorField

# Formatting available to editors. The same list drives server-side sanitization (nh3),
# so stored HTML can only contain what the editor is able to produce.
RICH_TEXT_EXTENSIONS: dict[str, Any] = {
    "Bold": True,
    "Italic": True,
    "Underline": True,
    "Strike": True,
    "Heading": {"levels": [2, 3, 4]},
    "BulletList": True,
    "OrderedList": True,
    "ListItem": True,
    "Blockquote": True,
    "HorizontalRule": True,
    "HardBreak": True,
    "Link": {"enableTarget": True, "protocols": ["http", "https", "mailto", "tel"]},
    "Table": True,
    "TableRow": True,
    "TableHeader": True,
    "TableCell": True,
    "History": True,
}


def RichTextField(*args: Any, **kwargs: Any) -> ProseEditorField:
    """A sanitized HTML text field edited with ProseMirror in the admin."""
    kwargs.setdefault("extensions", RICH_TEXT_EXTENSIONS)
    kwargs.setdefault("sanitize", True)
    kwargs.setdefault("blank", True)
    return ProseEditorField(*args, **kwargs)

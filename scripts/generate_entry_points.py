import ast
from pathlib import Path


def describe_node(node: ast.AST) -> str:
    """Return a human-readable description for non-def top-level statements."""

    if isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
        value = node.value.value
        if isinstance(value, str):
            return "Module docstring"
    if isinstance(node, ast.Import):
        parts = []
        for alias in node.names:
            if alias.asname:
                parts.append(f"import {alias.name} as {alias.asname}")
            else:
                parts.append(f"import {alias.name}")
        return ", ".join(parts) or "import"
    if isinstance(node, ast.ImportFrom):
        module = node.module or ""
        parts = []
        for alias in node.names:
            if alias.asname:
                parts.append(f"from {module} import {alias.name} as {alias.asname}")
            else:
                parts.append(f"from {module} import {alias.name}")
        return ", ".join(parts) or f"from {module} import *"

    def collect_targets(target):
        if isinstance(target, ast.Name):
            return [target.id]
        if isinstance(target, (ast.Tuple, ast.List)):
            names = []
            for elt in target.elts:
                names.extend(collect_targets(elt))
            return names
        return []

    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        targets = []
        if isinstance(node, ast.Assign):
            for target in node.targets:
                targets.extend(collect_targets(target))
        elif isinstance(node, ast.AnnAssign):
            targets.extend(collect_targets(node.target))
        if targets:
            return "Assignment to " + ", ".join(f"`{name}`" for name in targets)
        return "Assignment"
    if isinstance(node, ast.AugAssign):
        targets = collect_targets(node.target)
        if targets:
            return "Augmented assignment to " + ", ".join(f"`{name}`" for name in targets)
        return "Augmented assignment"
    if isinstance(node, ast.If):
        return "Top-level if statement"
    if isinstance(node, ast.For):
        return "Top-level for loop"
    if isinstance(node, ast.While):
        return "Top-level while loop"
    if isinstance(node, ast.With):
        return "Top-level with statement"
    if isinstance(node, ast.Try):
        return "Top-level try block"
    if isinstance(node, ast.AsyncFunctionDef):
        return f"async def {node.name}(…)"
    if isinstance(node, ast.ClassDef):  # Shouldn't happen here, handled earlier
        return f"class {node.name}"
    if isinstance(node, ast.FunctionDef):  # Shouldn't happen here, handled earlier
        return f"def {node.name}(…)"

    return f"Top-level {node.__class__.__name__}"

ROOT = Path(__file__).resolve().parents[1] / "AGI_Evolutive"

entries = []

for path in sorted(ROOT.rglob("*.py")):
    rel_path = path.relative_to(ROOT)
    try:
        module_ast = ast.parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        entries.append((str(rel_path), ["<parse_error>"], [], [f"Parse error: {exc}"]))
        continue

    classes = []
    functions = []
    others = []

    for node in module_ast.body:
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        else:
            description = describe_node(node)
            if description:
                others.append(description)

    entries.append((str(rel_path), classes, functions, others))

output_lines = [
    "# Public entry points inventory",
    "",
    "Generated inventory of top-level classes, functions, and other statements per module in `AGI_Evolutive`.",
    "",
    "Existing LLM wrapper helpers that only front single heuristics will be removed during the refactor and therefore are not treated as final entry points.",
    "",
    "Each section lists definitions and statements that will be considered for consolidation into single-call LLM orchestrators.",
]

for rel_path, classes, functions, others in entries:
    output_lines.append("")
    output_lines.append(f"## {rel_path}")
    if classes:
        public_classes = [c for c in classes if not c.startswith("_")]
        private_classes = [c for c in classes if c.startswith("_")]
        output_lines.append("")
        output_lines.append("### Classes")
        if public_classes:
            for name in public_classes:
                output_lines.append(f"- `{name}`")
        if private_classes:
            output_lines.append("- _(private)_ " + ", ".join(f"`{name}`" for name in private_classes))
    else:
        output_lines.append("")
        output_lines.append("### Classes")
        output_lines.append("- *(none)*")

    if functions:
        public_functions = [f for f in functions if not f.startswith("_")]
        private_functions = [f for f in functions if f.startswith("_")]
        output_lines.append("")
        output_lines.append("### Functions")
        if public_functions:
            for name in public_functions:
                output_lines.append(f"- `{name}`")
        if private_functions:
            output_lines.append("- _(private)_ " + ", ".join(f"`{name}`" for name in private_functions))
        if not public_functions and not private_functions:
            output_lines.append("- *(none)*")
    else:
        output_lines.append("")
        output_lines.append("### Functions")
        output_lines.append("- *(none)*")

    output_lines.append("")
    output_lines.append("### Other top-level statements")
    if others:
        for item in others:
            output_lines.append(f"- {item}")
    else:
        output_lines.append("- *(none)*")

output_path = Path(__file__).resolve().parents[1] / "docs" / "llm_refactor_entry_points.md"
output_path.write_text("\n".join(output_lines) + "\n", encoding="utf-8")
print(f"Wrote inventory to {output_path.relative_to(Path(__file__).resolve().parents[1])}")

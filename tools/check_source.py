"""Check Glue's Python 3.9 syntax and the embedded SQL without executing AWS calls."""
import ast
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    paths = [root / "cloud/glue_energy_pipeline.py"] + sorted((root / "include/src").glob("*.py"))
    for path in paths:
        ast.parse(path.read_text(), filename=str(path), feature_version=(3, 9))
    tree = ast.parse(paths[0].read_text())
    sql = next(ast.literal_eval(node.value) for node in tree.body
               if isinstance(node, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "TRANSFORM_SQL" for t in node.targets))
    expected = (root / "include/sql/transform_energy_marts.sql").read_text()
    if sql != expected:
        raise ValueError("Glue embedded SQL differs from the repository SQL; update both before deployment")
    print("Python 3.9 syntax and embedded SQL checks passed")


if __name__ == "__main__":
    main()

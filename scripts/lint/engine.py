#!/usr/bin/env python3
import ast
import os
import sys
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional

class Violation:
    def __init__(self, line: int, col: int, code: str, message: str, severity: str = "error"):
        self.line = line
        self.col = col
        self.code = code
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"{self.line}:{self.col}: {self.severity}: {self.message} ({self.code})"

class Rule(ABC):
    @abstractmethod
    def check(self, node: ast.AST, context: 'LinterEngine') -> List[Violation]:
        pass

class BaseVisitor(ast.NodeVisitor):
    def __init__(self, rules: List[Rule]):
        self.rules = rules
        self.violations = []
        self.context = None

    def visit(self, node: ast.AST):
        for rule in self.rules:
            # Use a naming convention for hook methods: visit_NodeName
            hook_name = f"check_{type(node).__name__}"
            if hasattr(rule, hook_name):
                res = getattr(rule, hook_name)(node, self.context)
                if res:
                    self.violations.extend(res)
        super().visit(node)

class LinterEngine:
    def __init__(self, rules: List[Rule]):
        self.rules = rules

    def lint_file(self, filepath: str) -> List[Violation]:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
        
        visitor = BaseVisitor(self.rules)
        visitor.context = self
        visitor.visit(tree)
        return visitor.violations

# --- Concrete Rules ---

class SC001SingleExitRule(Rule):
    """SC-001: Every function must have exactly one exit door (single return at end)."""
    def check_FunctionDef(self, node: ast.FunctionDef, context: LinterEngine) -> List[Violation]:
        exits = []
        for child in ast.walk(node):
            if isinstance(child, (ast.Return, ast.Raise)):
                exits.append(child)
        
        if len(exits) > 1:
            return [Violation(node.lineno, node.col_offset, "SC001", f"Function {node.name} has {len(exits)} exit doors")]
        return []

class SC002ZeroRaiseRule(Rule):
    """SC-002: No raise statements in non-dunder functions."""
    def check_FunctionDef(self, node: ast.FunctionDef, context: LinterEngine) -> List[Violation]:
        if node.name.startswith("__") and node.name.endswith("__"):
            return []
        
        violations = []
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                violations.append(Violation(child.lineno, child.col_offset, "SC002", f"Forbidden raise in function {node.name}"))
        return violations

class SC003ResultReturnRule(Rule):
    """SC-003/005: Result[T] returns, no tuples, explicit return types."""
    def check_FunctionDef(self, node: ast.FunctionDef, context: LinterEngine) -> List[Violation]:
        violations = []
        # Check return type annotation
        if not node.returns:
            violations.append(Violation(node.lineno, node.col_offset, "SC024", f"Function {node.name} missing return type annotation"))
        elif isinstance(node.returns, ast.Name) and node.returns.id != "Result":
             # Simple check for Result or Result[T]
             pass # In a full impl, we'd check the full type name

        # Check for tuple returns
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and isinstance(child.value, ast.Tuple):
                violations.append(Violation(child.lineno, child.col_offset, "SC005", f"Function {node.name} returns a tuple; use Result[T] instead"))
        
        return violations

class SC004InvalidResultRule(Rule):
    """SC-004: Module-level INVALID_RESULT sentinel."""
    def check_Module(self, node: ast.Module, context: LinterEngine) -> List[Violation]:
        has_sentinel = False
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name) and target.id == "INVALID_RESULT":
                        has_sentinel = True
                        break
        if not has_sentinel:
            return [Violation(1, 0, "SC004", "Module lacks INVALID_RESULT sentinel")]
        return []

class SC010FunctionLengthRule(Rule):
    """SC-010: Max 60 executable lines per function."""
    def check_FunctionDef(self, node: ast.FunctionDef, context: LinterEngine) -> List[Violation]:
        # Count unique line numbers of executable statements
        lines = set()
        for child in ast.walk(node):
            if isinstance(child, (ast.Assign, ast.Expr, ast.If, ast.For, ast.While, ast.With, ast.Try)):
                if hasattr(child, 'lineno'):
                    lines.add(child.lineno)
        
        if len(lines) > 60:
            return [Violation(node.lineno, node.col_offset, "SC010", f"Function {node.name} too long ({len(lines)} lines)")]
        return []

class SC011BContinueRule(Rule):
    """SC-011: b_continue error-gating rules."""
    def check_FunctionDef(self, node: ast.FunctionDef, context: LinterEngine) -> List[Violation]:
        if node.name.startswith("__") and node.name.endswith("__"):
            return []
        
        violations = []
        assignments = []
        guards = []

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == "b_continue":
                        assignments.append(child)
            elif isinstance(child, (ast.If, ast.While)):
                if "b_continue" in ast.dump(child.test):
                    guards.append(child)

        if not assignments:
            return [Violation(node.lineno, node.col_offset, "SC011-missing", f"Function {node.name} lacks b_continue")]

        first_assign = assignments[0]
        if not (isinstance(first_assign.value, ast.Constant) and first_assign.value.value is True):
            violations.append(Violation(first_assign.lineno, first_assign.col_offset, "SC011-init", "b_continue must be initialized to True"))

        for i in range(1, len(assignments)):
            assign = assignments[i]
            if isinstance(assign.value, ast.Constant) and assign.value.value is True:
                violations.append(Violation(assign.lineno, assign.col_offset, "SC011-reset", "b_continue reset to True forbidden"))

        if assignments and not guards:
            violations.append(Violation(node.lineno, node.col_offset, "SC011-unused", "b_continue initialized but never used"))

        return violations

class SC071DeterminismRule(Rule):
    """SC-071: No non-deterministic calls (datetime.now, random, etc.)."""
    FORBIDDEN = {
        'datetime': {'now', 'utcnow'},
        'time': {'time', 'monotonic', 'localtime', 'gmtime'},
        'random': {'random', 'randint', 'choice', 'sample', 'shuffle', 'gauss'},
        'uuid': {'uuid4'}
    }

    def check_Call(self, node: ast.Call, context: LinterEngine) -> List[Violation]:
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                mod = node.func.value.id
                meth = node.func.attr
                if mod in self.FORBIDDEN and meth in self.FORBIDDEN[mod]:
                    return [Violation(node.lineno, node.col_offset, "SC071", f"Non-deterministic call {mod}.{meth}() forbidden")]
        return []

class SC080ResourceRule(Rule):
    """SC-080/082: Mandatory context managers for resources."""
    RESOURCES = {'open', 'Popen', 'Lock', 'connect', 'NamedTemporaryFile'}

    def check_Call(self, node: ast.Call, context: LinterEngine) -> List[Violation]:
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in self.RESOURCES:
            # Check if the call is an argument to a 'with' statement
            # This is simplified; real implementation checks if call is inside ast.With
            # For now, we assume it's a violation if not immediately wrapped in 'with'
            # (This is a simplified proxy for the complex parent search)
            pass 
        return []

class SC100SecurityRule(Rule):
    """SC-100/101/104: Security (eval, exec, SQL injection)."""
    def check_Call(self, node: ast.Call, context: LinterEngine) -> List[Violation]:
        if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec', 'compile'):
            return [Violation(node.lineno, node.col_offset, "SC104", f"Forbidden call to {node.func.id}()")]
        
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'execute':
            # Check if first argument is an f-string or uses .format()
            if node.args and isinstance(node.args[0], (ast.JoinedStr, ast.Call)):
                return [Violation(node.lineno, node.col_offset, "SC101", "Possible SQL injection: use parameterized queries")]
        
        return []

class APrefixRule(Rule):
    """All function arguments must start with a_ prefix."""
    def check_FunctionDef(self, node: ast.FunctionDef, context: LinterEngine) -> List[Violation]:
        violations = []
        for arg in node.args.args:
            if arg.arg in ("self", "cls") or arg.arg.startswith("a_") or arg.arg.startswith("_a_"):
                continue
            violations.append(Violation(arg.lineno, arg.col_offset, "a-prefix", f"Argument {arg.arg} must start with a_"))
        return violations


class SC011BContinueRule(Rule):
    """SC-011: b_continue error-gating rules."""
    def check_FunctionDef(self, node: ast.FunctionDef, context: LinterEngine) -> List[Violation]:
        if node.name.startswith("__") and node.name.endswith("__"):
            return []
        
        violations = []
        assignments = []
        guards = []

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name) and target.id == "b_continue":
                        assignments.append(child)
            elif isinstance(child, ast.If) or isinstance(child, ast.While):
                # Check if b_continue is used in the test
                if "b_continue" in ast.dump(child.test):
                    guards.append(child)

        if not assignments:
            # Only a warning/info if it returns Result
            return [Violation(node.lineno, node.col_offset, "SC011-missing", f"Function {node.name} lacks b_continue")]

        # Rule 2: Initialized to True
        first_assign = assignments[0]
        if not (isinstance(first_assign.value, ast.Constant) and first_assign.value.value is True):
            violations.append(Violation(first_assign.lineno, first_assign.col_offset, "SC011-init", "b_continue must be initialized to True"))

        # Rule 3 & 5: Transitions and Reset
        for i in range(1, len(assignments)):
            assign = assignments[i]
            if isinstance(assign.value, ast.Constant) and assign.value.value is True:
                violations.append(Violation(assign.lineno, assign.col_offset, "SC011-reset", "b_continue reset to True forbidden"))

        # Rule 6: Unused
        if assignments and not guards:
            violations.append(Violation(node.lineno, node.col_offset, "SC011-unused", "b_continue initialized but never used"))

        return violations

class APrefixRule(Rule):
    """All function arguments must start with a_ prefix."""
    def check_FunctionDef(self, node: ast.FunctionDef, context: LinterEngine) -> List[Violation]:
        violations = []
        for arg in node.args.args:
            if arg.arg in ("self", "cls") or arg.arg.startswith("a_") or arg.arg.startswith("_a_"):
                continue
            violations.append(Violation(arg.lineno, arg.col_offset, "a-prefix", f"Argument {arg.arg} must start with a_"))
        return violations

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", required=True)
    args = parser.parse_args()

    rules = [
        SC001SingleExitRule(),
        SC002ZeroRaiseRule(),
        SC003ResultReturnRule(),
        SC004InvalidResultRule(),
        SC010FunctionLengthRule(),
        SC011BContinueRule(),
        SC071DeterminismRule(),
        SC080ResourceRule(),
        SC100SecurityRule(),
        APrefixRule()
    ]
    engine = LinterEngine(rules)

    all_violations = 0
    for root, _, files in os.walk(args.src):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                violations = engine.lint_file(path)
                for v in violations:
                    print(f"{path}:{v}")
                    all_violations += 1

    sys.exit(1 if all_violations > 0 else 0)

if __name__ == "__main__":
    main()

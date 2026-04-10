"""
Built-in Calculator Plugin
"""

from ..base import Plugin, PluginManifest, PluginType, PluginPermission
import ast
import operator

class CalculatorPlugin(Plugin):
    manifest = PluginManifest(
        name="calculator",
        version="1.0.0",
        description="Perform mathematical calculations",
        author="Local Agent Team",
        type=PluginType.TOOL,
        permissions=[PluginPermission.READ]
    )
    
    def initialize(self, agent) -> bool:
        self.agent = agent
        return True
    
    def get_tools(self):
        return {
            "calculate": self._calculate
        }
    
    def _calculate(self, expression: str, token: str = None) -> str:
        """Safe mathematical expression evaluator"""
        # Allowed operators and functions
        allowed_ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
        }
        
        def safe_eval(node):
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.BinOp):
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                return allowed_ops[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = safe_eval(node.operand)
                if isinstance(node.op, ast.USub):
                    return -operand
                return operand
            else:
                raise ValueError(f"Unsupported operation: {type(node)}")
        
        try:
            tree = ast.parse(expression, mode='eval')
            result = safe_eval(tree.body)
            return f"📐 Result: {result}"
        except Exception as e:
            return f"Calculation error: {e}"

"""Calculator tool for mathematical operations."""

import math
from typing import Dict

from src.core.tools.base import BaseTool, ToolParameter


class CalculatorTool(BaseTool):
    """Performs mathematical calculations and evaluates expressions."""

    def get_parameters(self) -> Dict[str, ToolParameter]:
        """Get tool parameters."""
        return {
            "expression": ToolParameter(
                name="expression",
                type="string",
                description="Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')",
                required=True,
            )
        }

    async def execute(self, expression: str) -> Dict[str, any]:
        """
        Execute mathematical calculation.

        Args:
            expression: Math expression to evaluate

        Returns:
            Calculation result
        """
        try:
            # Create safe namespace with math functions
            safe_dict = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                # Math module functions
                "sqrt": math.sqrt,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
                "ceil": math.ceil,
                "floor": math.floor,
                "factorial": math.factorial,
            }

            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, safe_dict)

            return {
                "expression": expression,
                "result": result,
                "formatted": f"{expression} = {result}",
            }

        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {e}")

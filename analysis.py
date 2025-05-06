import os
import re
import math
from collections import Counter

class URScriptAnalyzer:
    """
    Analyzes URScript files and computes code quality metrics including a URScript‐tailored 
    Maintainability Index (URMI) and a Reusability Index.

    The new Maintainability Index (URMI) is defined as:

      URMI = max(0, min(100, 100 
                        - (0.03 * total_lines)
                        - (0.5 * cyclomatic_complexity)
                        - (0.03 * average_function_length)
                        + (1.5 * comment_density)
                        - (1.0 * global_variables)))

    Additional metrics include:
      - Relative McCabe Index (complexity relative to file size)
      - Maximum Nesting Depth
      - Halstead Metrics (operators, operands, volume, difficulty, effort)
      - Dependency Density (include directives as a percentage of lines)
      - Concurrency Metrics (usage of thread-related commands)
      - Naming Convention Lowercase Ratio (consistency of variable naming)
    """
    def __init__(self, file_path):
        self.file_path = file_path
        with open(file_path, "r", encoding="utf-8") as file:
            self.lines = file.readlines()

    def analyze(self):
        lines = self.lines
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if line.strip() == "")
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        global_vars = sum(1 for line in lines if "global" in line)
        
        # Functions and their metrics, supporting both "def" and "sec" declarations.
        functions = re.findall(r"(?:def|sec)\s+(\w+)\s*\(", "".join(lines))
        function_count = len(functions)
        function_metrics = self.analyze_functions(lines)
        
        # Global control flow metrics
        if_count = sum(1 for line in lines if re.search(r"\bif\b", line))
        elif_count = sum(1 for line in lines if re.search(r"\belif\b", line))
        while_count = sum(1 for line in lines if re.search(r"\bwhile\b", line))
        for_count = sum(1 for line in lines if re.search(r"\bfor\b", line))
        loop_count = while_count + for_count
        
        # Count boolean operators as additional decision points.
        and_count = sum(1 for line in lines if re.search(r"\band\b", line))
        or_count = sum(1 for line in lines if re.search(r"\bor\b", line))
        xor_count = sum(1 for line in lines if re.search(r"\bxor\b", line))
        
        # Global cyclomatic complexity
        cyclomatic_complexity = if_count + elif_count + loop_count + and_count + or_count + xor_count + (function_count if function_count > 0 else 1)
        relative_mccabe_index = round((cyclomatic_complexity / total_lines) * 100, 2) if total_lines > 0 else 0
        
        # Motion commands (for extra context)
        motion_commands = ["movej", "movel", "movep"]
        motion_counts = {cmd: sum(1 for line in lines if cmd in line) for cmd in motion_commands}
        
        # Additional robotics commands
        robotics_commands = {
            "set_payload": sum(1 for line in lines if "set_payload" in line),
            "set_tcp": sum(1 for line in lines if "set_tcp" in line),
            "socket_open": sum(1 for line in lines if "socket_open" in line),
            "socket_close": sum(1 for line in lines if "socket_close" in line),
            "get_actual_joint_positions": sum(1 for line in lines if "get_actual_joint_positions" in line),
            "get_target_joint_positions": sum(1 for line in lines if "get_target_joint_positions" in line),
            "sleep": sum(1 for line in lines if "sleep(" in line)
        }
        
        # Duplicate lines (ignoring blank lines)
        non_empty_lines = [line for line in lines if line.strip()]
        line_counts = Counter(non_empty_lines)
        duplicate_lines = {line: count for line, count in line_counts.items() if count > 1}
        
        # Safety feature keywords
        safety_keywords = ["protective_stop", "force_mode", "set_safety_mode"]
        safety_counts = {kw: sum(1 for line in lines if kw in line) for kw in safety_keywords}
        
        # Variable analysis
        variable_pattern = re.compile(r"(\w+)\s*=.*")
        variable_names = variable_pattern.findall("".join(lines))
        var_counts = Counter(variable_names)
        non_lowercase_vars = [var for var in var_counts if var != var.lower()]
        
        # Additional Quality Metrics
        average_function_length = (sum(metric["lines"] for metric in function_metrics.values()) / function_count) if function_count > 0 else 0
        comment_density = (comment_lines / total_lines * 100) if total_lines > 0 else 0
        duplicate_ratio = (sum(duplicate_lines.values()) / total_lines * 100) if total_lines > 0 else 0
        
        # Compute additional metrics:
        max_nesting_depth = self.compute_max_nesting_depth(lines)
        halstead_metrics = self.compute_halstead_metrics(lines)
        dependency_count = sum(1 for line in lines if re.search(r"\binclude\b", line))
        dependency_density = round((dependency_count / total_lines * 100), 2) if total_lines > 0 else 0
        concurrency_keywords = ["thread", "run", "join", "kill"]
        concurrency_counts = {kw: sum(1 for line in lines if re.search(r"\b" + re.escape(kw) + r"\b", line)) for kw in concurrency_keywords}
        total_vars = len(var_counts)
        lowercase_ratio = round(((total_vars - len(non_lowercase_vars)) / total_vars * 100), 2) if total_vars > 0 else 0
        
        # Revised Maintainability Index tailored for URScript.
        MI = 100 - (0.03 * total_lines) \
                 - (0.5 * cyclomatic_complexity) \
                 - (0.03 * average_function_length) \
                 + (1.5 * comment_density) \
                 - (1.0 * global_vars)
        maintainability_index = max(0, min(100, MI))
        maintainability_index = round(maintainability_index, 2)
        
        # Reusability Index (heuristic)
        RI = (12 * function_count) - (average_function_length) - (7 * global_vars) \
             + (0.8 * comment_density) - (1.5 * duplicate_ratio) + 20
        reusability_index = max(0, min(100, RI))
        reusability_index = round(reusability_index, 2)
        
        analysis_report = {
            "File": os.path.basename(self.file_path),
            "Total Lines": total_lines,
            "Blank Lines": blank_lines,
            "Comment Lines": comment_lines,
            "Comment Density (%)": round(comment_density, 2),
            "Global Variables": global_vars,
            "Function Count": function_count,
            "Function Names": functions,
            "Function Metrics (Name: {'lines': count, 'mccabe': index})": function_metrics,
            "Average Function Length": round(average_function_length, 2),
            "If Statements": if_count,
            "Elif Statements": elif_count,
            "While Loops": while_count,
            "For Loops": for_count,
            "Total Loops": loop_count,
            "Cyclomatic Complexity (Global McCabe Index)": cyclomatic_complexity,
            "Relative McCabe Index (%)": relative_mccabe_index,
            "Maintainability Index (URScript)": maintainability_index,
            "Reusability Index (URScript)": reusability_index,
            "Duplicate Lines Ratio (%)": round(duplicate_ratio, 2),
            "Motion Commands": motion_counts,
            "Robotics Commands": robotics_commands,
            "Safety Features Used": safety_counts,
            "Maximum Nesting Depth": max_nesting_depth,
            "Halstead Metrics": halstead_metrics,
            "Dependency Density (%)": dependency_density,
            "Concurrency Metrics": concurrency_counts,
            "Top 5 Variables": var_counts.most_common(5),
            "Non-lowercase Variable Names Count": len(non_lowercase_vars),
            "Naming Convention Lowercase Ratio (%)": lowercase_ratio
        }
        return analysis_report

    def analyze_functions(self, lines):
        """
        Extracts functions and computes their lengths (in lines) and individual McCabe indices.
        Supports both "def" and "sec" declarations.
        Assumes that lines indented after a function definition belong to that function.
        Returns a dictionary mapping function names to a dict with keys 'lines' and 'mccabe'.
        """
        function_metrics = {}
        i = 0
        while i < len(lines):
            line = lines[i]
            match = re.match(r"\s*(?:def|sec)\s+(\w+)\s*\(", line)
            if match:
                func_name = match.group(1)
                function_body_lines = []
                function_body_lines.append(line)
                i += 1
                # Collect all indented lines as part of the function body.
                while i < len(lines) and (lines[i].startswith("    ") or lines[i].startswith("\t")):
                    function_body_lines.append(lines[i])
                    i += 1
                count_lines = len(function_body_lines)
                function_body = "".join(function_body_lines)
                mcCabe = self.getMcCabeIndex(function_body)
                function_metrics[func_name] = {"lines": count_lines, "mccabe": mcCabe}
            else:
                i += 1
        return function_metrics

    def compute_max_nesting_depth(self, lines):
        """
        Computes the maximum nesting depth in the file by tracking indentation levels.
        A new level is considered when the current line has greater indentation than the previous non-empty line.
        """
        max_depth = 0
        stack = []
        for line in lines:
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip(" "))
            if not stack or indent > stack[-1]:
                stack.append(indent)
            else:
                while stack and stack[-1] > indent:
                    stack.pop()
                stack.append(indent)
            max_depth = max(max_depth, len(stack))
        return max_depth

    def compute_halstead_metrics(self, lines):
        """
        Computes basic Halstead metrics:
          - n1: number of distinct operators
          - n2: number of distinct operands
          - N1: total operators count
          - N2: total operands count
          - Volume, Difficulty, and Effort.
        """
        code = "".join(lines)
        operator_set = set([
            "if", "elif", "while", "for", "def", "sec", "return", "global",
            "and", "or", "xor", "not",
            "+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">=",
            "(", ")", "[", "]", "{", "}", ":", ",", "."
        ])
        tokens = re.findall(r"[A-Za-z_]\w*|[^\sA-Za-z_]", code)
        operators = []
        operands = []
        for token in tokens:
            if token in operator_set:
                operators.append(token)
            else:
                operands.append(token)
        distinct_operators = set(operators)
        distinct_operands = set(operands)
        N1 = len(operators)
        N2 = len(operands)
        n1 = len(distinct_operators)
        n2 = len(distinct_operands)
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        return {
            "Distinct Operators (n1)": n1,
            "Distinct Operands (n2)": n2,
            "Total Operators (N1)": N1,
            "Total Operands (N2)": N2,
            "Vocabulary": vocabulary,
            "Length": length,
            "Volume": round(volume, 2),
            "Difficulty": round(difficulty, 2),
            "Effort": round(effort, 2)
        }

    def getCleanerExtra(self):
        """
        Returns a cleaner function that removes comments and string literals.
        This version more closely mimics Sokrates' cleaning:
          - Splits text into lines,
          - Removes any content following a '#' (comment),
          - Removes string literals,
          - Trims each line, then rejoins.
        """
        def cleaner(text):
            lines = text.splitlines()
            cleaned_lines = []
            for line in lines:
                # Remove comment portion
                if "#" in line:
                    line = line.split("#")[0]
                cleaned_lines.append(line.strip())
            cleaned = "\n".join(cleaned_lines)
            # Remove double-quoted and single-quoted string literals.
            cleaned = re.sub(r'("([^"\\]|\\.)*")|(\'([^\'\\]|\\.)*\')', "", cleaned)
            return cleaned
        return cleaner

    def getMcCabeIndex(self, body):
        """
        Calculates the McCabe (cyclomatic) complexity based on URScript rules,
        identical to the Sokrates Java implementation.
        Steps:
         1. Remove comments and string literals using getCleanerExtra.
         2. Convert the cleaned text into a single-line string with extra spaces.
         3. Count occurrences of control-flow tokens.
         4. Add one to the total count.
        """
        cleaner = self.getCleanerExtra()
        content = cleaner(body)
        # Convert content to a single-line string with extra spaces.
        bodyForSearch = " " + content.replace("\n", " ")
        bodyForSearch = bodyForSearch.replace("(", " (").replace("{", " {")
        
        mcCabeIndex = 1
        mcCabeIndex += bodyForSearch.count(" if ")
        mcCabeIndex += bodyForSearch.count(" elif ")
        mcCabeIndex += bodyForSearch.count(" for ")
        mcCabeIndex += bodyForSearch.count(" while ")
        mcCabeIndex += bodyForSearch.count(" and ")
        mcCabeIndex += bodyForSearch.count(" or ")
        mcCabeIndex += bodyForSearch.count(" xor ")
        return mcCabeIndex

# Example usage:
if __name__ == "__main__":
    file_path = "path/to/your/file.script"  # Replace with your URScript file path
    analyzer = URScriptAnalyzer(file_path)
    report = analyzer.analyze()
    for key, value in report.items():
        print(f"{key}: {value}")

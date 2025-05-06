import os
import re
from collections import Counter

class URTextAnalyzer:
    """
    Analyzes URScript description TXT files (exported from Polyscope).
    
    Computes text-specific metrics including:
      - Total Lines and Non-Empty Lines
      - Frequency counts of known commands (e.g., MoveJ, MoveL, Force, Call, Wait, 3FG Grip, 3FG Release)
      - Indentation statistics
      - Duplicate Lines Count
      
    In addition, it computes three new heuristic indexes:
    
      • Text Cyclomatic Complexity (TCC): Defined as (number of top-level sections) + 1.
         A section is any non-empty line with no leading spaces.
      
      • Text Maintainability Index (TMI): 
           TMI = max(0, min(100, 100 - (0.02 * total_lines)
                                  - (2.0 * duplicate_ratio)
                                  - (0.5 * TCC)))
         where duplicate_ratio is the percentage of duplicate non-empty lines.
      
      • Text Reusability Index (TRI):
           TRI = max(0, min(100, (sections * 15) - (0.1 * total_lines) - (duplicate_ratio)))
         where sections is the number of top-level (non-indented) lines.
    """
    def __init__(self, file_path):
        self.file_path = file_path
        with open(file_path, "r", encoding="utf-8") as file:
            self.lines = file.readlines()
    
    def analyze(self):
        lines = self.lines
        total_lines = len(lines)
        non_empty_lines = [line for line in lines if line.strip()]
        non_empty_count = len(non_empty_lines)
        
        # Known commands frequency (case-insensitive search)
        known_commands = ["MoveJ", "MoveL", "Force", "Call", "Wait", "3FG Grip", "3FG Release"]
        command_counts = {cmd: 0 for cmd in known_commands}
        for line in non_empty_lines:
            for cmd in known_commands:
                if cmd.lower() in line.lower():
                    command_counts[cmd] += 1
        
        # Indentation statistics: assuming spaces are used.
        indent_levels = []
        for line in non_empty_lines:
            indent = len(line) - len(line.lstrip(" "))
            indent_levels.append(indent)
        max_indent = max(indent_levels) if indent_levels else 0
        avg_indent = sum(indent_levels) / len(indent_levels) if indent_levels else 0
        
        # Duplicate lines (ignoring whitespace)
        stripped_lines = [line.strip() for line in non_empty_lines]
        line_counts = Counter(stripped_lines)
        duplicate_lines = {line: count for line, count in line_counts.items() if count > 1}
        duplicate_count = len(duplicate_lines)
        # Compute duplicate ratio as a percentage of non-empty lines
        duplicate_ratio = (sum(duplicate_lines.values()) / non_empty_count * 100) if non_empty_count > 0 else 0
        
        # Determine sections: top-level lines (no indentation)
        sections = sum(1 for line in non_empty_lines if len(line) == len(line.lstrip(" ")))
        # Text Cyclomatic Complexity (TCC): sections + 1
        TCC = sections + 1
        
        # Text Maintainability Index (TMI):
        TMI = 100 - (0.02 * total_lines) - (2.0 * duplicate_ratio) - (0.5 * TCC)
        TMI = max(0, min(100, TMI))
        TMI = round(TMI, 2)
        
        # Text Reusability Index (TRI):
        TRI = (sections * 15) - (0.1 * total_lines) - duplicate_ratio
        TRI = max(0, min(100, TRI))
        TRI = round(TRI, 2)
        
        analysis_report = {
            "Total Lines": total_lines,
            "Non-Empty Lines": non_empty_count,
            "Known Commands Frequency": command_counts,
            "Maximum Indentation": max_indent,
            "Average Indentation": round(avg_indent, 2),
            "Duplicate Lines Count": duplicate_count,
            "Duplicate Ratio (%)": round(duplicate_ratio, 2),
            "Top-level Sections": sections,
            "Text Cyclomatic Complexity (TCC)": TCC,
            "Text Maintainability Index (TMI)": TMI,
            "Text Reusability Index (TRI)": TRI
        }
        return analysis_report

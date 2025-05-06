import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
from analysis import URScriptAnalyzer
from translator import translate_description
from txt_analyzer import URTextAnalyzer

class URScriptAnalyzerApp:
    """
    GUI application for analyzing URScript files and their accompanying TXT description files.
    
    - Users upload URScript (.script) and TXT (.txt) files separately.
    - "Analyze Scripts" processes script files with code metrics (including maintainability and reusability)
      and, if available, processes the matching TXT file with translation.
    - "Analyze TXT Files" separately processes the TXT files for text-specific metrics.
    - The "Results" tab displays the combined results in clearly segmented boxes.
      Long details (like function names and metrics) are hidden behind a "Display Function Details" button,
      which opens them in a separate window.
    - The results pane is now scrollable via trackpad/mouse wheel.
    - The "Dashboard" tab visualizes key quality metrics.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("URScript Analyzer Tool")
        self.root.geometry("1200x800")
        self.style = tb.Style('flatly')
        
        # Dictionaries keyed by base file name (without extension)
        self.script_files = {}  # base_name -> full path (.script)
        self.desc_files = {}    # base_name -> full path (.txt)
        
        # Combined results: base_name -> {"analysis": ..., "translation": ..., "txt_analysis": ...}
        self.results = {}
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.setup_upload_tab()
        self.setup_results_tab()
        self.setup_dashboard_tab()
    
    def setup_upload_tab(self):
        self.upload_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.upload_frame, text="Upload & Analyze")
        
        # Upload URScript files
        script_label = ttk.Label(self.upload_frame, text="Upload URScript Files (.script):", font=("Arial", 12))
        script_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.btn_upload_scripts = ttk.Button(self.upload_frame, text="Upload Script Files", command=self.upload_script_files)
        self.btn_upload_scripts.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.script_listbox = tk.Listbox(self.upload_frame, height=8)
        self.script_listbox.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        
        # Upload TXT files
        desc_label = ttk.Label(self.upload_frame, text="Upload Description Files (.txt):", font=("Arial", 12))
        desc_label.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        self.btn_upload_desc = ttk.Button(self.upload_frame, text="Upload TXT Files", command=self.upload_desc_files)
        self.btn_upload_desc.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.desc_listbox = tk.Listbox(self.upload_frame, height=8)
        self.desc_listbox.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        
        # Analyze button for scripts and translation
        self.btn_analyze = ttk.Button(self.upload_frame, text="Analyze Scripts", command=self.analyze_all, bootstyle="success")
        self.btn_analyze.grid(row=3, column=0, columnspan=2, padx=10, pady=20)
        
        # New button: Analyze TXT Files (using URTextAnalyzer)
        self.btn_analyze_txt = ttk.Button(self.upload_frame, text="Analyze TXT Files", command=self.analyze_txt_files, bootstyle="info")
        self.btn_analyze_txt.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
    
    def setup_results_tab(self):
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="Results")
        
        # Left pane: list of base file names
        left_frame = ttk.Frame(self.results_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        results_label = ttk.Label(left_frame, text="Files:", font=("Arial", 12))
        results_label.pack(pady=5)
        self.results_listbox = tk.Listbox(left_frame, height=25)
        self.results_listbox.pack(fill=tk.Y, padx=5, pady=5)
        self.results_listbox.bind("<<ListboxSelect>>", self.display_result)
        
        # Right pane: a scrollable canvas to hold the segmented results
        self.canvas = tk.Canvas(self.results_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(self.results_frame, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        # Bind mouse wheel for trackpad scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Create an interior frame to hold the results
        self.results_container = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.results_container, anchor="nw")
        self.results_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
    
    def _on_mousewheel(self, event):
        # Cross-platform scrolling support
        if self.root.tk.call("tk", "windowingsystem") == "aqua":
            self.canvas.yview_scroll(-1 * int(event.delta), "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def setup_dashboard_tab(self):
        self.dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        
        dashboard_label = ttk.Label(self.dashboard_frame, text="Quality Metrics Dashboard", font=("Arial", 14, "bold"))
        dashboard_label.pack(pady=10)
        
        columns = ("File", "URMI", "Reusability")
        self.tree = ttk.Treeview(self.dashboard_frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def upload_script_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("URScript Files", "*.script"), ("All Files", "*.*")])
        for path in file_paths:
            base_name = os.path.splitext(os.path.basename(path))[0]
            self.script_files[base_name] = path
            if base_name not in self.script_listbox.get(0, tk.END):
                self.script_listbox.insert(tk.END, base_name)
    
    def upload_desc_files(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        for path in file_paths:
            base_name = os.path.splitext(os.path.basename(path))[0]
            self.desc_files[base_name] = path
            if base_name not in self.desc_listbox.get(0, tk.END):
                self.desc_listbox.insert(tk.END, base_name)
    
    def analyze_all(self):
        # Analyze each script file and run translation on matching TXT file if available.
        self.results.clear()
        self.results_listbox.delete(0, tk.END)
        for base_name, script_path in self.script_files.items():
            try:
                analyzer = URScriptAnalyzer(script_path)
                analysis_report = analyzer.analyze()
            except Exception as e:
                analysis_report = {"Error": f"Failed to analyze script: {e}"}
            
            # Translation from TXT file (if available)
            if base_name in self.desc_files:
                try:
                    translation = translate_description(self.desc_files[base_name])
                except Exception as e:
                    translation = [f"Failed to translate description: {e}"]
            else:
                translation = ["No description file provided."]
            
            self.results[base_name] = {
                "analysis": analysis_report,
                "translation": translation
            }
            self.results_listbox.insert(tk.END, base_name)
            
            # Update dashboard with quality metrics from script analysis
            cc = analysis_report.get("Maintainability Index (URScript)", "N/A")
            ri = analysis_report.get("Reusability Index (URScript)", "N/A")
            self.tree.insert("", tk.END, values=(base_name, cc, ri))
        
        messagebox.showinfo("Analysis Complete", "Script analysis and translation complete!")
        self.notebook.select(self.results_frame)
    
    def analyze_txt_files(self):
        # Analyze each TXT file using URTextAnalyzer and add the results to self.results
        for base_name, txt_path in self.desc_files.items():
            try:
                txt_analyzer = URTextAnalyzer(txt_path)
                txt_analysis = txt_analyzer.analyze()
            except Exception as e:
                txt_analysis = {"Error": f"Failed to analyze TXT file: {e}"}
            if base_name in self.results:
                self.results[base_name]["txt_analysis"] = txt_analysis
            else:
                self.results[base_name] = {"txt_analysis": txt_analysis}
                self.results_listbox.insert(tk.END, base_name)
        messagebox.showinfo("TXT Analysis Complete", "TXT file analysis complete!")
        self.notebook.select(self.results_frame)
    
    def clear_results_container(self):
        # Remove all child widgets in the results container
        for widget in self.results_container.winfo_children():
            widget.destroy()
    
    def create_section(self, parent, title, content_dict):
        # Create a labeled frame for a section with a given title and content.
        # If there are function details, add a button to show them separately.
        section = ttk.LabelFrame(parent, text=title, padding=(10, 5))
        # Check for keys to hide by default.
        hidden_keys = {}
        keys_to_show = {}
        for key, value in content_dict.items():
            if key in ["Function Names", "Function Metrics (Name: Lines)"]:
                hidden_keys[key] = value
            else:
                keys_to_show[key] = value
        for key, value in keys_to_show.items():
            row = ttk.Frame(section)
            row.pack(fill=tk.X, padx=5, pady=2)
            key_label = ttk.Label(row, text=f"{key}:", width=30, anchor="w")
            key_label.pack(side=tk.LEFT)
            value_label = ttk.Label(row, text=str(value), anchor="w", wraplength=800)
            value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # If there are hidden keys, add a button to display details in a new window.
        if hidden_keys:
            btn = ttk.Button(section, text="Display Function Details",
                             command=lambda: self.show_function_details(hidden_keys))
            btn.pack(pady=5)
        return section
    
    def create_text_section(self, parent, title, content_list):
        # Create a labeled frame for text content (like translation), displaying each line.
        section = ttk.LabelFrame(parent, text=title, padding=(10, 5))
        for line in content_list:
            line_label = ttk.Label(section, text=line, anchor="w", wraplength=800)
            line_label.pack(fill=tk.X, padx=5, pady=1)
        return section
    
    def show_function_details(self, details):
        # Open a new Toplevel window showing the function details.
        detail_win = tk.Toplevel(self.root)
        detail_win.title("Function Details")
        detail_win.geometry("600x400")
        container = ttk.Frame(detail_win, padding=10)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Use a scrolled Text widget for details.
        text_widget = tk.Text(container, wrap=tk.WORD)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Insert the details.
        for key, value in details.items():
            text_widget.insert(tk.END, f"{key}:\n{value}\n\n")
        
        text_widget.config(state=tk.DISABLED)
    
    def display_result(self, event):
        selection = self.results_listbox.curselection()
        if not selection:
            return
        
        base_name = self.results_listbox.get(selection[0])
        combined_result = self.results.get(base_name, {})
        analysis = combined_result.get("analysis", {})
        translation = combined_result.get("translation", [])
        txt_analysis = combined_result.get("txt_analysis", {})
        
        self.clear_results_container()
        
        header = ttk.Label(self.results_container, text=f"Results for: {base_name}", font=("Arial", 14, "bold"))
        header.pack(pady=5)
        
        if analysis:
            analysis_section = self.create_section(self.results_container, "URScript Analysis Report", analysis)
            analysis_section.pack(fill=tk.X, padx=10, pady=5)
        
        if translation:
            translation_section = self.create_text_section(self.results_container, "Description Translation", translation)
            translation_section.pack(fill=tk.X, padx=10, pady=5)
        
        if txt_analysis:
            txt_section = self.create_section(self.results_container, "TXT File Analysis", txt_analysis)
            txt_section.pack(fill=tk.X, padx=10, pady=5)
        
        self.results_container.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = URScriptAnalyzerApp(root)
    root.mainloop()

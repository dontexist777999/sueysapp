import sys
import argparse
import tkinter as tk
from tkinter import messagebox, ttk
from converter import (
    convert_to_diazepam, 
    EQUIVALENCE_TABLE, 
    DISPLAY_NAMES, 
    DISCLAIMER, 
    get_equivalence_markdown,
    to_morphine_ome,
    list_all_equivalences,
    OPIOID_TABLE,
    normalize_drug_name,
    save_custom_drug,
    USER_OPIOID_TABLE,
    calculate_tolerance_development,
    get_history,
    DATA_VERSION,
    from_diazepam,
    from_morphine_ome
)

def run_cli():
    """Startet das Kommandozeilen-Interface."""
    parser = argparse.ArgumentParser(description="Medizinischer Umrechner für Benzodiazepine und Opioide.")
    
    # Gemeinsame Optionen
    parser.add_argument("-d", "--drug", help="Name des Medikaments (z.B. hydromorphone, tilidin, alprazolam)")
    parser.add_argument("-q", "--dose", type=float, help="Dosis (mg, µg für Fentanyl IV, µg/h für Fentanyl TD)")
    parser.add_argument("--list", action="store_true", help="Gibt die Äquivalenztabelle aus.")
    parser.add_argument("--gui", action="store_true", help="Startet die grafische Benutzeroberfläche.")
    parser.add_argument("--history", action="store_true", help="Zeigt die Historie der Datenänderungen an.")
    
    # Opioid-spezifische Optionen
    parser.add_argument("-r", "--route", default="oral", help="Verabreichungsweg (oral, iv, sc, sl, td). Standard: oral.")
    parser.add_argument("--previous-ome", type=float, help="Vorherige tägliche Morphin-OME (nur für Methadon nötig).")
    parser.add_argument("--discount", type=float, default=0.0, help="Abschlag für unvollständige Kreuztoleranz in Prozent (z.B. 30).")
    
    # Benzo-spezifische Optionen (optional zur Kompatibilität)
    parser.add_argument("--benzo", action="store_true", help="Explizit den Benzo-Umrechner nutzen.")

    args = parser.parse_args()

    if args.list:
        print(f"Daten-Version: {DATA_VERSION}")
        print("\n".join(list_all_equivalences()))
        print("\n" + get_equivalence_markdown())
        return

    if args.history:
        print(f"Historie der Datenänderungen (Version {DATA_VERSION}):")
        print("-" * 60)
        for entry in get_history():
            print(f"[{entry['date']}] {entry['type']} - {entry['drug']}: {entry['change']}")
        return

    if args.gui or len(sys.argv) == 1:
        start_gui()
        return

    if not args.drug or args.dose is None:
        parser.print_help()
        return

    try:
        drug_norm = normalize_drug_name(args.drug)
        
        # Prüfen ob es ein Opioid ist
        is_opioid = False
        for (d, r) in OPIOID_TABLE.keys():
            if d == drug_norm:
                is_opioid = True
                break
        
        if is_opioid and not args.benzo:
            ome = to_morphine_ome(args.drug, args.dose, args.route, args.previous_ome, args.discount)
            unit = "µg" if "fentanyl" in drug_norm else "mg"
            if "fentanyl" in drug_norm and args.route == "td":
                unit = "µg/h"
            print(f"\nErgebnis: {args.dose} {unit} {args.drug} ({args.route}) ≈ {ome} mg Morphin PO (OME)")
            if args.discount > 0:
                print(f"HINWEIS: Ein {args.discount}% Abschlag wurde angewendet.")
            else:
                print(f"HINWEIS: Bei Umstellung auf ein neues Opioid wird oft ein Abschlag von 30-50% empfohlen.")
        else:
            # Benzo Umrechnung
            equiv, factor = convert_to_diazepam(args.drug, args.dose)
            print(f"\nErgebnis: {args.dose} mg {args.drug} ≈ {equiv:.2f} mg Diazepam")
            print(f"Verhältnis: 1 mg {args.drug} ≈ {factor:.2f} mg Diazepam (Basis 10mg)")
        
        print(f"\n{DISCLAIMER}")

    except (ValueError, KeyError) as e:
        print(f"Fehler: {e}")
        if "Unbekanntes" in str(e):
            print("\nNutzen Sie --list um alle verfügbaren Medikamente anzuzeigen.")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

def start_gui():
    """Startet das Tkinter-Frontend."""
    root = tk.Tk()
    app = ConverterGUI(root)
    root.mainloop()

class ConverterGUI:
    """Klasse für die grafische Benutzeroberfläche mit tkinter."""
    def __init__(self, root):
        self.root = root
        self.root.title("Medizinischer Umrechner (Benzo & Opioid)")
        self.root.geometry("600x700")
        
        # Design-Themes Definition
        self.themes = {
            "Standard (Hell)": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "text_bg": "#ffffff",
                "text_fg": "#000000",
                "accent": "#0078d7",
                "header_fg": "#000000",
                "disclaimer_fg": "red"
            },
            "Dark Mode": {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "text_bg": "#1e1e1e",
                "text_fg": "#d4d4d4",
                "accent": "#3a3a3a",
                "header_fg": "#569cd6",
                "disclaimer_fg": "#f44336"
            },
            "Medizin-Blau": {
                "bg": "#e3f2fd",
                "fg": "#0d47a1",
                "text_bg": "#ffffff",
                "text_fg": "#0d47a1",
                "accent": "#1976d2",
                "header_fg": "#1565c0",
                "disclaimer_fg": "#d32f2f"
            },
            "Smaragd-Grün": {
                "bg": "#e8f5e9",
                "fg": "#1b5e20",
                "text_bg": "#ffffff",
                "text_fg": "#1b5e20",
                "accent": "#4caf50",
                "header_fg": "#2e7d32",
                "disclaimer_fg": "#c62828"
            }
        }
        self.current_theme = tk.StringVar(value="Standard (Hell)")
        self.style = ttk.Style()
        
        self.setup_menu()
        self.setup_ui()
        self.apply_theme()

    def setup_menu(self):
        menubar = tk.Menu(self.root)
        
        # Datei Menü
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Beenden", command=self.root.quit)
        menubar.add_cascade(label="Datei", menu=file_menu)
        
        # Design Menü
        design_menu = tk.Menu(menubar, tearoff=0)
        for theme_name in self.themes.keys():
            design_menu.add_radiobutton(
                label=theme_name, 
                variable=self.current_theme, 
                command=self.apply_theme
            )
        menubar.add_cascade(label="Design", menu=design_menu)
        
        # Info/Hilfe Menü
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Über", command=self.show_about)
        help_menu.add_command(label="Haftungsausschluss", command=self.show_disclaimer)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        
        self.root.config(menu=menubar)

    def apply_theme(self):
        theme = self.themes[self.current_theme.get()]
        
        # Root Hintergrund
        self.root.config(bg=theme["bg"])
        
        # Styles konfigurieren
        self.style.configure("TFrame", background=theme["bg"])
        self.style.configure("TLabel", background=theme["bg"], foreground=theme["fg"])
        self.style.configure("TButton", padding=5)
        self.style.configure("TCheckbutton", background=theme["bg"], foreground=theme["fg"])
        self.style.configure("TRadiobutton", background=theme["bg"], foreground=theme["fg"])
        self.style.configure("Header.TLabel", font=("Helvetica", 12, "bold"), foreground=theme["header_fg"])
        self.style.configure("Disclaimer.TLabel", foreground=theme["disclaimer_fg"])
        
        # Notebook Style
        self.style.configure("TNotebook", background=theme["bg"])
        self.style.configure("TNotebook.Tab", padding=[10, 5])
        
        # Combobox Style (ttk)
        self.style.map("TCombobox", fieldbackground=[("readonly", theme["text_bg"])])
        self.style.configure("TCombobox", selectbackground=theme["accent"])

        # Alle Widgets rekursiv aktualisieren für Nicht-ttk Widgets
        self.update_widget_colors(self.root, theme)

    def update_widget_colors(self, parent, theme):
        for child in parent.winfo_children():
            widget_type = child.winfo_class()
            
            if widget_type == "Text":
                child.config(bg=theme["text_bg"], fg=theme["text_fg"], insertbackground=theme["text_fg"])
            elif widget_type == "Entry" and not isinstance(child, ttk.Entry):
                child.config(bg=theme["text_bg"], fg=theme["text_fg"], insertbackground=theme["text_fg"])
            elif widget_type == "Label" and not isinstance(child, ttk.Label):
                child.config(bg=theme["bg"], fg=theme["fg"])
            elif widget_type == "TNotebook":
                 self.update_widget_colors(child, theme)
            elif hasattr(child, "winfo_children"):
                self.update_widget_colors(child, theme)

    def show_about(self):
        messagebox.showinfo("Über Umrechner", 
                            "Medizinischer Umrechner v1.1\n\nBerechnung von Benzodiazepin- und Opioid-Äquivalenzdosen.\n\nAutor: Junie")

    def show_disclaimer(self):
        messagebox.showwarning("Haftungsausschluss", DISCLAIMER)

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Benzo Tab
        self.benzo_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.benzo_frame, text="Benzodiazepine")
        self.setup_benzo_ui()
        
        # Opioid Tab
        self.opioid_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.opioid_frame, text="Opioide")
        self.setup_opioid_ui()

        # Umstellungs Tab
        self.conversion_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.conversion_frame, text="Umstellung")
        self.setup_conversion_ui()
        
        # Toleranz & Custom Tab
        self.advanced_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.advanced_frame, text="Erweitert")
        self.setup_advanced_ui()

        # Historie Tab
        self.history_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.history_frame, text="Historie")
        self.setup_history_ui()

    def setup_about_tab(self):
        # Optionaler Tab für Disclaimer/Info
        info_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(info_frame, text="Info")
        ttk.Label(info_frame, text="Haftungsausschluss", style="Header.TLabel").pack(pady=(0, 10))
        ttk.Label(info_frame, text=DISCLAIMER, wraplength=550).pack(pady=(0, 20))
        ttk.Label(info_frame, text="Version: 1.5").pack(side=tk.BOTTOM, anchor=tk.E)

    def setup_benzo_ui(self):
        # Disclaimer
        ttk.Label(self.benzo_frame, text=DISCLAIMER, wraplength=550, style="Disclaimer.TLabel").pack(pady=(0, 10))
        
        # Medikamenten-Auswahl
        ttk.Label(self.benzo_frame, text="Medikament auswählen:").pack(anchor=tk.W)
        self.med_var = tk.StringVar()
        self.med_combo = ttk.Combobox(self.benzo_frame, textvariable=self.med_var, state="readonly")
        self.med_combo['values'] = sorted(list(DISPLAY_NAMES.values()))
        self.med_combo.pack(fill=tk.X, pady=(0, 10))
        self.med_combo.current(0)
        
        # Dosis-Eingabe
        ttk.Label(self.benzo_frame, text="Dosis in mg:").pack(anchor=tk.W)
        self.dose_entry = ttk.Entry(self.benzo_frame)
        self.dose_entry.pack(fill=tk.X, pady=(0, 20))
        self.dose_entry.insert(0, "0")
        
        # Umrechnen Button
        ttk.Button(self.benzo_frame, text="Umrechnen", command=self.calculate_benzo).pack(pady=(0, 10))
        
        # Ergebnis Label
        self.benzo_result_var = tk.StringVar(value="Ergebnis: -")
        ttk.Label(self.benzo_frame, textvariable=self.benzo_result_var, style="Header.TLabel").pack(pady=(0, 10))
        
        # Tabelle
        ttk.Label(self.benzo_frame, text="Äquivalenztabelle:").pack(anchor=tk.W)
        table_text = tk.Text(self.benzo_frame, height=10, width=50)
        table_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        table_text.insert(tk.END, get_equivalence_markdown())
        table_text.config(state=tk.DISABLED)

    def setup_opioid_ui(self):
        # Medikamenten-Auswahl
        ttk.Label(self.opioid_frame, text="Opioid auswählen:").pack(anchor=tk.W)
        self.op_med_var = tk.StringVar()
        self.op_med_combo = ttk.Combobox(self.opioid_frame, textvariable=self.op_med_var, state="readonly")
        # Eindeutige Medikamentennamen sammeln
        op_names = sorted(list(set(d.capitalize() for (d, r) in OPIOID_TABLE.keys())))
        self.op_med_combo['values'] = op_names
        self.op_med_combo.pack(fill=tk.X, pady=(0, 10))
        self.op_med_combo.current(0)
        
        # Weg-Auswahl
        ttk.Label(self.opioid_frame, text="Verabreichungsweg:").pack(anchor=tk.W)
        self.route_var = tk.StringVar()
        self.route_combo = ttk.Combobox(self.opioid_frame, textvariable=self.route_var, state="readonly")
        self.route_combo['values'] = ["oral", "iv", "sc", "sl", "td"]
        self.route_combo.pack(fill=tk.X, pady=(0, 10))
        self.route_combo.current(0)
        
        # Dosis-Eingabe
        ttk.Label(self.opioid_frame, text="Dosis (mg / µg für Fentanyl):").pack(anchor=tk.W)
        self.op_dose_entry = ttk.Entry(self.opioid_frame)
        self.op_dose_entry.pack(fill=tk.X, pady=(0, 10))
        self.op_dose_entry.insert(0, "0")
        
        # Previous OME (für Methadon)
        ttk.Label(self.opioid_frame, text="Vorherige OME (nur für Methadon):").pack(anchor=tk.W)
        self.prev_ome_entry = ttk.Entry(self.opioid_frame)
        self.prev_ome_entry.pack(fill=tk.X, pady=(0, 10))
        self.prev_ome_entry.insert(0, "")
        
        # Abschlag Checkbox & Custom CTF
        ttk.Label(self.opioid_frame, text="Cross-Tolerance Abschlag (%):").pack(anchor=tk.W)
        self.discount_val_var = tk.StringVar(value="0")
        self.discount_entry = ttk.Entry(self.opioid_frame, textvariable=self.discount_val_var)
        self.discount_entry.pack(fill=tk.X, pady=(0, 5))
        
        self.discount_var = tk.BooleanVar()
        self.ctf_check = ttk.Checkbutton(self.opioid_frame, text="30% Standard-Abschlag nutzen", variable=self.discount_var)
        self.ctf_check.pack(anchor=tk.W, pady=(0, 10))
        
        # Umrechnen Button
        ttk.Button(self.opioid_frame, text="Umrechnen", command=self.calculate_opioid).pack(pady=(0, 10))
        
        # Ergebnis Label
        self.op_result_var = tk.StringVar(value="Ergebnis: -")
        ttk.Label(self.opioid_frame, textvariable=self.op_result_var, style="Header.TLabel").pack(pady=(0, 10))
        
        # Tabelle
        ttk.Label(self.opioid_frame, text="Hinweise:").pack(anchor=tk.W)
        op_table_text = tk.Text(self.opioid_frame, height=8, width=50)
        op_table_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        op_table_text.insert(tk.END, "\n".join(list_all_equivalences()))
        op_table_text.config(state=tk.DISABLED)

    def setup_conversion_ui(self):
        # Disclaimer
        ttk.Label(self.conversion_frame, text=DISCLAIMER, wraplength=550, style="Disclaimer.TLabel").pack(pady=(0, 10))
        
        # Typ-Auswahl (Opioid vs Benzo)
        self.conv_type_var = tk.StringVar(value="Benzo")
        type_frame = ttk.Frame(self.conversion_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Radiobutton(type_frame, text="Benzodiazepine", variable=self.conv_type_var, value="Benzo", command=self.update_conv_ui).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(type_frame, text="Opioide", variable=self.conv_type_var, value="Opioid", command=self.update_conv_ui).pack(side=tk.LEFT)
        
        # Ausgangs-Medikament
        ttk.Label(self.conversion_frame, text="Von Medikament:").pack(anchor=tk.W)
        self.conv_from_var = tk.StringVar()
        self.conv_from_combo = ttk.Combobox(self.conversion_frame, textvariable=self.conv_from_var, state="readonly")
        self.conv_from_combo.pack(fill=tk.X, pady=(0, 5))
        
        # Weg für Ausgang (nur für Opioide sichtbar)
        self.conv_from_route_label = ttk.Label(self.conversion_frame, text="Verabreichungsweg (von):")
        self.conv_from_route_var = tk.StringVar(value="oral")
        self.conv_from_route_combo = ttk.Combobox(self.conversion_frame, textvariable=self.conv_from_route_var, state="readonly", values=["oral", "iv", "sc", "sl", "td"])
        
        # Dosis
        ttk.Label(self.conversion_frame, text="Dosis:").pack(anchor=tk.W)
        self.conv_dose_entry = ttk.Entry(self.conversion_frame)
        self.conv_dose_entry.pack(fill=tk.X, pady=(0, 10))
        self.conv_dose_entry.insert(0, "0")
        
        # Ziel-Medikament
        ttk.Label(self.conversion_frame, text="Auf Medikament:").pack(anchor=tk.W)
        self.conv_to_var = tk.StringVar()
        self.conv_to_combo = ttk.Combobox(self.conversion_frame, textvariable=self.conv_to_var, state="readonly")
        self.conv_to_combo.pack(fill=tk.X, pady=(0, 5))
        
        # Weg für Ziel (nur für Opioide sichtbar)
        self.conv_to_route_label = ttk.Label(self.conversion_frame, text="Verabreichungsweg (auf):")
        self.conv_to_route_var = tk.StringVar(value="oral")
        self.conv_to_route_combo = ttk.Combobox(self.conversion_frame, textvariable=self.conv_to_route_var, state="readonly", values=["oral", "iv", "sc", "sl", "td"])

        # Umrechnen Button
        ttk.Button(self.conversion_frame, text="Dosis umstellen", command=self.calculate_conversion).pack(pady=(10, 10))
        
        # Ergebnis Label
        self.conv_result_var = tk.StringVar(value="Ergebnis: -")
        ttk.Label(self.conversion_frame, textvariable=self.conv_result_var, style="Header.TLabel", wraplength=550).pack(pady=(0, 10))
        
        self.update_conv_ui()

    def update_conv_ui(self):
        if self.conv_type_var.get() == "Benzo":
            # Benzo UI
            benzo_names = sorted(list(DISPLAY_NAMES.values()))
            self.conv_from_combo['values'] = benzo_names
            self.conv_to_combo['values'] = benzo_names
            self.conv_from_combo.current(0)
            self.conv_to_combo.current(0)
            
            self.conv_from_route_label.forget()
            self.conv_from_route_combo.forget()
            self.conv_to_route_label.forget()
            self.conv_to_route_combo.forget()
        else:
            # Opioid UI
            op_names = sorted(list(set(d.capitalize() for (d, r) in OPIOID_TABLE.keys() | USER_OPIOID_TABLE.keys())))
            self.conv_from_combo['values'] = op_names
            self.conv_to_combo['values'] = op_names
            self.conv_from_combo.current(0)
            self.conv_to_combo.current(0)
            
            # Pack order matters for visual layout
            self.conv_from_route_label.pack(after=self.conv_from_combo, anchor=tk.W)
            self.conv_from_route_combo.pack(after=self.conv_from_route_label, fill=tk.X, pady=(0, 5))
            
            self.conv_to_route_label.pack(after=self.conv_to_combo, anchor=tk.W)
            self.conv_to_route_combo.pack(after=self.conv_to_route_label, fill=tk.X, pady=(0, 5))

    def setup_advanced_ui(self):
        # Sektion: Benutzerdefinierte Medikamente
        ttk.Label(self.advanced_frame, text="Benutzerdefiniertes Opioid hinzufügen", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(self.advanced_frame, text="Name:").pack(anchor=tk.W)
        self.custom_name_entry = ttk.Entry(self.advanced_frame)
        self.custom_name_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(self.advanced_frame, text="Weg (z.B. oral, iv):").pack(anchor=tk.W)
        self.custom_route_entry = ttk.Entry(self.advanced_frame)
        self.custom_route_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(self.advanced_frame, text="Faktor zu oralem Morphin:").pack(anchor=tk.W)
        self.custom_factor_entry = ttk.Entry(self.advanced_frame)
        self.custom_factor_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(self.advanced_frame, text="Medikament speichern", command=self.add_custom_drug).pack(pady=(0, 15))
        
        ttk.Separator(self.advanced_frame, orient='horizontal').pack(fill='x', pady=10)
        
        # Sektion: Toleranz-Entwicklung
        ttk.Label(self.advanced_frame, text="Toleranz-Geschwindigkeits-Modell", style="Header.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        # Typ-Auswahl (Opioid vs Benzo)
        self.tol_type_var = tk.StringVar(value="Opioid (OME)")
        tol_type_frame = ttk.Frame(self.advanced_frame)
        tol_type_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Radiobutton(tol_type_frame, text="Opioid (OME)", variable=self.tol_type_var, value="Opioid (OME)", command=self.update_tol_labels).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(tol_type_frame, text="Benzo (mg Diazepam)", variable=self.tol_type_var, value="Benzo (mg Diazepam)", command=self.update_tol_labels).pack(side=tk.LEFT)
        
        self.tol_start_label = ttk.Label(self.advanced_frame, text="Start-Dosis (OME mg/Tag):")
        self.tol_start_label.pack(anchor=tk.W)
        self.tol_start_entry = ttk.Entry(self.advanced_frame)
        self.tol_start_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(self.advanced_frame, text="Zeitraum (Tage):").pack(anchor=tk.W)
        self.tol_days_entry = ttk.Entry(self.advanced_frame)
        self.tol_days_entry.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(self.advanced_frame, text="Steigerungsrate pro Tag (z.B. 0.02 für 2%):").pack(anchor=tk.W)
        self.tol_rate_entry = ttk.Entry(self.advanced_frame)
        self.tol_rate_entry.insert(0, "0.02")
        self.tol_rate_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(self.advanced_frame, text="Toleranz berechnen", command=self.calculate_tolerance).pack(pady=(0, 10))
        
        self.tol_result_var = tk.StringVar(value="Erwartetes Ergebnis: -")
        ttk.Label(self.advanced_frame, textvariable=self.tol_result_var, font=("Helvetica", 11, "bold")).pack(pady=(0, 10))

    def update_tol_labels(self):
        if self.tol_type_var.get() == "Opioid (OME)":
            self.tol_start_label.config(text="Start-Dosis (OME mg/Tag):")
        else:
            self.tol_start_label.config(text="Start-Dosis (mg Diazepam/Tag):")

    def setup_history_ui(self):
        ttk.Label(self.history_frame, text=f"Historie der Datenänderungen (Version {DATA_VERSION})", font=("Helvetica", 12, "bold")).pack(pady=(0, 10))
        
        self.history_text = tk.Text(self.history_frame, height=20, width=60)
        self.history_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        ttk.Button(self.history_frame, text="Aktualisieren", command=self.refresh_history).pack()
        self.refresh_history()

    def refresh_history(self):
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        for entry in get_history():
            line = f"[{entry['date']}] {entry['type']} - {entry['drug']}: {entry['change']}\n"
            self.history_text.insert(tk.END, line)
        self.history_text.config(state=tk.DISABLED)

    def add_custom_drug(self):
        try:
            name = self.custom_name_entry.get().strip()
            route = self.custom_route_entry.get().strip()
            factor = float(self.custom_factor_entry.get().replace(",", "."))
            
            if not name or not route:
                raise ValueError("Name und Weg dürfen nicht leer sein.")
            
            save_custom_drug(name, route, factor)
            messagebox.showinfo("Erfolg", f"Medikament {name} ({route}) wurde gespeichert.")
            
            # GUI aktualisieren
            self.refresh_history()
            
            # Update Combobox
            op_names = sorted(list(set(d.capitalize() for (d, r) in OPIOID_TABLE.keys() | USER_OPIOID_TABLE.keys())))
            self.op_med_combo['values'] = op_names
            
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def calculate_tolerance(self):
        try:
            start = float(self.tol_start_entry.get().replace(",", "."))
            days = int(self.tol_days_entry.get())
            rate = float(self.tol_rate_entry.get().replace(",", "."))
            
            result = calculate_tolerance_development(start, days, rate)
            unit = "mg OME" if self.tol_type_var.get() == "Opioid (OME)" else "mg Diazepam"
            self.tol_result_var.set(f"Erwartete Dosis nach {days} Tagen: {result} {unit}")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def calculate_benzo(self):
        try:
            display_name = self.med_var.get()
            med_key = None
            for key, val in DISPLAY_NAMES.items():
                if val == display_name:
                    med_key = key
                    break
            
            dose = float(self.dose_entry.get().replace(",", "."))
            equiv, factor = convert_to_diazepam(med_key, dose)
            self.benzo_result_var.set(f"{dose} mg {display_name} ≈ {equiv:.2f} mg Diazepam")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def calculate_conversion(self):
        try:
            dose = float(self.conv_dose_entry.get().replace(",", "."))
            if self.conv_type_var.get() == "Benzo":
                # Benzo Umrechnung
                from_display = self.conv_from_var.get()
                to_display = self.conv_to_var.get()
                
                from_key = next(k for k, v in DISPLAY_NAMES.items() if v == from_display)
                to_key = next(k for k, v in DISPLAY_NAMES.items() if v == to_display)
                
                # Erst in Diazepam
                diaz_equiv, _ = convert_to_diazepam(from_key, dose)
                # Dann in Zielmedikament
                target_dose = from_diazepam(to_key, diaz_equiv)
                
                self.conv_result_var.set(f"{dose} mg {from_display} ≈ {target_dose:.2f} mg {to_display}\n(entspricht {diaz_equiv:.2f} mg Diazepam)")
            else:
                # Opioid Umrechnung
                from_drug = self.conv_from_var.get()
                to_drug = self.conv_to_var.get()
                from_route = self.conv_from_route_var.get()
                to_route = self.conv_to_route_var.get()
                
                # Erst in OME (ohne Abschlag für die Zwischenrechnung)
                ome_equiv = to_morphine_ome(from_drug, dose, from_route)
                # Dann in Zielmedikament
                target_dose = from_morphine_ome(to_drug, ome_equiv, to_route)
                
                self.conv_result_var.set(f"{dose} mg {from_drug} ({from_route}) ≈ {target_dose:.2f} mg {to_drug} ({to_route})\n(entspricht {ome_equiv:.2f} mg OME)")
                
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

    def calculate_opioid(self):
        try:
            drug_input = self.op_med_var.get()
            drug = normalize_drug_name(drug_input)
            route = self.route_var.get()
            dose = float(self.op_dose_entry.get().replace(",", "."))
            
            prev_ome_str = self.prev_ome_entry.get().strip()
            prev_ome = float(prev_ome_str.replace(",", ".")) if prev_ome_str else None
            
            # Discount berechnen
            discount = 0.0
            if self.discount_var.get():
                discount = 30.0
            else:
                discount_str = self.discount_val_var.get().strip()
                discount = float(discount_str.replace(",", ".")) if discount_str else 0.0
            
            ome = to_morphine_ome(drug, dose, route, prev_ome, discount)
            unit = "µg" if "fentanyl" in drug else "mg"
            if "fentanyl" in drug and route == "td":
                unit = "µg/h"
            self.op_result_var.set(f"{dose} {unit} {drug_input} ≈ {ome} mg OME")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))

def main():
    run_cli()

if __name__ == "__main__":
    main()

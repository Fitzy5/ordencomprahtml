import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime
import os

# Function to load registry CSV with error handling
def load_registry_csv():
    try:
        return pd.read_csv("registry.csv", dtype=str)
    except FileNotFoundError:
        messagebox.showerror("Error", "Could not find 'registry.csv'. Please ensure it’s in the same directory.")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load registry CSV: {str(e)}")
        return None

# Function to load or initialize providers CSV
def load_providers_csv():
    provider_cols = ['provider', 'vendedor', 'direccion_proveedor', 'ubicacion_proveedor', 
                    'contacto_proveedor', 'correo_proveedor']
    try:
        if os.path.exists("providers.csv"):
            return pd.read_csv("providers.csv", dtype=str)
        else:
            # Initialize from registry.csv if providers.csv doesn't exist
            registry_df = load_registry_csv()
            if registry_df is None:
                return pd.DataFrame(columns=provider_cols)
            providers_df = registry_df[provider_cols].drop_duplicates(subset='provider')
            providers_df.to_csv("providers.csv", index=False)
            return providers_df
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load providers CSV: {str(e)}")
        return pd.DataFrame(columns=provider_cols)

# Main application class
class CSVSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Search Application")
        
        # Load registry CSV
        self.df = load_registry_csv()
        if self.df is None:
            self.root.destroy()
            return
        
        # Load providers CSV
        self.providers_df = load_providers_csv()
        self.provider_info = self.providers_df.set_index('provider').to_dict('index')
        
        # Define search fields mapping
        self.search_fields = {
            "Product Code": "code",
            "Order Number": "nro_oc",
            "Description": "description"
        }
        
        # Store selected provider for filtering
        self.selected_provider = tk.StringVar()
        
        # GUI setup
        self.setup_gui()
        
        # Initialize with all data displayed
        self.update_results()

    def setup_gui(self):
        # Main frame for search and filter controls
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(fill="x", padx=10, pady=5)
        
        # Search criteria dropdown
        tk.Label(self.control_frame, text="Search by:").grid(row=0, column=0, padx=5, pady=5)
        self.criteria_var = tk.StringVar()
        self.criteria_dropdown = ttk.Combobox(self.control_frame, 
                                            textvariable=self.criteria_var,
                                            values=list(self.search_fields.keys()),
                                            state="readonly")
        self.criteria_dropdown.grid(row=0, column=1, padx=5, pady=5)
        self.criteria_dropdown.set("Description")  # Default selection
        
        # Search entry field
        tk.Label(self.control_frame, text="Enter search term:").grid(row=0, column=2, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.control_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=3, padx=5, pady=5)
        
        # Buttons frame
        self.button_frame = ttk.Frame(self.control_frame)
        self.button_frame.grid(row=0, column=4, padx=5, pady=5)
        
        # Add New Product button
        ttk.Button(self.button_frame, text="Add New Product", command=self.open_add_form).pack(side="left", padx=5)
        
        # Add New Provider button
        ttk.Button(self.button_frame, text="Add New Provider", command=self.open_add_provider_form).pack(side="left", padx=5)
        
        # Clear Filter button
        ttk.Button(self.button_frame, text="Clear Provider Filter", command=self.clear_provider_filter).pack(side="left", padx=5)
        
        # Provider filter list
        tk.Label(self.control_frame, text="Filter by Provider:").grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        self.provider_tree = ttk.Treeview(self.control_frame, columns=['provider'], show="headings", height=5)
        self.provider_tree.heading('provider', text='Provider')
        self.provider_tree.column('provider', width=200, anchor="w")
        self.provider_tree.grid(row=1, column=2, columnspan=2, padx=5, pady=5)
        
        # Add scrollbar for provider list
        provider_vsb = ttk.Scrollbar(self.control_frame, orient="vertical", command=self.provider_tree.yview)
        self.provider_tree.configure(yscroll=provider_vsb.set)
        provider_vsb.grid(row=1, column=4, sticky="ns")
        
        # Populate provider list
        for provider in self.provider_info.keys():
            self.provider_tree.insert("", "end", values=[provider])
        
        # Bind selection event
        self.provider_tree.bind('<<TreeviewSelect>>', self.on_provider_select)
        
        # Results table
        self.tree_frame = ttk.Frame(self.root)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(self.tree_frame, columns=list(self.df.columns), show="headings")
        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")
        
        # Add scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind real-time updates
        self.search_var.trace("w", self.update_results)
        self.criteria_var.trace("w", self.update_results)
        
        # Auto-adjust columns initially
        self.adjust_column_widths()

    def adjust_column_widths(self):
        # Calculate maximum width needed for each column
        for col in self.df.columns:
            # Get maximum length of content in column
            max_length = max(
                [len(str(self.tree.heading(col)['text']))] + 
                [len(str(row.get(col, ''))) for _, row in self.df.iterrows()]
            )
            # Convert to pixels (approximate: multiply by font size factor)
            width = max_length * 8
            width = max(100, min(width, 300))  # Set reasonable min/max bounds
            self.tree.column(col, width=width)

    def on_provider_select(self, event):
        selection = self.provider_tree.selection()
        if selection:
            item = self.provider_tree.item(selection[0])
            self.selected_provider.set(item['values'][0])
            self.update_results()

    def clear_provider_filter(self):
        self.selected_provider.set("")
        self.provider_tree.selection_remove(self.provider_tree.selection())
        self.update_results()

    def update_results(self, *args):
        # Clear current results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get search parameters
        query = self.search_var.get().strip().lower()
        criteria = self.criteria_var.get()
        
        filtered_df = self.df
        
        # Apply provider filter
        provider_filter = self.selected_provider.get()
        if provider_filter:
            filtered_df = filtered_df[filtered_df['provider'] == provider_filter]
        
        # Apply search
        if criteria and query:
            column = self.search_fields[criteria]
            filtered_df = filtered_df[filtered_df[column].str.lower().str.contains(query, na=False)]
        
        # Populate treeview
        for _, row in filtered_df.iterrows():
            self.tree.insert("", "end", values=row.tolist())
        
        # Adjust column widths
        self.adjust_column_widths()

    def open_add_provider_form(self):
        self.provider_window = tk.Toplevel(self.root)
        self.provider_window.title("Add New Provider")
        
        form_frame = ttk.Frame(self.provider_window)
        form_frame.pack(padx=10, pady=10)
        
        provider_fields = ['provider', 'vendedor', 'direccion_proveedor', 'ubicacion_proveedor', 
                          'contacto_proveedor', 'correo_proveedor']
        self.provider_entries = {}
        
        for i, field in enumerate(provider_fields):
            ttk.Label(form_frame, text=field).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            entry = ttk.Entry(form_frame)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            self.provider_entries[field] = entry
        
        ttk.Button(form_frame, text="Submit", command=self.add_new_provider).grid(row=len(provider_fields), column=0, columnspan=2, pady=10)
    
    def add_new_provider(self):
        provider_name = self.provider_entries['provider'].get().strip()
        
        # Validate provider
        if not provider_name:
            messagebox.showerror("Error", "Provider name is required.")
            return
        if provider_name in self.provider_info:
            messagebox.showerror("Error", "Provider already exists.")
            return
        
        # Collect provider details
        new_provider = {field: self.provider_entries[field].get().strip() for field in self.provider_entries}
        
        # Update in-memory provider info
        self.provider_info[provider_name] = new_provider
        
        # Append to providers CSV
        new_provider_df = pd.DataFrame([new_provider])
        try:
            new_provider_df.to_csv("providers.csv", mode='a', header=not os.path.exists("providers.csv"), index=False)
            self.providers_df = pd.concat([self.providers_df, new_provider_df], ignore_index=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save provider to CSV: {str(e)}")
            return
        
        # Update provider tree
        self.provider_tree.insert("", "end", values=[provider_name])
        
        # Show success message
        messagebox.showinfo("Success", "New provider added successfully.")
        
        # Close the provider window
        self.provider_window.destroy()
        
        # Update provider dropdown in add product form if open
        if hasattr(self, 'provider_dropdown'):
            self.provider_dropdown['values'] = list(self.provider_info.keys())
    
    def open_add_form(self):
        self.add_window = tk.Toplevel(self.root)
        self.add_window.title("Add New Product")
        
        form_frame = ttk.Frame(self.add_window)
        form_frame.pack(padx=10, pady=10)
        
        columns = [col for col in self.df.columns if col != 'index']
        self.entries = {}
        
        current_date = datetime.now().strftime("%d-%m-%Y")
        defaults = {
            'nro_oc': "-1",
            'date_of_quotation': current_date,
            'fecha_oc': current_date,
            'quantity': "1",
            'unit_price': "$0",
            'forma_pago': "cheque 30 días",
            'unidad': "UN",
            'quotation_number': "Unknown",
            'addressee': "CONSTRUCTORA MAHUIDA",
            'code': "",
            'description': ""
        }
        
        # Create provider dropdown
        provider_label = ttk.Label(form_frame, text="provider")
        provider_label.grid(row=0, column=0, sticky="e", padx=5, pady=2)
        self.provider_var = tk.StringVar()
        self.provider_dropdown = ttk.Combobox(form_frame, textvariable=self.provider_var, 
                                            values=list(self.provider_info.keys()), state="readonly")
        self.provider_dropdown.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        self.provider_dropdown.bind("<<ComboboxSelected>>", self.update_provider_fields)
        
        # Create entry fields for other columns
        row_index = 1
        for col in columns:
            if col == 'provider':
                continue  # Skip provider as it's handled by dropdown
            ttk.Label(form_frame, text=col).grid(row=row_index, column=0, sticky="e", padx=5, pady=2)
            entry = ttk.Entry(form_frame)
            entry.grid(row=row_index, column=1, sticky="w", padx=5, pady=2)
            if col in defaults:
                entry.insert(0, defaults[col])
            self.entries[col] = entry
            row_index += 1
        
        ttk.Button(form_frame, text="Submit", command=self.add_new_product).grid(row=row_index, column=0, columnspan=2, pady=10)
    
    def update_provider_fields(self, event=None):
        provider = self.provider_var.get()
        if provider in self.provider_info:
            info = self.provider_info[provider]
            for field in ['vendedor', 'direccion_proveedor', 'ubicacion_proveedor', 
                         'contacto_proveedor', 'correo_proveedor']:
                if field in self.entries:
                    self.entries[field].delete(0, tk.END)
                    self.entries[field].insert(0, info[field] or "")
    
    def add_new_product(self):
        # Check if provider is selected
        if not self.provider_var.get():
            messagebox.showerror("Error", "Please select a provider.")
            return
        
        # Validate unit_price
        unit_price = self.entries['unit_price'].get().strip()
        if not unit_price.startswith('$'):
            messagebox.showerror("Error", "Unit price must start with a '$' symbol.")
            return
        
        new_row = {}
        for col, entry in self.entries.items():
            new_row[col] = entry.get()
        
        # Add provider from dropdown
        new_row['provider'] = self.provider_var.get()
        
        # Calculate new index
        try:
            max_index = self.df['index'].apply(lambda x: int(x) if x.isdigit() else 0).max()
        except ValueError:
            max_index = 0
        new_index = str(max_index + 1)
        new_row['index'] = new_index
        
        # Create new DataFrame row
        new_df_row = pd.DataFrame([new_row])
        
        # Append to main DataFrame
        self.df = pd.concat([self.df, new_df_row], ignore_index=True)
        
        # Update provider info if new provider was added
        if new_row['provider'] not in self.provider_info:
            provider_cols = {col: new_row.get(col, '') for col in 
                           ['vendedor', 'direccion_proveedor', 'ubicacion_proveedor', 
                            'contacto_proveedor', 'correo_proveedor']}
            self.provider_info[new_row['provider']] = provider_cols
            new_provider_df = pd.DataFrame([provider_cols])
            try:
                new_provider_df.to_csv("providers.csv", mode='a', header=not os.path.exists("providers.csv"), index=False)
                self.providers_df = pd.concat([self.providers_df, new_provider_df], ignore_index=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save provider to CSV: {str(e)}")
                return
        
        # Save to registry CSV
        try:
            self.df.to_csv("registry.csv", index=False)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to registry CSV: {str(e)}")
            return
        
        # Show success message
        messagebox.showinfo("Success", "New product added successfully.")
        
        # Close the add window
        self.add_window.destroy()
        
        # Update results
        self.update_results()

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVSearchApp(root)
    root.mainloop()
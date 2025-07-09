import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime

# Function to load CSV with error handling
def load_csv():
    try:
        return pd.read_csv("registry.csv", dtype=str)
    except FileNotFoundError:
        messagebox.showerror("Error", "Could not find 'registry.csv'. Please ensure it’s in the same directory.")
        return None
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load CSV: {str(e)}")
        return None

# Main application class
class CSVSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Search Application")
        
        # Load CSV data
        self.df = load_csv()
        if self.df is None:
            self.root.destroy()
            return
        
        # Define search fields mapping
        self.search_fields = {
            "Product Code": "code",
            "Order Number": "nro_oc",
            "Description": "description"
        }
        
        # GUI setup
        self.setup_gui()
        
        # Initialize with all data displayed
        self.update_results()

    def setup_gui(self):
        # Search criteria dropdown
        tk.Label(self.root, text="Search by:").pack(pady=5)
        self.criteria_var = tk.StringVar()
        self.criteria_dropdown = ttk.Combobox(self.root, 
                                            textvariable=self.criteria_var,
                                            values=list(self.search_fields.keys()),
                                            state="readonly")
        self.criteria_dropdown.pack(pady=5)
        self.criteria_dropdown.set("Description")  # Default selection
        
        # Search entry field
        tk.Label(self.root, text="Enter search term:").pack(pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.root, textvariable=self.search_var)
        self.search_entry.pack(pady=5)
        
        # Add New Product button
        ttk.Button(self.root, text="Add New Product", command=self.open_add_form).pack(pady=5)
        
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
    
    def update_results(self, *args):
        # Clear current results
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get search parameters
        query = self.search_var.get().strip().lower()
        criteria = self.criteria_var.get()
        
        if not criteria:
            return
        column = self.search_fields[criteria]
        
        # Filter data
        if query:
            filtered_df = self.df[self.df[column].str.lower().str.contains(query, na=False)]
        else:
            filtered_df = self.df  # Show all if query is empty
        
        # Populate treeview
        for _, row in filtered_df.iterrows():
            self.tree.insert("", "end", values=row.tolist())
    
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
            'unit_price': "0",
            'forma_pago': "cheque 30 días",
            'unidad': "UN",
        }
        
        for i, col in enumerate(columns):
            ttk.Label(form_frame, text=col).grid(row=i, column=0, sticky="e", padx=5, pady=2)
            entry = ttk.Entry(form_frame)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=2)
            if col in defaults:
                entry.insert(0, defaults[col])
            self.entries[col] = entry
        
        ttk.Button(form_frame, text="Submit", command=self.add_new_product).grid(row=len(columns), column=0, columnspan=2, pady=10)
    
    def add_new_product(self):
        new_row = {}
        for col, entry in self.entries.items():
            new_row[col] = entry.get()
        
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
        
        # Save to CSV
        self.df.to_csv("registry.csv", index=False)
        
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
import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

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
            return  # No criteria selected yet
        
        column = self.search_fields[criteria]
        
        # Filter data
        if query:
            filtered_df = self.df[self.df[column].str.lower().str.contains(query, na=False)]
        else:
            filtered_df = self.df  # Show all if query is empty
        
        # Populate treeview
        for _, row in filtered_df.iterrows():
            self.tree.insert("", "end", values=row.tolist())

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVSearchApp(root)
    root.mainloop()
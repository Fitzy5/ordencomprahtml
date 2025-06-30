import pandas as pd
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

# Load the CSV file
try:
    df = pd.read_csv(r'C:\Users\Jeyson\proyectos\Proyectos\ordencomprahtml\registry.csv', dtype=str)
except FileNotFoundError:
    messagebox.showerror("Error", "CSV file 'registry.csv' not found.")
    exit()
except pd.errors.ParserError:
    messagebox.showerror("Error", "Error parsing CSV file.")
    exit()

# Set up the GUI
root = tk.Tk()
root.title("CSV Search App")

# Add instructions
tk.Label(root, text="Select search criteria and enter query:").pack()

# Search criteria selection
criteria_var = tk.StringVar()
criteria_dropdown = ttk.Combobox(root, textvariable=criteria_var, values=['Product Code', 'Order Number', 'Description'])
criteria_dropdown.pack()

# Search entry field
search_var = tk.StringVar()
search_entry = ttk.Entry(root, textvariable=search_var)
search_entry.pack()

# Results display with scrollbars
frame = ttk.Frame(root)
frame.pack(fill='both', expand=True)

tree = ttk.Treeview(frame, columns=list(df.columns), show='headings')
for col in df.columns:
    tree.heading(col, text=col)
    tree.column(col, width=100)  # Default column width

vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

tree.grid(row=0, column=0, sticky='nsew')
vsb.grid(row=0, column=1, sticky='ns')
hsb.grid(row=1, column=0, sticky='ew')

frame.grid_rowconfigure(0, weight=1)
frame.grid_columnconfigure(0, weight=1)

# Function to update search results
def update_results(*args):
    query = search_var.get().lower()
    criteria = criteria_var.get()
    
    # Define the search filter based on criteria
    if criteria == 'Product Code':
        mask = df['code'].str.lower().str.contains(query, regex=False, na=False)
    elif criteria == 'Order Number':
        mask = df['nro_oc'].str.lower().str.contains(query, regex=False, na=False)
    elif criteria == 'Description':
        mask = df['description'].str.lower().str.contains(query, regex=False, na=False)
    else:
        mask = pd.Series([True] * len(df))
    
    results = df[mask]
    
    # Clear previous results
    for i in tree.get_children():
        tree.delete(i)
    
    # Insert new results
    for index, row in results.iterrows():
        tree.insert('', 'end', values=list(row))

# Bind events for real-time updates
search_var.trace('w', update_results)
criteria_var.trace('w', update_results)

# Perform initial update
update_results()

# Start the GUI event loop
root.mainloop()
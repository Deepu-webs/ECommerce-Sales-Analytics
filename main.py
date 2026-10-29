import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

FILE_NAME = "sales_data.csv"
REQUIRED_COLUMNS = ["Product", "Category", "Quantity", "Price", "Date"]


def empty_data():
    return pd.DataFrame(columns=REQUIRED_COLUMNS + ["Revenue"])


def load_data(show_errors=True):
    if not os.path.exists(FILE_NAME):
        return empty_data()
    try:
        df = pd.read_csv(FILE_NAME)
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            if show_errors:
                messagebox.showerror("Data Error", "Missing columns: " + ", ".join(missing))
            return None
        if df.empty:
            df["Revenue"] = pd.Series(dtype="float64")
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            return df
        df["Date"] = pd.to_datetime(df["Date"], errors="raise")
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="raise")
        df["Price"] = pd.to_numeric(df["Price"], errors="raise")
        if df[REQUIRED_COLUMNS].isna().any().any():
            raise ValueError("Some sales fields are empty.")
        if (df["Quantity"] <= 0).any() or (df["Price"] < 0).any():
            raise ValueError("Quantity must be positive and Price cannot be negative.")
        df["Revenue"] = df["Quantity"] * df["Price"]
        return df
    except Exception as e:
        if show_errors:
            messagebox.showerror("Data Error", str(e))
        return None


def save_data(df):
    try:
        output = df[REQUIRED_COLUMNS].copy()
        output["Revenue"] = output["Quantity"] * output["Price"]
        output.to_csv(FILE_NAME, index=False)
        return True
    except Exception as e:
        messagebox.showerror("Save Error", str(e))
        return False


def get_filtered_data(show_errors=True, search_text=None):
    df = load_data(show_errors=show_errors)
    if df is None:
        return None
    from_text = from_date_entry.get().strip()
    to_text = to_date_entry.get().strip()
    try:
        if from_text:
            start_date = pd.to_datetime(from_text, format="%Y-%m-%d")
            df = df[df["Date"] >= start_date]
        if to_text:
            end_date = pd.to_datetime(to_text, format="%Y-%m-%d")
            df = df[df["Date"] <= end_date]
        if from_text and to_text and start_date > end_date:
            raise ValueError("From Date cannot be later than To Date.")
    except ValueError:
        if show_errors:
            messagebox.showerror("Date Filter Error", "Use YYYY-MM-DD and make sure From Date is not after To Date.")
        return None
    if search_text:
        df = df[df["Product"].astype(str).str.lower().str.contains(search_text.lower(), na=False, regex=False)]
    return df


def clear_form():
    for entry in (product_entry, category_entry, quantity_entry, price_entry, sale_date_entry):
        entry.delete(0, tk.END)


def update_kpi_cards(df):
    if df is None or df.empty:
        total_revenue = 0
        total_orders = 0
        units_sold = 0
        best_product = "N/A"
    else:
        total_revenue = df["Revenue"].sum()
        total_orders = len(df)
        units_sold = df["Quantity"].sum()
        product_units = df.groupby("Product")["Quantity"].sum()
        best_product = product_units.idxmax() if not product_units.empty else "N/A"
    revenue_card_value.config(text=f"Rs. {total_revenue:,.2f}")
    orders_card_value.config(text=str(total_orders))
    units_card_value.config(text=f"{units_sold:,.0f}")
    best_card_value.config(text=best_product)


def refresh_dashboard():
    df = get_filtered_data()
    if df is None:
        return
    update_kpi_cards(df)
    for item in table.get_children():
        table.delete(item)
    for idx, row in df.iterrows():
        table.insert("", "end", iid=str(idx), values=(
            row["Product"], row["Category"], int(row["Quantity"]),
            f'{row["Price"]:,.2f}', f'{row["Revenue"]:,.2f}',
            row["Date"].strftime("%Y-%m-%d")
        ))
    show_all_charts(df)


def add_sale():
    product = product_entry.get().strip()
    category = category_entry.get().strip()
    try:
        quantity = int(quantity_entry.get().strip())
        price = float(price_entry.get().strip())
        date = pd.to_datetime(sale_date_entry.get().strip(), format="%Y-%m-%d")
        if not product or not category or quantity <= 0 or price < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Input Error", "Fill all fields correctly. Quantity must be positive, Price non-negative, Date format YYYY-MM-DD.")
        return
    df = load_data()
    if df is None:
        return
    new_row = pd.DataFrame([{
        "Product": product, "Category": category, "Quantity": quantity,
        "Price": price, "Date": date, "Revenue": quantity * price
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    if save_data(df):
        clear_form()
        refresh_dashboard()
        messagebox.showinfo("Success", "Sale added successfully!")


def on_row_select(event=None):
    selected = table.selection()
    if not selected:
        return
    values = table.item(selected[0], "values")
    if not values:
        return
    clear_form()
    product_entry.insert(0, values[0])
    category_entry.insert(0, values[1])
    quantity_entry.insert(0, values[2])
    price_entry.insert(0, str(values[3]).replace(",", ""))
    sale_date_entry.insert(0, values[5])


def update_sale():
    selected = table.selection()
    if not selected:
        messagebox.showwarning("Select Sale", "Select a row in the table first.")
        return
    try:
        row_index = int(selected[0])
        product = product_entry.get().strip()
        category = category_entry.get().strip()
        quantity = int(quantity_entry.get().strip())
        price = float(price_entry.get().strip())
        date = pd.to_datetime(sale_date_entry.get().strip(), format="%Y-%m-%d")
        if not product or not category or quantity <= 0 or price < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Input Error", "Enter valid product, category, quantity, price and date (YYYY-MM-DD).")
        return
    df = load_data()
    if df is None or row_index not in df.index:
        messagebox.showerror("Update Error", "Record not found. Clear date filters and refresh, then select the row again.")
        return
    df.loc[row_index, ["Product", "Category", "Quantity", "Price", "Date"]] = [product, category, quantity, price, date]
    if save_data(df):
        clear_form()
        refresh_dashboard()
        messagebox.showinfo("Success", "Sale updated successfully!")


def delete_sale():
    selected = table.selection()
    if not selected:
        messagebox.showwarning("Select Sale", "Select a row in the table first.")
        return
    if not messagebox.askyesno("Confirm Delete", "Delete the selected sale?"):
        return
    try:
        row_index = int(selected[0])
    except ValueError:
        messagebox.showerror("Delete Error", "Refresh the table and select the row again.")
        return
    df = load_data()
    if df is None or row_index not in df.index:
        messagebox.showerror("Delete Error", "Record not found. Refresh and try again.")
        return
    df = df.drop(index=row_index).reset_index(drop=True)
    if save_data(df):
        clear_form()
        refresh_dashboard()
        messagebox.showinfo("Success", "Sale deleted successfully!")


def search_sale():
    search_text = search_entry.get().strip()
    df = get_filtered_data(search_text=search_text)
    if df is None:
        return
    update_kpi_cards(df)
    for item in table.get_children():
        table.delete(item)
    for idx, row in df.iterrows():
        table.insert("", "end", iid=str(idx), values=(
            row["Product"], row["Category"], int(row["Quantity"]),
            f'{row["Price"]:,.2f}', f'{row["Revenue"]:,.2f}', row["Date"].strftime("%Y-%m-%d")
        ))
    show_all_charts(df)
    if df.empty:
        messagebox.showinfo("Search", "No matching sales found.")


def export_csv():
    df = get_filtered_data()
    if df is None:
        return
    if df.empty:
        messagebox.showwarning("Export", "There is no data to export.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile="sales_report.csv")
    if not path:
        return
    try:
        df.to_csv(path, index=False)
        messagebox.showinfo("Export Complete", f"CSV report saved to:\n{path}")
    except Exception as e:
        messagebox.showerror("Export Error", str(e))


def export_excel():
    df = get_filtered_data()
    if df is None:
        return
    if df.empty:
        messagebox.showwarning("Export", "There is no data to export.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")], initialfile="sales_report.xlsx")
    if not path:
        return
    try:
        df.to_excel(path, index=False, engine="openpyxl")
        messagebox.showinfo("Export Complete", f"Excel report saved to:\n{path}")
    except ImportError:
        messagebox.showerror("Missing Library", "Install Excel support with: pip install openpyxl")
    except Exception as e:
        messagebox.showerror("Export Error", str(e))


def show_all_charts(df=None):
    if df is None:
        df = get_filtered_data(show_errors=False)
    for widget in chart_frame.winfo_children():
        widget.destroy()
    if df is None or df.empty:
        tk.Label(chart_frame, text="Add sales or change date filters to display charts.", bg="white").pack(pady=10)
        return
    fig = Figure(figsize=(12, 2.5), dpi=85)
    ax1 = fig.add_subplot(131)
    ax2 = fig.add_subplot(132)
    ax3 = fig.add_subplot(133)
    df.groupby("Product")["Revenue"].sum().sort_values().plot(kind="bar", ax=ax1, title="Revenue by Product")
    ax1.set_xlabel("Product")
    ax1.set_ylabel("Revenue (Rs.)")
    ax1.tick_params(axis="x", labelrotation=35, labelsize=7)
    ax1.tick_params(axis="y", labelsize=7)
    category_sales = df.groupby("Category")["Revenue"].sum()
    if category_sales.sum() > 0:
        category_sales.plot(kind="pie", autopct="%1.1f%%", startangle=90, ax=ax2, textprops={"fontsize": 7})
        ax2.set_title("Revenue by Category")
        ax2.set_ylabel("")
    else:
        ax2.set_title("Revenue by Category")
        ax2.text(0.5, 0.5, "No revenue", ha="center", va="center")
    monthly = df.assign(Month=df["Date"].dt.to_period("M").astype(str)).groupby("Month")["Revenue"].sum()
    monthly.plot(kind="line", marker="o", ax=ax3, title="Monthly Revenue")
    ax3.set_xlabel("Month")
    ax3.set_ylabel("Revenue (Rs.)")
    ax3.tick_params(axis="x", labelrotation=35, labelsize=7)
    ax3.tick_params(axis="y", labelsize=7)
    ax3.grid(True, alpha=0.3)
    fig.tight_layout(pad=1.2)
    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


def clear_date_filters():
    from_date_entry.delete(0, tk.END)
    to_date_entry.delete(0, tk.END)
    search_entry.delete(0, tk.END)
    refresh_dashboard()


# ---------------- MAIN WINDOW ----------------
root = tk.Tk()
root.title("E-Commerce Sales Analytics - Improved Dashboard")
root.geometry("1250x900")
root.minsize(1050, 760)
root.configure(bg="#eef2f7")

header = tk.Label(root, text="E-Commerce Sales Analytics", font=("Arial", 21, "bold"), bg="#eef2f7", fg="#243447")
header.pack(pady=(8, 2))
subtitle = tk.Label(root, text="Sales overview, product performance and reports", font=("Arial", 10), bg="#eef2f7", fg="#536273")
subtitle.pack(pady=(0, 5))

# KPI cards
cards_frame = tk.Frame(root, bg="#eef2f7")
cards_frame.pack(fill="x", padx=12, pady=4)
card_specs = [
    ("TOTAL REVENUE", "revenue_card_value"),
    ("TOTAL SALES", "orders_card_value"),
    ("UNITS SOLD", "units_card_value"),
    ("BEST-SELLING PRODUCT", "best_card_value")
]
card_values = {}
for title_text, key in card_specs:
    card = tk.Frame(cards_frame, bg="white", bd=1, relief="solid", padx=10, pady=6)
    card.pack(side="left", fill="both", expand=True, padx=4)
    tk.Label(card, text=title_text, font=("Arial", 9, "bold"), bg="white", fg="#526173").pack()
    value_label = tk.Label(card, text="0", font=("Arial", 14, "bold"), bg="white", fg="#176b45", wraplength=220)
    value_label.pack(pady=(4, 0))
    card_values[key] = value_label
revenue_card_value = card_values["revenue_card_value"]
orders_card_value = card_values["orders_card_value"]
units_card_value = card_values["units_card_value"]
best_card_value = card_values["best_card_value"]

# Sale entry form
form_frame = tk.LabelFrame(root, text="Add / Edit Sale", font=("Arial", 10, "bold"), bg="#eef2f7", padx=7, pady=5)
form_frame.pack(fill="x", padx=12, pady=4)
form_labels = ["Product", "Category", "Quantity", "Price", "Date (YYYY-MM-DD)"]
entries = []
for i, label_text in enumerate(form_labels):
    tk.Label(form_frame, text=label_text, bg="#eef2f7").grid(row=0, column=i, padx=4, pady=2)
    entry = tk.Entry(form_frame, width=15)
    entry.grid(row=1, column=i, padx=4, pady=3)
    entries.append(entry)
product_entry, category_entry, quantity_entry, price_entry, sale_date_entry = entries
button_frame = tk.Frame(form_frame, bg="#eef2f7")
button_frame.grid(row=1, column=5, padx=5)
tk.Button(button_frame, text="Add Sale", width=11, command=add_sale).pack(pady=1)
tk.Button(button_frame, text="Update Sale", width=11, command=update_sale).pack(pady=1)
tk.Button(button_frame, text="Delete Sale", width=11, command=delete_sale).pack(pady=1)

# Filters and exports
controls = tk.LabelFrame(root, text="Search, Date Filter and Export", font=("Arial", 10, "bold"), bg="#eef2f7", padx=6, pady=5)
controls.pack(fill="x", padx=12, pady=3)
tk.Label(controls, text="Product:", bg="#eef2f7").grid(row=0, column=0, padx=3, pady=3)
search_entry = tk.Entry(controls, width=16)
search_entry.grid(row=0, column=1, padx=3, pady=3)
tk.Label(controls, text="From Date:", bg="#eef2f7").grid(row=0, column=2, padx=3, pady=3)
from_date_entry = tk.Entry(controls, width=13)
from_date_entry.grid(row=0, column=3, padx=3, pady=3)
tk.Label(controls, text="To Date:", bg="#eef2f7").grid(row=0, column=4, padx=3, pady=3)
to_date_entry = tk.Entry(controls, width=13)
to_date_entry.grid(row=0, column=5, padx=3, pady=3)
tk.Button(controls, text="Apply Filter / Search", command=search_sale).grid(row=0, column=6, padx=4, pady=3)
tk.Button(controls, text="Clear Filters", command=clear_date_filters).grid(row=0, column=7, padx=4, pady=3)
tk.Button(controls, text="Export CSV", command=export_csv).grid(row=0, column=8, padx=4, pady=3)
tk.Button(controls, text="Export Excel", command=export_excel).grid(row=0, column=9, padx=4, pady=3)

# Charts
chart_frame = tk.LabelFrame(root, text="Sales Analytics Charts", font=("Arial", 10, "bold"), bg="white", padx=3, pady=3)
chart_frame.pack(fill="x", padx=12, pady=4)

# Table
table_frame = tk.LabelFrame(root, text="Sales Records (select a row to edit or delete)", font=("Arial", 10, "bold"), bg="#eef2f7", padx=5, pady=3)
table_frame.pack(fill="both", expand=True, padx=12, pady=(3, 8))
columns = ("Product", "Category", "Quantity", "Price", "Revenue", "Date")
table = ttk.Treeview(table_frame, columns=columns, show="headings", height=6, selectmode="browse")
for col in columns:
    table.heading(col, text=col)
    table.column(col, width=145, anchor="center")
scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
table.configure(yscrollcommand=scrollbar.set)
table.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
table.bind("<<TreeviewSelect>>", on_row_select)

refresh_dashboard()
root.mainloop()

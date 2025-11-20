# Instructions:
#
# This program allows you to search for stock news data from the ShareData website by entering a stock symbol.
# It fetches the news for the stock symbol, displays the results in a Tkinter GUI, and allows exporting to PDF.
# To use this program, make sure you have the following libraries installed:
#
# Installation Commands for Terminal (Linux/macOS/Windows):
# 1. Install Playwright and download the browsers:
#    pip install playwright
#    playwright install
#
# 2. Install tkinter (if not already installed with Python):
#    pip install tk
#
# 3. Install ReportLab for PDF export:
#    pip install reportlab
#
# 4. Install Requests:
#    pip install requests
#
# Once the libraries are installed, you can run the program, and it will allow you to interact with the interface and fetch stock data.
#
# All ideas and concepts for this program were created by Gawie Thirion.
# Code written by ChatGPT and modified by Gawie Thirion where needed.
#
#
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from playwright.sync_api import sync_playwright
import re
from datetime import datetime
import requests


def is_valid_stock_symbol_with_playwright(stock_symbol):
    """Use Playwright to validate the stock symbol by ensuring the page loads correctly."""
    url = f"https://www.sharedata.co.za/v2/Scripts/News.aspx?c={stock_symbol}&group=SENS"
    try:
        # Using Playwright to load the page and ensure the table appears
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            # Wait for the NewsListTable to load or timeout
            page.wait_for_selector("#NewsListTable tbody tr", timeout=5000)  # 5-second timeout
            rows = page.locator("#NewsListTable tbody tr")
            row_count = rows.count()
            browser.close()
            if row_count > 0:
                return True
            else:
                print(f"Error: No rows found for stock symbol '{stock_symbol}'")
                return False
    except Exception as e:
        print(f"Error loading URL for stock symbol '{stock_symbol}': {str(e)}")
        return False


def get_sens_titles_with_playwright(stock_symbol, update_loading_status):
    results = []
    print("Starting Playwright...")
    with sync_playwright() as p:
        print("Playwright initialized.")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        url = f"https://www.sharedata.co.za/v2/Scripts/News.aspx?c={stock_symbol}&group=SENS"
        print(f"Navigating to URL: {url}")
        page.goto(url)

        # Wait for the table to load or timeout if it doesn't appear
        try:
            page.wait_for_selector("#NewsListTable tbody tr", timeout=5000)  # 5-second timeout
        except Exception as e:
            browser.close()
            messagebox.showerror("Error", f"Error loading stock symbol '{stock_symbol}'\n{str(e)}")
            return []

        # Extract all rows from the table
        rows = page.locator("#NewsListTable tbody tr")
        row_count = rows.count()

        if row_count == 0:
            browser.close()
            messagebox.showerror("No Data", f"No news found for stock symbol '{stock_symbol}'.")
            return []

        # Get the current year
        current_year = datetime.now().year
        # Set the range for the last 5 years
        start_year = current_year - 5

        if row_count > 0:
            print(f"\nResults for stock symbol: {stock_symbol}")
            all_data = []

            # Loop through all rows and extract the date and title
            for i in range(1, row_count, 2):  # Start at 1 to get the title of each pair of rows
                # Update the loading status with moving dots
                update_loading_status(i, row_count)

                # Get the title from the previous row (i-1)
                title_row = rows.nth(i - 1)
                title_text = title_row.text_content().strip()

                # Skip if the title is too short
                if len(title_text) < 10:
                    continue

                # Get the date from the current row (i)
                date_row = rows.nth(i)
                date_content = date_row.text_content().strip()

                # Regular expression to match the date and time pattern (e.g., "Wed 22 Nov 2023 16:45")
                date_match = re.search(r"(\w{3} \d{1,2} \w{3} \d{4} \d{2}:\d{2})", date_content)
                if date_match:
                    # Extract the date and format it to "DAY-MON-YEAR @TIME"
                    date_text = date_match.group(1)
                    date_parts = date_text.split()
                    day_of_week = date_parts[0]
                    day_of_month = date_parts[1]
                    month_name = date_parts[2]
                    year = date_parts[3]
                    time = date_parts[4]

                    # Ensure we correctly map month names to numeric months
                    month_mapping = {
                        'Jan': 'Jan', 'Feb': 'Feb', 'Mar': 'Mar', 'Apr': 'Apr', 'May': 'May',
                        'Jun': 'Jun', 'Jul': 'Jul', 'Aug': 'Aug', 'Sep': 'Sep', 'Oct': 'Oct',
                        'Nov': 'Nov', 'Dec': 'Dec'
                    }

                    # If the month is not valid, skip the entry
                    if month_name not in month_mapping:
                        continue

                    # Skip if the year is outside the last 5 years
                    year = int(year)
                    if year < start_year or year > current_year:
                        continue

                    # Ensure the formatted date has the year included
                    formatted_date = f"{day_of_week}-{day_of_month}-{month_name}-{year} @{time}"

                    # Include the title and formatted date in the output
                    all_data.append(f"{formatted_date}: {title_text}")

            if all_data:
                results = all_data
            else:
                results.append(f"No valid events found for stock symbol: {stock_symbol}")

        browser.close()
        print("Browser closed.")
    return results


class PDFExporter:
    @staticmethod
    def export_to_pdf(results, filename, text_widget):
        # Get the content of the editable text box
        results = text_widget.get(1.0, tk.END).strip()  # Get the entire text content from the widget

        if not results:
            messagebox.showerror("Error", "There is no content to export.")
            return

        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        c.setFont("Helvetica", 10)
        y_position = height - 40  # Starting y position

        for line in results.splitlines():
            if y_position < 40:  # Check if we are near the bottom of the page
                c.showPage()
                c.setFont("Helvetica", 10)
                y_position = height - 40  # Reset y position for the new page
            c.drawString(30, y_position, line)
            y_position -= 14  # Move down for the next line

        c.save()



class StockGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("SENS Results Viewer")
        self.master.geometry("600x400")
        self.master.minsize(720, 720)  # Set minimum window size

        # Create a label for helpful text above the results box
        self.help_label = tk.Label(master, text="Don't panic if it looks stuck, it's just loading data.", font=("Helvetica", 10))
        self.help_label.pack(pady=5)

        # Text box with a scrollbar
        self.results_frame = tk.Frame(master)
        self.results_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.results_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_text = tk.Text(self.results_frame, wrap=tk.WORD, height=15, width=70, yscrollcommand=self.scrollbar.set)
        self.results_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.results_text.yview)

        self.add_stock_button = tk.Button(master, text="Add Stock Symbol", command=self.add_stock)
        self.add_stock_button.pack(pady=5)

        self.clear_button = tk.Button(master, text="Clear", command=self.clear_results)
        self.clear_button.pack(pady=5)

        self.export_button = tk.Button(master, text="Export to PDF", command=self.export_to_pdf)
        self.export_button.pack(pady=5)

        self.loading_label = tk.Label(master, text="Loading...", font=("Helvetica", 10))
        self.loading_label.pack(pady=5)
        self.loading_label.pack_forget()  # Initially hide the loading label

        self.stock_symbols = []
        self.results = []

    def add_stock(self):
        stock_symbol = simpledialog.askstring("Stock Symbol", "Enter stock symbol:")
        if stock_symbol:
            stock_symbol = stock_symbol.upper()

            # Reject stock symbols with spaces or invalid characters
            if " " in stock_symbol or not stock_symbol.isalnum():
                messagebox.showerror("Invalid Stock Symbol", "Stock symbol cannot contain spaces or non-alphanumeric characters.")
                return

            # Validate the stock symbol
            if not is_valid_stock_symbol_with_playwright(stock_symbol):
                messagebox.showerror("Error", f"Error loading stock symbol '{stock_symbol}'")
                return

            self.stock_symbols.append(stock_symbol)
            self.loading_label.pack()  # Show loading label while fetching results

            # Function to update loading status with moving dots
            def update_loading_status(i, row_count):
                dots = '.' * ((i // 10) % 4)  # Create moving dots
                self.loading_label.config(text=f"Loading{dots}")
                self.master.update()  # Update the UI

            stock_results = get_sens_titles_with_playwright(stock_symbol, update_loading_status)
            print(stock_results)  # Debugging output to verify the fetched results
            if stock_results:
                # Ensure the stock symbol is displayed correctly in the results
                self.results.append(f"Results for: {stock_symbol}")
                self.results_text.insert(tk.END, f"{stock_symbol}\n")  # Stock symbol in editable text box
                self.results.extend(stock_results)
                self.results.append("-" * 50)  # Separator line
                self.update_results_display()

            self.loading_label.pack_forget()  # Hide the loading label after results are fetched

    def update_results_display(self):
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, "\n\n".join(self.results))

    def export_to_pdf(self):
        if self.results_text.get(1.0, tk.END).strip():  # Ensure there's content in the text box
            filename = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
            if filename:
                PDFExporter.export_to_pdf(self.results, filename, self.results_text)
                messagebox.showinfo("Success", f"Results saved to {filename}")
        else:
            messagebox.showerror("Error", "No results to export!")


    def clear_results(self):
        """Clear all stock symbols and results."""
        self.stock_symbols.clear()
        self.results.clear()
        self.update_results_display()
        messagebox.showinfo("Cleared", "All results have been cleared.")


def main():
    root = tk.Tk()
    gui = StockGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

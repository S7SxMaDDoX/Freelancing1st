import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
import configparser

class TableEditor:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.database_created = False
        self.table_data_inserted = False

        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(pady=20)

        self.username_label = tk.Label(self.login_frame, text="Username:")
        self.username_label.grid(row=0, column=0, padx=10, pady=5)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5)

        self.password_label = tk.Label(self.login_frame, text="Password:")
        self.password_label.grid(row=1, column=0, padx=10, pady=5)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5)

        self.login_button = tk.Button(self.login_frame, text="Login", command=self.login_button_click)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=10)

    def login_button_click(self):
        if self.username_entry.get() == self.config['Database']['username'] and \
           self.password_entry.get() == self.config['Database']['password']:
            self.show_table_editor()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def show_table_editor(self):
        self.login_frame.destroy()

        try:
            self.connection = mysql.connector.connect(
                host=self.config['Database']['host'],
                user=self.config['Database']['username'],
                password=self.config['Database']['password']
            )
            self.cursor = self.connection.cursor()

            # Create database if not exists
            if not self.database_created:
                self.create_database()

            # Connect to the database
            self.connection.database = self.config['Database']['database']

            # Create table if not exists
            self.create_table()

            # Insert data into the table (only if it hasn't been inserted before)
            if not self.table_data_inserted:
                self.insert_data()
                self.table_data_inserted = True

            # Fetch data and display in table editor
            self.cursor.execute("SELECT * FROM your_table")
            self.rows = self.cursor.fetchall()

            self.table_frame = tk.Frame(self.root)
            self.table_frame.pack(fill="both", expand=True)

            self.tree = ttk.Treeview(self.table_frame, selectmode="browse")
            self.tree["columns"] = tuple("column" + str(i) for i in range(len(self.rows[0])))
            self.tree["show"] = "headings"

            self.columns = [i[0] for i in self.cursor.description]
            for i, col in enumerate(self.columns):
                self.tree.heading("column" + str(i), text=col)
                self.tree.column("column" + str(i), width=100)  # Adjust width as needed

            for row in self.rows:
                self.tree.insert("", "end", values=row)

            self.tree.pack(fill="both", expand=True)

            # Apply black borders
            self.tree.tag_configure('oddrow', background='#FFFFFF')
            self.tree.tag_configure('evenrow', background='#F0F0F0')

            for i, row in enumerate(self.tree.get_children()):
                if i % 2 == 0:
                    self.tree.item(row, tags=('evenrow',))
                else:
                    self.tree.item(row, tags=('oddrow',))

            # Bind double click to edit
            self.tree.bind("<Double-1>", self.on_cell_edit)

        except mysql.connector.Error as error:
            messagebox.showerror("Error", "Failed to fetch data from MySQL: {}".format(error))

    def create_database(self):
        try:
            # Check if the database exists
            self.cursor.execute("SHOW DATABASES LIKE %s", (self.config['Database']['database'],))
            result = self.cursor.fetchone()

            if not result:
                # Database doesn't exist, create it
                self.cursor.execute("CREATE DATABASE {}".format(self.config['Database']['database']))
                self.database_created = True
        except mysql.connector.Error as error:
            messagebox.showerror("Error", "Failed to create database: {}".format(error))

    def create_table(self):
        try:
            # Check if the table exists
            self.cursor.execute("SHOW TABLES LIKE 'your_table'")
            result = self.cursor.fetchone()

            if not result:
                # Table doesn't exist, create it
                self.cursor.execute("""
                CREATE TABLE your_table (
                    SL_NO INT AUTO_INCREMENT PRIMARY KEY,
                    NAI_TYPE VARCHAR(255),
                    LOC VARCHAR(255),
                    OWN_SUB_BN VARCHAR(255),
                    TO_BE_TGT_BY_COS VARCHAR(255),
                    A VARCHAR(255),
                    B VARCHAR(255),
                    C VARCHAR(255)
                )
                """)
                self.connection.commit()
        except mysql.connector.Error as error:
            messagebox.showerror("Error", "Failed to create table: {}".format(error))

    def insert_data(self):
        try:
            # Check if any data exists in the table
            self.cursor.execute("SELECT COUNT(*) FROM your_table")
            count = self.cursor.fetchone()[0]

            if count == 0:
                # Sample data to be inserted
                data = [
                    ("REAR CP", "(I)KEYS , (II)T Scthan", "2IA , SATT", "EW", "", "H-120", ""),
                    ("BASE CP", "(i)TSONA , (i)RONG", "SF", "", "", "H-60", ""),
                    ("ADVANCE CP", "(I)LAMBU , (II)SERCHE, (III)KACHAN RI", "ARS", "EW,LRV,SF", "", "H-48", "COMN BLACK OUT ,COS TO CDR AT HQ"),
                    ("LSG A", "(I)LAMBU W,(II)KEYS", "", "", "", "", ""),
                    ("HELIPAD", "(I)CHUNI,(II)LAMBU,(III)NAGDALA", "", "ARITY,LRV", "", "", ""),
                    ("PLA EW", "(I)LAMBU", "", "", "", "", ""),
                    ("DEBUSTING PT", "", "", "", "", "", ""),
                    ("ATT || KEPTYS", "", "", "", "", "", ""),
                    ("OPS", "", "", "", "", "", ""),
                    ("UAV", "", "", "", "", "", ""),
                    ("EW", "", "", "", "", "", "")
                ]
                self.cursor.executemany("INSERT INTO your_table (NAI_TYPE, LOC, OWN_SUB_BN, TO_BE_TGT_BY_COS, A, B, C) VALUES (%s, %s, %s, %s, %s, %s, %s)", data)
                self.connection.commit()
                self.table_data_inserted = True
        except mysql.connector.Error as error:
            messagebox.showerror("Error", "Failed to insert data: {}".format(error))

    def on_cell_edit(self, event):
        cell_value = self.tree.item(self.tree.selection())['values']
        row = self.tree.selection()[0]
        column_id = self.tree.identify_column(event.x)
        column = self.tree.heading(column_id)['text']

        print("Selected column:", column)

        self.edit_window = tk.Toplevel()
        self.edit_window.title("Edit Cell")
        self.edit_window.geometry("200x100")

        self.new_value_entry = tk.Entry(self.edit_window)
        self.new_value_entry.pack(pady=10)

        self.update_button = tk.Button(self.edit_window, text="Update", command=lambda: self.update_cell(row, column))
        self.update_button.pack()

    def update_cell(self, row, column_name):
        print("Updating cell with column:", column_name)
        new_value = self.new_value_entry.get()

        # Find the index of the column name
        column_index = self.columns.index(column_name)

        self.tree.set(row, column_index, new_value)

        # Get the primary key column name
        primary_key_column = self.columns[0]

        row_id = self.tree.item(row)['values'][0]
        update_query = f"UPDATE your_table SET `{column_name}` = %s WHERE `{primary_key_column}` = %s"

        try:
            self.cursor.execute(update_query, (new_value, row_id))
            self.connection.commit()
            messagebox.showinfo("Success", "Data updated successfully")
        except mysql.connector.Error as error:
            messagebox.showerror("Error", "Failed to update data: {}".format(error))

def load_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return config

root = tk.Tk()
root.title("Table Editor")

config = load_config('config.ini')
app = TableEditor(root, config)

root.mainloop()

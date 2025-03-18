# src/main.py
import tkinter as tk
from tkinter import filedialog, Menu
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.collections import PathCollection
import polars as pl
import numpy as np

from data_generator import DataGen


class MatplotlibTk(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.title("Matplotlib Tk Interface")
        self.geometry("1280x820")

        # Create menubar
        menubar = Menu(self)
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.open_data)
        file_menu.add_command(label="Save", command=self.save_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        edit_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Generate Data", command=self.generate_data)

        self.config(menu=menubar)

        # add a frame for all of the left side widgets.
        self.plot_frame = tk.Frame(self)
        self.plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # stup the tk variables for our entry boxes
        self.x_min_value = tk.DoubleVar()
        self.x_min_value.set(-86.0)
        self.x_max_value = tk.DoubleVar()
        self.x_max_value.set(86.0)
        self.y_min_value = tk.DoubleVar()
        self.y_min_value.set(-76.0)
        self.y_max_value = tk.DoubleVar()
        self.y_max_value.set(76.0)
        # add a frame for limit value entry
        self.limit_frame = tk.Frame(self.plot_frame)
        self.limit_frame.pack(side=tk.TOP, fill=tk.X)
        self.x_min_limit_label = tk.Label(self.limit_frame, text="X Min:")
        self.x_min_limit_label.pack(side=tk.LEFT)
        self.x_min_limit_entry = tk.Entry(self.limit_frame, textvariable=self.x_min_value)
        self.x_min_limit_entry.pack(side=tk.LEFT)
        self.x_max_limit_label = tk.Label(self.limit_frame, text="X Max:")
        self.x_max_limit_label.pack(side=tk.LEFT)
        self.x_max_limit_entry = tk.Entry(self.limit_frame, textvariable=self.x_max_value)
        self.x_max_limit_entry.pack(side=tk.LEFT)
        self.y_min_limit_label = tk.Label(self.limit_frame, text="Y Min:")
        self.y_min_limit_label.pack(side=tk.LEFT)
        self.y_min_limit_entry = tk.Entry(self.limit_frame, textvariable=self.y_min_value)
        self.y_min_limit_entry.pack(side=tk.LEFT)
        self.y_max_limit_label = tk.Label(self.limit_frame, text="Y Max:")
        self.y_max_limit_label.pack(side=tk.LEFT)
        self.y_max_limit_entry = tk.Entry(self.limit_frame, textvariable=self.y_max_value)
        self.y_max_limit_entry.pack(side=tk.LEFT)
        # add a button to regenerate the limit data
        self.regenerate_button = tk.Button(self.limit_frame, text="Regenerate", command=self.generate_data)
        self.regenerate_button.pack(side=tk.LEFT)
        # add a checkbox and variable for selecting legacy limits
        self.legacy_var = tk.BooleanVar(value=False)
        self.legacy_check = ttk.Checkbutton(self.limit_frame, text="Legacy limits", variable=self.legacy_var)
        self.legacy_check.pack(side=tk.LEFT)

        # Initialize plotting area
        self.plot_figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.plot_ax = self.plot_figure.add_subplot(111)

        # Set up canvas to display plots
        self.canvas = FigureCanvasTkAgg(self.plot_figure, master=self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.generate_data()

        # add a frame for the matplotlib navigation bar
        self.nav_frame = tk.Frame(self.plot_frame)
        self.nav_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.nav_toolbar = NavigationToolbar2Tk(self.canvas, self.nav_frame)
        self.nav_toolbar.update()
        self.nav_toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        # add a frame for the right hand side widgets
        self.right_frame = tk.Frame(self)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

        # create Treeview widgets
        self.limit_data_tree = ttk.Treeview(self.right_frame, columns=("Az", "El"), show="headings")
        # set the headings
        self.limit_data_tree.heading("Az", text="Az")
        self.limit_data_tree.heading("El", text="El")
        self.limit_data_tree.column("Az", width=100, anchor='center')
        self.limit_data_tree.column("El", width=100, anchor='center')
        # Create a scrollbar
        self.limit_scroll = ttk.Scrollbar(self.right_frame, orient=tk.VERTICAL, command=self.limit_data_tree.yview)
        # Attach the scrollbar
        self.limit_data_tree.configure(yscrollcommand=self.limit_scroll.set)
        # Add Treeview and Scrollbar to the right frame
        self.limit_data_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.limit_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.limit_data_tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.update_treeview()

        #self.canvas.mpl_connect('motion_notify_event', self.update_status_bar)

    def update_status_bar(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            r, theta = self.plot_ax.transData.inverted().transform((x, y))
            theta = np.degrees(theta) % 360
            status_text = f"Az={theta:.2f}, El={r:.2f}"
            self.plot_figure.canvas.toolbar.set_message(status_text)
        else:
            self.plot_figure.canvas.toolbar.set_message("")

    def update_treeview(self):
        """
        Update the treeview using our current limit data set.
        """
        if hasattr(self, 'limit_data_tree'):
            self.limit_data_tree.delete(*self.limit_data_tree.get_children())
            for row in self.data.rows():
                az, el = row
                el = round(el, 3)
                self.limit_data_tree.insert("", tk.END, values=[az, el])
        else:
            # first run no treeview exists yet
            pass

    def on_tree_select(self, event):
        """
        Highlight a data point on the plot when the data is selected.
        """
        # clear existing scatter points without affecting other plot elements
        for collection in self.plot_ax.collections:
            if isinstance(collection, PathCollection): # check if its a scatter point
                collection.remove()

        selected_items = self.limit_data_tree.selection()
        if selected_items:
            item = selected_items[0]
            theta, r = self.limit_data_tree.item(item, 'values')
            theta = np.radians(float(theta))
            r = round(float(r), 3) # round the "El"
            self.plot_ax.scatter(theta, r, color='red', s=15)
        self.canvas.draw()
            

    def open_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                data = pl.read_csv(file_path)

                if len(data.columns) == 2:  # Cartesian plot
                    x, y = data[data.columns[0]], data[data.columns[1]]
                    self.plot_ax.clear()
                    self.plot_ax.plot(x, y)
                elif len(data.columns) == 3:  # Polar plot
                    r, theta = data[data.columns[0]], data[data.columns[2]] * np.pi / 180  # Convert to radians
                    self.plot_ax.clear()
                    self.plot_ax.polar(theta, r)

            except Exception as e:
                print(f"Error loading file: {e}")

    def save_data(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                self.data.write_csv(file_path)

            except Exception as e:
                print(f"Error saving file: {e}")

    def generate_data(self):
        """
        Generate limit data for the x,y antenna.
        """
        x_lims = (self.x_min_value.get(), self.x_max_value.get())
        y_lims = (self.y_min_value.get(), self.y_max_value.get())
        lims = DataGen((x_lims, y_lims))
        if self.legacy_var.get():
            lims.find_from_point()
        else:
            lims.find_limits()

        self.data = pl.DataFrame(lims.limit_list, orient='row', schema=['az', 'el'])
        theta = self.data[self.data.columns[0]] * np.pi / 180  # Convert 'az' to radians
        r = self.data[self.data.columns[1]]

        if self.plot_ax is None:
            fig = plt.figure(figsize=(5, 4), dpi=100)
            self.plot_ax = fig.add_subplot(111, projection='polar')
        else:
            # Check if the current axes are polar
            if 'theta_zero_location' in dir(self.plot_ax):
                self.plot_ax.clear()
            else:
                # Create a new polar subplot and update the canvas
                self.plot_figure.clear()
                self.plot_ax = self.plot_figure.add_subplot(111, projection='polar')

        # close the plot line
        theta = np.append(theta, theta[0])
        r = np.append(r, r[0])

        self.plot_ax.plot(theta, r)
        self.plot_ax.set_ylim(90,0)
        self.plot_ax.set_theta_direction(-1)
        self.plot_ax.set_theta_offset(np.pi/2)

        self.canvas.draw()

        self.update_treeview()


if __name__ == "__main__":
    app = MatplotlibTk()
    app.mainloop()
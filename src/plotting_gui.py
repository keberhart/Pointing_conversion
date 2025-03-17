# src/main.py
import tkinter as tk
from tkinter import filedialog, Menu
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import polars as pl
import numpy as np

from data_generator import DataGen


class MatplotlibTk(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)

        self.title("Matplotlib Tk Interface")
        self.geometry("1000x1000")

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
        self.limit_frame = tk.Frame(self)
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

        # Initialize plotting area
        self.plot_figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.plot_ax = self.plot_figure.add_subplot(111)

        # Set up canvas to display plots
        self.canvas = FigureCanvasTkAgg(self.plot_figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # add a frame for the matplotlib navigation bar
        self.nav_frame = tk.Frame(self)
        self.nav_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.nav_toolbar = NavigationToolbar2Tk(self.canvas, self.nav_frame)
        self.nav_toolbar.update()
        self.nav_toolbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.mpl_connect('motion_notify_event', self.update_status_bar)

    def update_status_bar(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            r, theta = self.plot_ax.transData.inverted().transform((x, y))
            theta = np.degrees(theta) % 360
            status_text = f"Az={theta:.2f}, El={r:.2f}"
            self.plot_figure.canvas.toolbar.set_message(status_text)
        else:
            self.plot_figure.canvas.toolbar.set_message("")


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
                if hasattr(self.plot_ax, 'lines'):
                    x, y = zip(*self.plot_ax.lines[0].get_data())
                    data = pl.DataFrame({'X': x, 'Y': y})
                else:  # For polar plots
                    angles, radii = self.plot_ax.lines[0].get_data()
                    data = pl.DataFrame({'Theta': angles * 180 / np.pi, 'Radius': radii})

                data.write_csv(file_path)

            except Exception as e:
                print(f"Error saving file: {e}")

    def generate_data(self):
        """
        Generate limit data for the x,y antenna.
        """
        x_lims = (self.x_min_value.get(), self.x_max_value.get())
        y_lims = (self.y_min_value.get(), self.y_max_value.get())
        lims = DataGen((x_lims, y_lims))

        data = pl.DataFrame(lims.limit_list, schema=['az', 'el'])
        theta = data[data.columns[0]] * np.pi / 180  # Convert 'az' to radians
        r = data[data.columns[1]]

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
        self.plot_ax.set_ylim(90, 0)
        self.plot_ax.set_theta_direction(-1)
        self.plot_ax.set_theta_offset(np.pi/2)

        self.canvas.draw()


if __name__ == "__main__":
    app = MatplotlibTk()
    app.mainloop()
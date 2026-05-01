from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.setParent(parent)

    def update_plot(self, x_data, y_data):
        self.axes.clear()
        self.axes.plot(x_data, y_data)
        self.axes.set_xlabel('time (s)')
        self.axes.set_ylabel('throttle (%)')
        self.draw()

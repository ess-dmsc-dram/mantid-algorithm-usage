import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


class PlotPDF:
    def __init__(self, filename):
        self._pdf = PdfPages(filename)
        self._colors = ['gold', 'yellowgreen', 'lightcoral', 'lightskyblue', 'yellow', 'green', 'grey']
        self._explode = (0.2, 0.1, 0.05, 0, 0, 0, 0)
        self._current_figure = 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._pdf.close()

    def plot_pie(self, data, labels, title=''):
        self._enter_plot()

        plt.axes([0.1, 0.1, 0.8, 0.75])
        plt.pie(data, explode=self._explode[0:len(data)], labels=labels, colors=self._colors[0:len(data)],
                autopct='%1.1f%%', shadow=True, startangle=110)
        plt.title(title)
        plt.title(title, y=1.07)
        # Set aspect ratio to be equal so that pie is drawn as a circle.
        plt.axis('equal')
        #plt.tight_layout()

        self._exit_plot()

    def plot_bars(self, data, labels, title=''):
        self._enter_plot()

        y_pos = range(len(data), 0, -1)
        plt.barh(y_pos, data, align='center', alpha=0.4)
        plt.yticks(y_pos, labels)
        #plt.xlabel('Number of algorithms')
        plt.title(title, y=1.04)
        plt.tight_layout()

        self._exit_plot()

    def _enter_plot(self):
        plt.figure(self._current_figure)

    def _exit_plot(self):
        self._pdf.savefig()
        self._current_figure = self._current_figure + 1

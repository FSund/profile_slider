import numpy as np
import matplotlib.pyplot as plt
# import matplotlib
from matplotlib.widgets import Slider
import itertools
import io
import os.path


class ProfileSlider:
    def __init__(
            self,
            path="./",
            files=["massFlow.csv", "pressure.csv", "temperature.csv"],
            labels=["Mass flow [kg/s]", "Pressure [Pa]", "Temperature [K]"],
            load_x_from_file=True, n_max=0
    ):

        # support for single file (files and labels as strings instead of
        # iterable/list)
        if isinstance(files, str):
            files = [files]
        if isinstance(labels, str):
            labels = [labels]

        assert len(files), "Need at least one file"

        if len(labels) > len(files):
            labels = labels[0:len(labels)]

        nlines = self.file_len(path + files[0])
        # chech that all files have same length
        if len(files) > 1:
            for file in files[1:]:
                assert nlines == self.file_len(
                    path + file), "All files should have same length"

        data = []
        if nlines > 10000:
            # only load a limited number of lines
            divisor = int(round(nlines / 1000.0))
            print("Only loading every %d lines (%d of %d lines)" %
                  (divisor, nlines / divisor, nlines))
            for filename in files:
                with io.open(path + filename, 'rt') as f_in:
                    data.append(np.loadtxt(itertools.islice(
                        f_in, 0, None, divisor), delimiter=','))
        else:
            for filename in files:
                data.append(np.loadtxt(path + filename, delimiter=','))

        # discard some data
        if n_max:
            for i in range(len(data)):
                data[i] = data[i][0:n_max]

        # check that time vectors are equal
        if len(files) > 1:
            t0 = data[0][:, 0]
            for d in data[1:]:
                t = d[:, 0]
                assert np.allclose(t, t0), "Time vectors are not equal"

        self.y = []
        for d in data:
            self.y.append(d[:, 1:])
        t = data[0][:, 0]
        t -= t[0]
        t = t / 60.0
        self.t = t

        if load_x_from_file:
            path, _ = os.path.split(path + files[0])
            x = np.loadtxt(os.path.join(path, "gridPoints.csv"), delimiter=',')
            x = x / 1000.0
        else:
            x = np.arange(0, len(self.t), 1)
        self.x = x

        self.fig = plt.figure(figsize=np.array([16, 9]) / 2)
        self.fig.canvas.mpl_connect('key_press_event', self.key)
        # self.fig.canvas.mpl_connect('key_release_event', self.key)

        ax = self.fig.add_subplot(111)
        self.axes = []
        self.axes.append(ax)
        self.lines = []
        for i in range(1, len(files)):
            self.axes.append(ax.twinx())

        for i, ax in enumerate(self.axes):
            color = "C%d" % i

            line, = ax.plot(self.x, self.y[i][0, :], color=color)
            self.lines.append(line)
            span = np.max(self.y[i]) - np.min(self.y[i])
            ax.set_ylim([np.min(self.y[i]) - span * 0.05,
                         np.max(self.y[i]) + span * 0.05])

            label = labels[i]
            ax.set_ylabel(label, color=color)
            ax.tick_params(axis='y', colors=color)

            # fix labels and locations, since twinx puts all twin axes on the
            # right side
            ax.get_yaxis().set_label_position("left")
            ax.get_yaxis().set_tick_params(right='off', left='on',
                                           labelleft=True, labelright=False)

        # make room for all axes
        if len(files) > 1:
            width_fraction = 0.09
            self.fig.subplots_adjust(left=width_fraction * len(files))

        # move axes so they all show
        for i in range(1, len(files)):
            # approx width of axis with tick marks, tick labels and label
            pos = -0.15 * i

            self.axes[i].spines['left'].set_position(('axes', pos))
            self.axes[i].get_yaxis().get_offset_text().set_x(pos)

        self.axes[0].set_xlim([x[0], x[-1]])
        # self.axes[0].grid() # looks bad when extra axes are added
        self.tmin = t[0]
        self.tmax = t[-1]

        self.line = line
        # make room for slider and title
        self.fig.subplots_adjust(top=0.9, bottom=0.15)
        self.title = self.fig.suptitle("Title")
        slider_ax = self.fig.add_axes(
            [0.15, 0.025, 0.7, 0.05])  # x, y, width, height
        self.slider = Slider(
            ax=slider_ax, label='Time',
            valmin=self.tmin, valmax=self.tmax, valinit=self.tmin,
            valfmt='%.0f min'
        )
        self.i = 0

        self.slider.on_changed(self.update)

    def key(self, event):
        if event.key == 'left':
            # check that we have room to move slider
            if self.slider.val > self.tmin:
                self.i -= 1
                self.slider.set_val(self.t[self.i])
        elif event.key == 'right':
            # check that we have room to move slider
            if self.slider.val < self.tmax:
                self.i += 1
                self.slider.set_val(self.t[self.i])
        else:
            pass

    def update(self, val):
        i = self.find_nearest(self.t, self.slider.val)
        self.i = i

        # (use blitting instead of updating everything)
        # this seems to work fine without blitting...
        for ax, y, line in zip(self.axes, self.y, self.lines):
            line.set_ydata(y[i, :])
            # ax.draw_artist(line)

        self.title.set_text("t = %d minutes (#%d)" % (self.t[i], i))

        # fig.canvas.blit(ax.bbox) # blit just axis
        # self.fig.canvas.blit(self.fig.bbox) # blit everything to get new
        # title -- this might leak memory?

    def file_len(self, fname):
        with open(fname) as f:
            for i, l in enumerate(f):
                pass
        return i + 1

    def find_nearest(self, array, value):
        idx = (np.abs(array - value)).argmin()
        return idx

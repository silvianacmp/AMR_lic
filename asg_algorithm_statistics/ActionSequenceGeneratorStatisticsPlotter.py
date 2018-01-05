import matplotlib.pyplot as plt
from os import path

abs_path = path.abspath('./plots_asg_statistics')
print abs_path

def plot_histogram(histogram_data, histogram_names, alg_version, subdirectory,filename):
    """
       Description:
            plots histograms to a file
       Args:
            histogram_data - list of dictionaries representing the histograms
            histogram_names - list of histogram names (the titles for each histogram)
            alg_version - alg version, for example: no_swap, swap_10, swap_1 :?
            subdirectoy - name of the subdirectory to plot in (the plot will be saved in "./plots_asg_statistics/subdirectory/filename.png"
            filename - name of file to which the plot will be saved
    """

    no_of_hists = len(histogram_data)
    p = abs_path + "/"+alg_version+"/" + subdirectory + "/" + filename + ".png";
    fig, axes = plt.subplots(nrows=no_of_hists, ncols=1, figsize=(10, 5*no_of_hists), sharey=True)

    for i in range(0, no_of_hists):
        ax = axes[i]
        ax.set_title(histogram_names[i])
        x_data = range(len(histogram_data[i]))
        y_data = list(histogram_data[i].values())
        labels = list(histogram_data[i].keys())
        ax.bar(x_data,y_data , align='center')
        # put the value of each bar above the bar
        for x, y in zip(x_data, y_data):
            ax.text(x, y, str(y))
        ax.set_xticks(x_data, minor=False)
        ax.set_xticklabels(labels, fontdict=None, minor=False)

    plt.savefig(p)
    plt.close('all')

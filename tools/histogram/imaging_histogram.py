from matplotlib.ticker import FuncFormatter
import matplotlib
#Force matplotlib to not use any Xwindows backend
matplotlib.use('Agg')
import subprocess
import pandas as pd
import seaborn as sns
import sys
import optparse
import numpy as np
import matplotlib.pyplot as plt
 
def millions_formatter_fcn(x, p):
    return "%2.1fM" % (x / 1E6)

def plot_histogram(input,output):

    millions_formatter = FuncFormatter(millions_formatter_fcn)

    spreadsheet = pd.read_csv(input)

    data = spreadsheet.\
        rename(columns={
            "AreaOccupied_AreaOccupied_ThreshCK":   "epithelial_area",
            "AreaOccupied_AreaOccupied_ThreshSMA":  "stroma_area",
            "AreaOccupied_AreaOccupied_ThreshSYP":  "endocrine_area",
            "AreaOccupied_TotalArea_ThreshCK":      "total_area",
            "AreaOccupied_TotalArea_ThreshSMA":     "stroma_total_area",
            "AreaOccupied_TotalArea_ThreshSYP":     "endocrine_total_area",
            "Count_ExpandNuclei":                   "expanded_nuclei_count",
            "Count_Filtered":                       "filtered_nuclei_count",
            "Count_Nuclei":                         "nuclei_count",
            "Count_StrictFiltered":                 "strict_filtered_nuclei_count",
            "FileName_OrigDAPI":                    "filename",
            "ImageNumber":                          "image_number"
            })\
        [["image_number",
         "epithelial_area",
         "stroma_area",
         "endocrine_area",
         "total_area",
         "nuclei_count",
         "filtered_nuclei_count",
         "strict_filtered_nuclei_count"]]
 
    stats = pd.DataFrame({
        "covered_area":                       data[["epithelial_area", "stroma_area", "endocrine_area"]].sum(axis=1),
        "epithelial_area":                    data["epithelial_area"],
        "stroma_area":                        data["stroma_area"],
        "endocrine_area":                     data["endocrine_area"],
        "filtered_nuclei":                    data["nuclei_count"] - data["filtered_nuclei_count"],
        "strict_filtered_nuclei":             data["nuclei_count"] - data["filtered_nuclei_count"],
        "remaining_nuclei":                   data["filtered_nuclei_count"] - data["strict_filtered_nuclei_count"]})
 
    # Sort our stats based on total covered area, in descending order.
    stats = stats.sort("covered_area", ascending=False)
 
    summed_stats = pd.DataFrame(stats.sum(axis=0)).transpose()
 
    # Set some defaults for the bar plots
    x_positions = np.arange(len(stats))
    width = 0.35
    colors = sns.color_palette("Set2", 6)
 
    gs = matplotlib.gridspec.GridSpec(2, 2, width_ratios=[5, 1])
 
    plt.clf()
 
    plt.subplot(gs[0])
 
    plt.bar(x_positions, stats["endocrine_area"], width, label="Endocrine", color=colors[0])
    plt.bar(x_positions, stats["stroma_area"], width, bottom=stats["endocrine_area"], label="Stroma", color=colors[1])
    plt.bar(x_positions, stats["epithelial_area"], width, bottom=stats["endocrine_area"] + stats["stroma_area"], label="Epithelial", color=colors[2])
 
    plt.gca().yaxis.set_major_formatter(millions_formatter)
    plt.gca().xaxis.set_ticklabels([])
 
    plt.ylabel("Area")
 
    handles, labels = plt.gca().get_legend_handles_labels()
    plt.legend(handles[::-1], labels[::-1])
 
    plt.title("Tile Composition")
 
    plt.subplot(gs[1])
 
    plt.bar([0], summed_stats["endocrine_area"], width, label="Endocrine", color=colors[0])
    plt.bar([0], summed_stats["stroma_area"], width, bottom=summed_stats["endocrine_area"], label="Stroma", color=colors[1])
    plt.bar([0], summed_stats["epithelial_area"], width, bottom=summed_stats["endocrine_area"] + summed_stats["stroma_area"], label="Epithelial", color=colors[2])
 
    plt.gca().yaxis.set_major_formatter(millions_formatter)
    plt.gca().xaxis.set_ticklabels([])
 
    plt.title("Global\nComposition")
 
    plt.subplot(gs[2])
 
    plt.bar(x_positions, stats["remaining_nuclei"], width, label="Strict Filter", color=colors[3])
    plt.bar(x_positions, stats["strict_filtered_nuclei"], width, bottom=stats["remaining_nuclei"], label="Permissive Filter", color=colors[4])
    plt.bar(x_positions, stats["filtered_nuclei"], width, bottom=stats["remaining_nuclei"] + stats["strict_filtered_nuclei"], label="No Filter", color=colors[5])
 
    plt.gca().xaxis.set_ticklabels([])
 
    plt.ylabel("Nuclei Count")
 
    handles, labels = plt.gca().get_legend_handles_labels()
    plt.legend(handles[::-1], labels[::-1])
 
    plt.xlabel("Tile")
 
    plt.title("Epithelial Nuclei Counts")
 
    plt.subplot(gs[3])
 
    plt.bar([0], summed_stats["remaining_nuclei"], width, label="Strict Filter", color=colors[3])
    plt.bar([0], summed_stats["strict_filtered_nuclei"], width, bottom=summed_stats["remaining_nuclei"], label="Permissive Filter", color=colors[4])
    plt.bar([0], summed_stats["filtered_nuclei"], width, bottom=summed_stats["remaining_nuclei"] + summed_stats["strict_filtered_nuclei"], label="No Filter", color=colors[5])
 
    plt.gca().xaxis.set_ticklabels([])
 
    plt.title("Global Epithelial\nNuclei Counts")
 
    plt.savefig('plot.png')
    subprocess.call('mv plot.png '+output,shell=True)

if __name__ == "__main__":
    #Read in input/output references
    parser = optparse.OptionParser()
    parser.add_option('-i',dest='input')
    parser.add_option('-o',dest='output')
    opts, args = parser.parse_args()

    plot_histogram(opts.input,opts.output)

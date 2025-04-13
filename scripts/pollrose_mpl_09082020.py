#!/usr/bin/env python
import numpy as np
import argparse
import pandas as pd
from matplotlib import pyplot as plt

# getting data and arguments
parser = argparse.ArgumentParser("Providing arguments for pollution rose plots")
parser.add_argument('--ifile', dest='ifile', required=True,
                     help='Input data file (.csv format)')
parser.add_argument('--site', dest='site', required=True,
                     help='Site name')
parser.add_argument('--bdate', dest='bdate', required=True,
                     help='Begin date (format: 1-1-2018)')
parser.add_argument('--edate', dest='edate', required=True,
                     help='End date (format: 12-31-2018)')
parser.add_argument('--pollv', dest='pollv', required=True,
                     help='Pollutant variable name (H2S or NO2)')
parser.add_argument('--wind-dir', dest='winddir', default='WD',
                     help='Wind direction variable')
parser.add_argument('--binwidth', dest='binwidth', type=float,
                     default=45., help='Direction bin width (degrees)')
parser.add_argument('--wscut', dest='wscut', type=float,
                     default=0.0, help='Wind speed cut-off (excluded)')
parser.add_argument('--max-pct', dest='maxpct', type=float,
                     default=50., help='Maximum percent on plot')
parser.add_argument('--fromnorth', dest='fromnorth', action='store_true',
                     default=False, help='Bins should start from north')
parser.add_argument('--bounds', dest='bounds', type=lambda x: np.array(eval(x)),
                     default=np.array([10, 20, 30, 50, 100, 120, 140, np.inf]), 
                     help='Boundaries for pollutant bins')
parser.add_argument('--outpath', dest='outpath', type=str, required=True,
                     help='Output directory for plots')
args = parser.parse_args()

# Read CSV data
wd_data = pd.read_csv(args.ifile, index_col=False, engine='python')
print("Aavailable columns in dataset: ", wd_data.columns.tolist())

# Function to calculate calm wind conditions
def calmws(wd_data, pollv):
    # Convert column names and pollutant name to lowercase
    wd_data.columns = map(str.lower, wd_data.columns)
    pollv = pollv.lower()
    print("Normalized columns in dataset:", wd_data.columns.tolist())
    if pollv not in wd_data.columns:
        raise ValueError(f"Error: Pollutant '{pollv}' not found in dataset! Available: {list(wd_data.columns)}")
    
    calm_data = wd_data.loc[wd_data['ws'] <= args.wscut]
    calm_per = round(calm_data.ws.size * 100 / float(wd_data.ws.size), 1)
    calm_max = round(calm_data[pollv].max(), 3)
    calm_ave = round(calm_data[pollv].mean(), 3)
    
    return calm_per, calm_max, calm_ave

# Function to generate pollution rose plot
def pollrose(wd_data, args):
     # Convert column names to lowercase
    wd_data.columns = map(str.lower, wd_data.columns)
     # Convert user input pollutant to lowercase
    pollutant = args.pollv.lower()
    winddir = args.winddir.lower()
    print("Normalized columns in dataset:", wd_data.columns.tolist())  # Debugging
    
     # Ensure the required columns exist
    if pollutant not in wd_data.columns:
        raise ValueError(f"Error: Pollutant '{pollutant}' not found in dataset! Available: {list(wd_data.columns)}")
    if winddir not in wd_data.columns:
        raise ValueError(f"Error: Wind direction '{winddir}' not found in dataset! Available: {list(wd_data.columns)}")

    # Now it correctly selects 'pm25'
    # Compute calm wind statistics
    calm_per, calm_max, calm_ave = calmws(wd_data, args.pollv)

    # Exclude calm wind conditions
    wd_data = wd_data.loc[wd_data['ws'] > args.wscut]

    # Select pollutant dynamically
    poll = wd_data[pollutant]
    wd = wd_data[winddir]
    ws = wd_data['ws']

    # Bar width
    width = args.binwidth
    halfwidth = width / 2.

    # Setup plot
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_axes([0.1, 0.07, 0.8, 0.8], polar=True)
    ax.set_theta_offset(np.radians(90))
    ax.set_theta_direction(-1)

    # Get bounds and assign colors
    ubs = args.bounds[1:]
    lbs = args.bounds[:-1]
    #   ubcs = plt.cm.jet(np.arange(len(ubs), dtype='float64') / ubs.size)
    # adding colors
    ubcs = plt.cm.jet(np.arange(len(ubs), dtype='f') / ubs.size)
    color_dict = dict(zip(ubs, ubcs))

    # Mask invalid data
    mask = np.ma.getmaskarray(poll) | np.ma.getmaskarray(wd) | (poll < args.bounds[0]) | (poll > args.bounds[-1])
    poll = np.ma.masked_where(mask, poll).compressed()
    wd = np.ma.masked_where(mask, wd).compressed()

    # Compute thetas
    if args.fromnorth:
        thetas = (np.radians((wd + halfwidth) // width * width) % (2 * np.pi)).astype("float64")
    else:
        thetas = (np.radians((wd.astype("int64") + halfwidth) // width * width - halfwidth) % (2 * np.pi)).astype("float64")

    # Plot data
    uthetas = np.unique(thetas)
    npolls = float(poll.size)
    
    for theta in uthetas:
        tpoll = poll[thetas == theta]
        for ub in reversed(ubs):
            ubc = color_dict[ub]
            pct = (tpoll < ub).sum() / npolls * 100.
            ax.bar(theta, pct, width=np.radians(width), bottom=0.0, color=ubc)

    # Plot labels
    ax.set_title(f"Pollution Rose - {args.site} ({args.pollv})", fontsize=14)
    ticks = np.linspace(0, args.maxpct, 6)[1:]
    labels = ['%s%%' % int(i) for i in ticks]
    plt.yticks(ticks, labels)
    ax.set_rmax(args.maxpct)

    # Save figure
    figpath = f"{args.outpath}/PRose_{args.site}_{args.bdate}_{args.edate}_{args.pollv}.png"
    fig.savefig(figpath, transparent=True)
    print(f"Saved figure: {figpath}")
    plt.close(fig)

# Run pollution rose function
pollrose(wd_data, args)

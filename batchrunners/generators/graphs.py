import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ternary

from batchrunners.const import *
from ctmmodels.const import *
from ctmmodels.delaythroughput import DelayThroughputSimplex as Model


class GraphGenerator(object):

    def __init__(self, headless=True, time_range=TIME_RANGE, simplex_range=10, folder=None, image_path=IMAGE_PATH):
        self.headless = headless
        self.time_range = time_range
        self.time_ticks = np.arange(0, time_range+1, 1)
        self.simplex_range = simplex_range
        self.image_path = image_path
        self.folder = folder

    def plot_volume(self, dfx, cell_path, title, filename='volume.png'):
        dfx_approach = pd.concat([
            dfx[dfx.cell == c].sort_values(by='timestep')
            for c in cell_path
        ]).pivot(index='timestep', columns='cell', values='volume')
        
        fig, axs = plt.subplots(1,2, figsize=(20,10))
        
        sns.lineplot(data=dfx_approach, ax=axs[0])
        sns.lineplot(data=dfx_approach.cumsum(), ax=axs[1])

        axs[0].set_title('Volume of cells')
        axs[0].set_xlabel('Timesteps')
        axs[0].set_ylabel('Instantaneous volume')
        axs[0].set_xticks(self.time_ticks, minor=True)

        axs[1].set_title('Volume of cells (cumulative)')
        axs[1].set_xlabel('Timesteps')
        axs[1].set_ylabel('Cumulative volume')
        axs[1].set_xticks(self.time_ticks, minor=True)
        
        fig.suptitle(title, fontsize=18)
        
        if self.headless:
            fig.savefig(os.path.join(self.image_path, self.folder, filename))
            plt.close(fig)
        else:
            return fig

    def plot_flow(self, dfy, cell_path, title, filename='flow.png'):
        dfy_approach = pd.concat([
            dfy[dfy.cell_from == c].groupby(['cell_from', 'timestep']).agg({'flow': 'sum'}).sort_values(by='timestep')
            for c in cell_path
        ]).reset_index().pivot(index='timestep', columns='cell_from', values='flow')
        
        fig, axs = plt.subplots(1,2, figsize=(20,10))

        sns.lineplot(data=dfy_approach, ax=axs[0])
        sns.lineplot(data=dfy_approach.cumsum(), ax=axs[1])

        axs[0].set_title('Flow from cells')
        axs[0].set_xlabel('Timesteps')
        axs[0].set_ylabel('Instantaneous flow')
        axs[0].set_xticks(self.time_ticks, minor=True)

        axs[1].set_title('Flow from cells (cumulative)')
        axs[1].set_xlabel('Timesteps')
        axs[1].set_ylabel('Cumulative flow')
        axs[1].set_xticks(self.time_ticks, minor=True)
        
        fig.suptitle(title, fontsize=18)
        
        if self.headless:
            fig.savefig(os.path.join(self.image_path, self.folder, filename))
            plt.close(fig)
        else:
            return fig

    def plot_greentime(self, dfg, title, filename='greentime.png'):
        dfg_map = dfg.pivot(index='timestep', columns='cell', values='is_green')

        fig, axs = plt.subplots(8,1,figsize=(18,18), sharey=True)

        for ndx, t in enumerate(_all_phases):
            sns.lineplot(data=dfg_map[t], ax=axs[ndx])
            axs[ndx].text(0.01,.5,self.all_phases_labels[ndx],
                horizontalalignment='left',
                transform=axs[ndx].transAxes,
                fontsize='large')
            axs[ndx].set_xticks(self.time_ticks, minor=False)
        
        fig.suptitle(title, fontsize=18)
        
        if self.headless:
            fig.savefig(os.path.join(self.image_path, self.folder, filename))
            plt.close(fig)
        else:
            return fig

    def plot_obj_values(self, df, title_partial, filename_partial='obj'):
        df_nparr = df.values
        delay_dict = {}
        thru_dict = {}
        runtime_dict = {}
        obj_dict = {}

        for row in df_nparr:
            runtime_dict[(row[-3]*self.simplex_range, row[-2]*self.simplex_range, row[-1]*self.simplex_range)] = row[1]
            delay_dict[(row[-3]*self.simplex_range, row[-2]*self.simplex_range, row[-1]*self.simplex_range)] = row[2]
            thru_dict[(row[-3]*self.simplex_range, row[-2]*self.simplex_range, row[-1]*self.simplex_range)] = row[3]
            obj_dict[(row[-3]*self.simplex_range, row[-2]*self.simplex_range, row[-1]*self.simplex_range)] = row[4]

        self.plot_simplex(delay_dict, "{} (Delay)".format(title_partial), "{}_delay.png".format(filename_partial), cb_kwargs={'vmin': 1200, 'vmax': 6000})
        self.plot_simplex(thru_dict, "{} (Throughput)".format(title_partial), "{}_throughput.png".format(filename_partial), cb_kwargs={'vmin': 42, 'vmax': 45})
        self.plot_simplex(obj_dict, "{} (Objective Value)".format(title_partial), "{}_obj.png".format(filename_partial), cb_kwargs={'vmin': -3000, 'vmax': 5000})
        self.plot_simplex(runtime_dict, "{} (Runtime)".format(title_partial), "{}_runtime.png".format(filename_partial), cb_kwargs={'vmin': 1, 'vmax': 100})

    def plot_simplex(self, data, title, filename, tax=None, cb_kwargs={}):
        if tax is None:
            fig, tax = ternary.figure(scale=self.simplex_range)
            fig.set_size_inches(10, 8)
        else:
            fig = None

        tax.heatmap(data, style="triangular", **cb_kwargs)
        tax.boundary(linewidth=2.0)

        tax.set_title(title)
        tax.bottom_axis_label("Delay weight $\\alpha$", fontsize=12, offset=0.14)
        tax.right_axis_label("Throughput weight $\\beta$", fontsize=12, offset=0.14)
        tax.left_axis_label("Flow maximization $\\gamma$", fontsize=12, offset=0.14)

        tax.ticks(axis='lbr', linewidth=1, multiple=5)
        tax.clear_matplotlib_ticks()
        tax._redraw_labels()

        if fig is not None:
            if self.headless:
                fig.savefig(os.path.join(self.image_path, self.folder, filename))
                plt.close(fig)
            else:
                return fig

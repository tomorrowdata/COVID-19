import os
from PIL import Image
from matplotlib import pyplot as plt, dates as mdates, cbook, image

FIGSIZE=(30,15)
TITLE_FONTSIZE=30
LABEL_FONTSIZE=27
TICK_FONTSIZE=30
TICK_LABEL_ROTATION=45
TICK_WIDTH=5
LEGEND_FONTSIZE=30

def _create_figure(
    figsize=FIGSIZE, 
    title='', x_label='', y_label='', 
    xlim=None, ylim=None,
    title_fontsize=TITLE_FONTSIZE,
    label_fontsize=LABEL_FONTSIZE,
    tick_fontsize=TICK_FONTSIZE,
    tick_label_rotation=TICK_LABEL_ROTATION,
    tick_width=TICK_WIDTH
):

    fig, ax = plt.subplots(figsize=figsize)

    ax.set_title(title, fontsize=title_fontsize)

    ax.set_xlabel(x_label, fontsize=label_fontsize)
    ax.set_ylabel(y_label, fontsize=label_fontsize)

    ax.tick_params(axis='both', labelsize=tick_fontsize)
    ax.tick_params(axis='x', labelrotation=tick_label_rotation)
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.WE))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.xaxis.set_tick_params(width=tick_width)
    ax.yaxis.set_tick_params(width=tick_width)
    ax.grid()

    if ylim:
        ax.set_ylim(*ylim)
    if xlim:
        ax.set_xlim(*xlim)    

    return fig, ax

def plot_env(plot_func):
    def wrapper(
        *args, 
        figsize=FIGSIZE, 
        title='', x_label='', y_label='', 
        xlim=None, ylim=None,
        title_fontsize=TITLE_FONTSIZE,
        label_fontsize=LABEL_FONTSIZE,
        tick_fontsize=TICK_FONTSIZE,
        tick_label_rotation=TICK_LABEL_ROTATION,
        tick_width=TICK_WIDTH,
        legend_fontsize=LEGEND_FONTSIZE,
        legend_on=True,
        legend_loc='upper left', 
        img_file_path_without_extension=None,
        dpi=300,
        quality=90,
        **kwargs):

        fig, ax = _create_figure(
            figsize, 
            title, x_label, y_label, 
            xlim, ylim, 
            title_fontsize, label_fontsize, tick_fontsize, tick_label_rotation, tick_width
        )

        plot_func(ax, *args, **kwargs)

        if legend_on:
            _ = ax.legend(fontsize=legend_fontsize, loc=legend_loc)


        if img_file_path_without_extension:
            png_path = '{}.png'.format(img_file_path_without_extension)
            jpg_path = '{}.jpg'.format(img_file_path_without_extension)
            plt.savefig(png_path, dpi=dpi)
            im = Image.open(png_path)
            rgb_im = im.convert('RGB')
            rgb_im.save(jpg_path, optimize=True, quality=quality)

        plt.show()

    return wrapper


@plot_env
def errorbar(ax, x, y, bars, label):

    ax.errorbar(
        x, 
        y, 
        bars,
        uplims=True, lolims=True,
        label=label
    )


@plot_env
def plot_series(ax, df=None, yfields=None, data=None, xfield='data'):

    if data is None and df is not None:
        data=[{}]
        data[0]['df'] = df
        data[0]['yfields'] = yfields
        data[0]['labels'] = yfields
        
    for d in data:
        df = d['df']
        yfields = d['yfields']

        if 'xfield' in d:
            x = df.loc[:,[d['xfield']]]
        else:
            x = df.loc[:,[xfield]]

        if 'bars' in d:
            plotfunc = ax.errorbar
            bars = d['bars']
        else:
            plotfunc = ax.plot
            bars=None

        if 'labels' in d:
            labels = d['labels']
        else:
            labels = yfields

        if 'colors' in d:
            colors = d['colors']
        else:
            colors = None

        for f in yfields:
            findex = yfields.index(f)
            args = (x.to_numpy(), df.loc[:,[f]].to_numpy())

            kwargs={
                'label': labels[findex],
                'linestyle': ':', 'marker': 'o'
            }
            if colors:
                kwargs.update({'color':colors[findex]})
                
            if bars:
                yerr = df.loc[:,bars[findex]].to_numpy().T
                kwargs.update({'yerr': yerr, 'uplims':True, 'lolims':True})
            plotfunc(
                *args,
                **kwargs
            )

        if 'fill_between' in d:
            interval = d['fill_between']
            ax.fill_between(
                x.to_numpy().squeeze(), 
                df.loc[:,interval[0]].to_numpy().T,
                df.loc[:,interval[1]].to_numpy().T,
                color='violet', alpha=.25,
            )                


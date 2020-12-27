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
        legend_loc='upper left', 
        img_file_path_without_extension=None,
        dpi=300,
        **kwargs):

        fig, ax = _create_figure(
            figsize, 
            title, x_label, y_label, 
            xlim, ylim, 
            title_fontsize, label_fontsize, tick_fontsize, tick_label_rotation, tick_width
        )

        plot_func(ax, *args, **kwargs)

        _ = ax.legend(fontsize=legend_fontsize, loc=legend_loc)

        plt.show()

        if img_file_path_without_extension:
            png_path = '{}.png'.format(img_file_path_without_extension)
            jpg_path = '{}.jpg'.format(img_file_path_without_extension)
            plt.savefig(png_path, dpi=dpi)
            im = Image.open(png_path)
            rgb_im = im.convert('RGB')
            rgb_im.save(jpg_path)

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
        if 'labels' in d:
            labels = d['labels']
        else:
            labels = yfields
            
        for f in yfields:
            ax.plot(
                df.loc[:,[xfield]], 
                df.loc[:,[f]], 
                label=labels[yfields.index(f)], 
                linestyle=':', marker='o'
            )


def plot_MCMC_sampling(df, column, ISS_df, ylim=(0,3), xlim=None, average=True, std=True, conf_int=False, path=None, dpi=None):
            
    fig, ax1 = plt.subplots(figsize=(30,15))
    ax1.set_title('', fontsize=30)
    ax1.tick_params(axis='both', labelsize=27)
    ax1.tick_params(axis='x', labelrotation=45)

    ax1.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.WE))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax1.xaxis.set_tick_params(width=5)
    ax1.yaxis.set_tick_params(width=5)
    ax1.grid()    

    updatemessage = 'Aggiornamento del {}'.format(df.data.max().strftime('%d %b %Y'))
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)    
    ax1.text(0.65, 0.97, updatemessage, transform=ax1.transAxes, fontsize=24,
            verticalalignment='top', bbox=props)    
    
    ax1.set_ylim(*ylim)
    if xlim:
        ax1.set_xlim(*xlim)
        
    date = df['data'].dt.normalize()
    ax1.plot(
        date, 
        df['{}_Rt_MCMC'.format(column)], 
        label='Stima di $R_t$ sul valore dei $nuovi\_positivi$ giornalieri, dati Protezione Civile',
        marker='o', color = 'orange'
    )

    if conf_int:
        ax1.fill_between(
            date, 
            df['{}_Rt_MCMC_CI_95_min'.format(column)],
            df['{}_Rt_MCMC_CI_95_max'.format(column)],
            color='orange', alpha=.3,
            label="95% confidence interval"
        )

    print('{}_Rt_MCMC_HDI_95_min'.format(column))
    ax1.fill_between(
        date, 
        df['{}_Rt_MCMC_HDI_95_min'.format(column)],
        df['{}_Rt_MCMC_HDI_95_max'.format(column)],
        color='violet', alpha=.3, 
        label = '95% credible interval'
    )

    if average:
        ax1.plot(
            date, 
            df['{}_Rt_MCMC_avg14'.format(column)], 
            label='Avg14 Rt MCMC Estimate - {}'.format(column),
            marker='o', color = 'green'
        )    

    if std:
        ax1.fill_between(
            date, 
            df['{}_Rt_MCMC_CI_95_14_min'.format(column)],
            df['{}_Rt_MCMC_CI_95_14_max'.format(column)],
            color='blue', alpha=.25,
            label="95% confidence interval on 14 days average"
        )

    ISS_ref_date = ISS_df.Rt_reference_date.dt.normalize()
    ax1.errorbar(
        ISS_ref_date, 
        ISS_df.Rt, 
        ISS_Rt_clean.loc[:,['Rt_95_err_min','Rt_95_err_max']].to_numpy().T,
        uplims=True, lolims=True,
        label='Stima di $R_t$ pubblicata dall\'Istituto Superiore di Sanità, con intervallo di credibilità 95%',
        marker='o', color = 'blue'
    )


    _ = ax1.legend(fontsize=27, loc='lower right')
    
    if path:
        plt.savefig(path.format('png'), dpi=dpi)

        im = Image.open(path.format('png'))
        rgb_im = im.convert('RGB')
        rgb_im.save(path.format('jpg'))
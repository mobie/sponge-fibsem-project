# new spec
# from mobie import add_image, add_segmentation

# old spec
from mobie import initialize_dataset


def add_cell(path, ds_name, resolution, key='*.tif'):
    scale_factors = 5 * [[2, 2, 2]]
    chunks = [64, 64, 64]
    root = '/g/emcf/pape/sponge-fibsem-project/data'

    # new spec
    # add_image(path, key, root=root, dataset_name=ds_name,
    #           image_name='raw', resolution=resolution, scale_factors=scale_factors,
    #           menu_name='fibsem', target='local', chunks=chunks, max_jobs=16)

    # old spec
    initialize_dataset(path, key, root=root, dataset_name=ds_name,
                       raw_name='fibsem-raw', resolution=resolution,
                       scale_factors=scale_factors,
                       target='local', chunks=chunks, max_jobs=24)


def add_cell1():
    path = '/g/emcf/schwab/For Constantin/aligned_cropped_cell1'
    res = [0.008] * 3
    add_cell(path, 'cell1', resolution=res)


def add_cell3():
    path = '/g/emcf/schwab/For Constantin/aligned_cropped_cell3'
    res = [0.008, 0.005, 0.005]
    add_cell(path, 'cell3', resolution=res)


# Is this one of the cells above? Or is it a different one.
def add_chamber_raw():
    path = '/g/emcf/schwab/For Constantin/choano_chambr/corrected-full'
    resolution = [0.015, 0.015, 0.015]
    ds_name = 'choanocyte-chamber'
    add_cell(path, ds_name, resolution)


if __name__ == '__main__':
    # add_cell1()
    # add_cell3()
    add_chamber_raw()

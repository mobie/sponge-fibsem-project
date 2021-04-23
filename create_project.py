import os

# new spec
# from mobie import add_image

# old spec
from mobie import initialize_dataset


def add_cell(path, ds_name):
    scale_factors = 5 * [[2, 2, 2]]
    resolution = [0.015, 0.015, 0.015]
    chunks = [64, 64, 64]
    root = '/g/emcf/pape/sponge-fibsem-project/data'

    # new spec
    # add_image(path, '*.tif', root=root, dataset_name=ds_name,
    #           image_name='raw', resolution=resolution, scale_factors=scale_factors,
    #           menu_name='fibsem', target='local', chunks=chunks, max_jobs=16)

    # old spec
    initialize_dataset(path, '*.tif', root=root, dataset_name=ds_name,
                       raw_name='fibsem-raw', resolution=resolution,
                       scale_factors=scale_factors,
                       target='local', chunks=chunks, max_jobs=24)


def add_cell1():
    path = os.path.join('/g/emcf/ronchi/Arendt-Jake/Arendt_sponge_19-11-27/FIBSEM',
                        'jake_19-12-11_spongilla77-5/processing/aligned_cropped_cell1')
    add_cell(path, 'cell1')


def add_cell3():
    path = os.path.join('/g/emcf/ronchi/Arendt-Jake/Arendt_sponge_19-11-27/FIBSEM',
                        'jake_19-12-13_spongilla77-5_cell3/processing/aligned_cropped_cell3')
    add_cell(path, 'cell3')


# TODO add segmentation volume
# Is this one of the cells above? Or is it a different one.
def add_seg():
    path = '/g/kreshuk/data/arendt/sponge/data.n5'
    key_raw = 'volumes/raw'
    # TODO is this the correct segmentation ?
    key_seg = 'volumes/segmentation/painera_merged'


if __name__ == '__main__':
    # add_cell1()
    add_cell3()

import os
from glob import glob

import napari
import z5py
from tifffile import memmap


def check_input(path):
    files = glob(os.path.join(path, '*.tif'))
    files.sort()
    im_shape = memmap(files[0], mode='r').shape
    for ff in files[1:]:
        this_shape = memmap(ff, mode='r').shape
        if im_shape != this_shape:
            print("Shapes don't match for", ff)
            print(im_shape, this_shape)
            assert False
    shape = (len(files),) + im_shape
    print(shape)


def check_seg():
    path = '/g/kreshuk/data/arendt/sponge/data.n5'
    key_raw = 'volumes/raw/s0'
    key_seg = 'volumes/segmentation/painera_merged'
    with z5py.File(path, 'r') as f:
        shape = f[key_raw].shape
        print(shape)
        shape = f[key_seg].shape
        print(shape)


def check_shapes():
    path1 = os.path.join('/g/emcf/schwab/For Constantin/aligned_cropped_cell1')
    check_input(path1)

    path3 = os.path.join('/g/emcf/schwab/For Constantin/aligned_cropped_cell3')
    check_input(path3)

    check_seg()


def find_roi():
    path = '/g/kreshuk/data/arendt/sponge/data.n5'
    key = 'volumes/raw/s3'

    with z5py.File(path, 'r') as f:
        ds = f[key]
        ds.n_threads = 8
        raw = ds[:]

    with napari.gui_qt():
        viewer = napari.Viewer()
        viewer.add_image(raw)


def check_chamber():
    roi_center = [193, 350, 275]
    roi_center = [8 * ce for ce in roi_center]
    halo = [50, 512, 512]

    path = '/g/kreshuk/data/arendt/sponge/data.n5'
    key = 'volumes/raw/s0'

    f = z5py.File(path, 'r')
    ds = f[key]
    ds.n_threads = 8
    shape = ds.shape

    bb = tuple(
        slice(
            max(ce - ha, 0),
            min(ce + ha, sh)
        )
        for ce, ha, sh in zip(roi_center, halo, shape)
    )
    raw = ds[bb]

    path = '/g/kreshuk/data/arendt/sponge/data.n5'
    seg_keys = [
        'volumes/segmentation/painera_final',
        'volumes/predictions/masks/cells',
        'volumes/predictions/masks/nuclei',
        'volumes/predictions/masks/flagella',
        'volumes/predictions/masks/microvillae',
        'volumes/segmentation/painera_postprocessed'
    ]

    segs = []
    for seg_key in seg_keys:
        ds = f[seg_key]
        ds.n_threads = 8
        segs.append(ds[bb])

    with napari.gui_qt():
        viewer = napari.Viewer()
        viewer.add_image(raw)
        for seg, key in zip(segs, seg_keys):
            name = key.split('/')[-1]
            viewer.add_labels(seg, name=name)


if __name__ == '__main__':
    check_chamber()

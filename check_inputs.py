import os
from glob import glob
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


if __name__ == '__main__':
    path1 = os.path.join('/g/emcf/ronchi/Arendt-Jake/Arendt_sponge_19-11-27/FIBSEM',
                         'jake_19-12-11_spongilla77-5/processing/aligned_cropped_cell1')
    check_input(path1)

    path3 = os.path.join('/g/emcf/ronchi/Arendt-Jake/Arendt_sponge_19-11-27/FIBSEM',
                         'jake_19-12-13_spongilla77-5_cell3/processing/aligned_cropped_cell3')
    check_input(path3)

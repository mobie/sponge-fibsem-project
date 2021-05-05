import numpy as np
from elf.io import open_file
from elf.transformation import matrix_to_parameters
from elf.transformation.affine import affine_matrix_3d
from pybdv import make_bdv

#
# transform amira to bdv registration for the xray data, not working properly yet
#


# adapted from https://git.embl.de/schorb/bdv_convert/-/blob/master/amira2bdv.py
def parse_trafo(trafo_file):
    with open(trafo_file, 'r') as f:
        trafo = f.read().splitlines()

    affine = np.array(
        list(map(float, trafo[0].split(',')))
    )
    affine = affine.reshape((4, 4))
    bbox = np.array(list(map(float, trafo[1].split(','))))
    resolution = np.array(list(map(float, trafo[2].split(','))))
    translation = np.array(list(map(float, trafo[3].split(','))))

    shape = np.array(list(map(
        int, trafo[4].split(',')[0].split(' x ')
    )))

    # assemble the amira transformations, based on
    # https://git.embl.de/schorb/bdv_convert/-/blob/master/amira2bdv.py#L130
    bbox_0 = bbox/np.repeat(resolution, 2)
    bbox_n = bbox_0.copy()
    bbox_n[0] = 0
    bbox_n[1] = bbox_n[1] - bbox_0[0]
    bbox_n[2] = 0
    bbox_n[3] = bbox_n[3] - bbox_0[2]
    bbox_n[4] = 0
    bbox_n[5] = bbox_n[5] - bbox_0[4]

    # translation transformation matrix
    trans = np.array([bbox[1], bbox[3], bbox[5]]) / 2 + translation
    mat_tr = affine_matrix_3d(translation=trans)

    # affine transformation matrix
    mat_aff = affine.T * np.append(resolution, 1)

    # origin transformation matrix
    trans_or = -1. * np.array([[bbox_0[1], bbox_0[4], bbox_0[5]]]) / 2
    mat_or = affine_matrix_3d(translation=trans_or)

    return {
        "transformations": [mat_tr, mat_aff, mat_or],
        "resolution": resolution,
        "shape": shape
    }


def get_fibsem():
    vol_path = '/g/emcf/common/for_constantin/fibsem_cell1'
    trafo = './amira-trafos/00777.tif.am.tform'
    return vol_path, "*.tif", parse_trafo(trafo)


def get_skyscan():
    vol_path = '/g/emcf/common/for_constantin/skyscan'
    trafo = './amira-trafos/20191127_sponge77-5_4_1k_rec00000022.bmp.am.tform'
    return vol_path, "*.bmp", parse_trafo(trafo)


def get_ximg():
    vol_path = '/g/emcf/common/for_constantin/XIMG'
    trafo = './amira-trafos/crop-8bit-invert0000.tif.am.tform'
    return vol_path, "*.tif", parse_trafo(trafo)


def check_volumes():
    import napari

    def _view(p, key, name):
        with open_file(p, 'r') as f:
            raw = f[key]
            raw.n_threads = 16
            raw = raw[:]
        with napari.gui_qt():
            v = napari.Viewer()
            v.add_image(raw)
            v.title = name

    p, key, _ = get_fibsem()
    _view(p, key, 'fibsem')

    p, key, _ = get_skyscan()
    _view(p, key, 'skyscan')

    p, key, _ = get_ximg()
    _view(p, key, 'ximg')


def register_bdv():

    out_file = './amira-trafos/transformed.xml'
    ds_factors = [[2, 2, 2], [2, 2, 2]]

    def _register(p, key, name, setup_id, res, trafos):
        with open_file(p, 'r') as f:
            raw = f[key]
            raw.n_threads = 16
            raw = raw[:]
        affine_trafo = {
            "AmiraTranslation": matrix_to_parameters(trafos[0]),
            "AmiraTransform": matrix_to_parameters(trafos[1]),
            "AmiraOrigin": matrix_to_parameters(trafos[2])
        }
        make_bdv(raw, out_file, downscale_factors=ds_factors,
                 resolution=res, setup_id=setup_id,
                 affine=affine_trafo)

    p, key, trafo = get_fibsem()
    _register(p, key, 'fibsem', 0, trafo["resolution"], trafo["transformations"])

    p, key, _ = get_skyscan()
    _register(p, key, 'skyscan', 1, trafo["resolution"], trafo["transformations"])

    p, key, _ = get_ximg()
    _register(p, key, 'ximg', 2, trafo["resolution"], trafo["transformations"])


if __name__ == '__main__':
    # check_volumes()
    # check_registered()
    register_bdv()

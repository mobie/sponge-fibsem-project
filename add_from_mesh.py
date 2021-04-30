import os
from glob import glob

import numpy as np
from elf.io import open_file
from elf.mesh.mesh_to_segmentation import mesh_to_segmentation
from elf.wrapper import RoiWrapper
from mobie import add_segmentation
from scipy.ndimage import binary_closing


def get_name(ff):
    if 'cilia' in ff or 'cilium' in ff:
        return 'cilia'
    if 'GC' in ff or 'golgi' in ff:
        return 'golgi'
    if 'nucleus' in ff:
        return 'nucleus'
    if 'cell' in ff:
        return 'cell'
    raise ValueError(ff)


def _get_path(ds_name):
    if ds_name == 'cell1':
        p = os.path.join('/g/emcf/ronchi/Arendt-Jake/Arendt_sponge_19-11-27/FIBSEM',
                         'jake_19-12-11_spongilla77-5/processing/visualization/data')
    else:
        p = os.path.join('/g/emcf/ronchi/Arendt-Jake/Arendt_sponge_19-11-27/FIBSEM',
                         'jake_19-12-13_spongilla77-5_cell3/processing/visualization_cell3/data_Cell3_scaled0.5-0.5-1')
    return p


def get_shape(ds_name):
    p = _get_path(ds_name)
    f = open_file(p, mode='r', ext='')
    shape = f['*.tif'].shape
    return shape


def extract_segmentations(ds_name, mesh_folder, resolution):
    out_folder = '/g/emcf/pape/sponge-meshes'
    os.makedirs(out_folder, exist_ok=True)
    out_path = os.path.join(out_folder, f'{ds_name}.n5')
    f_out = open_file(out_path, 'a')

    shape = get_shape(ds_name)

    mesh_files = glob(os.path.join(mesh_folder, '*.obj'))
    mesh_files.sort()
    for ff in mesh_files:
        name = get_name(ff)
        if name in f_out:
            continue
        print("Extracting segmentation from mesh for", name, "@ resolution:", resolution)
        seg = mesh_to_segmentation(ff, resolution, shape=shape,
                                   reverse_coordinates=True, verbose=True)
        f_out.create_dataset(name, data=seg, compression='gzip', chunks=(96,)*3)


def postprocess_seg(path, in_key, out_key, ds_name):
    f = open_file(path, 'a')

    if out_key in f:
        return

    ds = f[in_key]
    ds.n_threads = 8
    seg = ds[:]

    # 1.) map background label
    bg_id = seg[0, 0, 0]
    seg[seg == bg_id] = 0
    dtype = seg.dtype

    # 2.) different post-processing depending on the type of segmentation:
    # 'cell', 'nucleus' -> postprocess so that this is a single object and apply closing
    # 'cilia' -> no further post-processing necessary
    # 'golgi' -> no further post-processing necessary
    if in_key in ('cell', 'nucleus'):
        seg[seg > 0] = 1
        seg = binary_closing(seg, iterations=4).astype(dtype)

    # align with the mobie volume if this is cell1
    if ds_name == 'cell1':
        offset = [777, 70, 211]
        raw_path = '/g/emcf/pape/sponge-fibsem-project/data/cell1/images/local/fibsem-raw.n5'
        with open_file(raw_path, 'r') as f_raw:
            full_shape = f_raw['setup0/timepoint0/s0'].shape
        full_seg = np.zeros(full_shape, dtype=seg.dtype)
        bb = tuple(
            slice(off, off + sh) for off, sh in zip(offset, seg.shape)
        )
        full_seg[bb] = seg
        seg = full_seg

    print(in_key)
    import napari
    with napari.gui_qt():
        viewer = napari.Viewer()
        viewer.add_labels(seg)

    ds = f.require_dataset(out_key, shape=seg.shape, dtype=seg.dtype,
                           compression='gzip', chunks=(96,) * 3)
    ds.n_threads = 8
    ds[:] = seg


def postprocess_segmentations(ds_name):
    path = f'/g/emcf/pape/sponge-meshes/{ds_name}.n5'
    seg_names = list(open_file(path, 'r').keys())
    for name in seg_names:
        if name == 'pp':
            continue
        out_name = 'pp/' + name
        print("Post-process", name, "to", out_name)
        postprocess_seg(path, name, out_name, ds_name)


def add_to_mobie(ds_name):
    root = '/g/emcf/pape/sponge-fibsem-project/data'
    seg_path = f'/g/emcf/pape/sponge-meshes/{ds_name}.n5'

    if ds_name == 'cell1':
        resolution = 3 * [0.008]
    else:
        resolution = [0.008, 0.01, 0.01]
    scale_factors = 4 * [[2, 2, 2]]
    chunks = 3 * (96,)

    mobie_ds_name = 'cell2' if ds_name == 'cell3' else ds_name

    names = list(open_file(seg_path, 'r')['pp'].keys())
    for name in names:
        in_key = 'pp/' + name
        seg_name = f'fibsem-{name}'
        tmp_folder = f'./tmp_{ds_name}_{name}'
        add_segmentation(
            seg_path, in_key, root, mobie_ds_name, seg_name,
            resolution=resolution, scale_factors=scale_factors, chunks=chunks,
            target='local', max_jobs=12, tmp_folder=tmp_folder
        )


def add_seg(ds_name):
    if ds_name == 'cell1':
        mesh_folder = os.path.join('/g/emcf/ronchi/Arendt-Jake/Arendt_sponge_19-11-27/FIBSEM',
                                   'jake_19-12-11_spongilla77-5/processing/visualization/visualization3/cell1_final')
        resolution = [8] * 3
    else:
        mesh_folder = os.path.join('/g/emcf/ronchi/Arendt-Jake/Arendt_sponge_19-11-27/FIBSEM',
                                   'jake_19-12-13_spongilla77-5_cell3/processing/visualization_cell3/cell3_final')
        resolution = [8, 10, 10]

    # extract the segmentations from the mesh files
    extract_segmentations(ds_name, mesh_folder, resolution)

    # align segmentations with the raw volume and postprocess
    postprocess_segmentations(ds_name)

    # add segmentations to the mobie dataset
    add_to_mobie(ds_name)


# cell1: don't align, probably due to cropping mentioned by paolo; need to double check in his mail
# cell3: align with a scale factor of [1, 2, 2] -> resolution = (8, 10, 10)
def align_seg(compute_offset):

    points_mobie = [
        [1077, 525],
        [941, 564],
        [848, 1314],
        [467, 959],
        [432, 826],
        [976, 758],
        [1134, 907]
    ]
    points_amira = [
        [1008, 315],
        [875, 350],
        [777, 1103],
        [394, 747],
        [357, 616],
        [908, 547],
        [1064, 695]
    ]

    if compute_offset:
        diff = [
            [mo - am for mo, am in zip(pm, pa)]
            for pm, pa in zip(points_mobie, points_amira)
        ]
        offset = np.array(diff).mean(axis=0)
        offset = np.round(offset).astype('int').tolist()
        offset = [777] + offset
        print(offset)
        return

    ds_name = 'cell1'

    p = _get_path(ds_name)
    with open_file(p, mode='r', ext='') as f:
        ds = f['*.tif']
        shape = ds.shape
        ds.n_threads = 8
        print("Load raw1")
        raw1 = ds[:]
        # raw1 = ResizedVolume(raw1, (raw1.shape[0] // 2, raw1.shape[1], raw1.shape[2]))[:]

    roi = np.s_[777:-223, :, :]
    raw_p = f'/g/emcf/pape/sponge-fibsem-project/data/{ds_name}/images/local/fibsem-raw.n5'
    with open_file(raw_p, 'r') as f:
        ds = f['setup0/timepoint0/s0']
        ds.n_thredas = 8
        ds = RoiWrapper(ds, roi)
        rshape = ds.shape
        print("Load raw2")
        raw2 = ds[:]

    scale_factor = [float(rs) / sh for rs, sh in zip(rshape, shape)]
    print(ds_name)
    print("Seg-shape  :", shape)
    print("Mobie-shape:", rshape)
    print("Factor     :", scale_factor)

    print("Start viewer")
    import napari
    with napari.gui_qt():
        viewer = napari.Viewer()
        viewer.add_image(raw1, name='amira')
        viewer.add_image(raw2, name='mobie')


def check_seg(ds_name, use_halo=False):
    import napari

    p = _get_path(ds_name)
    f = open_file(p, mode='r', ext='')
    ds = f['*.tif']
    ds.n_threads = 8

    if use_halo:
        shape = ds.shape
        halo = [25, 512, 512]
        bb = tuple(
            slice(sh // 2 - ha, sh // 2 + ha) for sh, ha in zip(shape, halo)
        )
    else:
        bb = np.s_[:]

    print("Load raw ...")
    raw = ds[bb]

    segs = {}
    seg_path = f'/g/emcf/pape/sponge-meshes/{ds_name}.n5'
    with open_file(seg_path, 'r') as f:
        names = list(f['pp'].keys())
        for name in names:
            ds = f[name]
            ds.n_threads = 8
            print("Load", name, "...")
            segs[name] = ds[bb]

            ds = f['pp/' + name]
            ds.n_threads = 8
            segs[name + "_postprocessed"] = ds[bb]

    with napari.gui_qt():
        viewer = napari.Viewer()
        viewer.add_image(raw)
        for name, seg in segs.items():
            viewer.add_labels(seg, name=name)


if __name__ == '__main__':

    add_seg('cell1')
    # add_seg('cell3')

    # check_seg('cell1', True)
    # check_seg('cell3', True)

    # align_seg(True)

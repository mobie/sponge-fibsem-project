import json
import os

import luigi
import numpy as np
import pandas as pd
import vigra
import z5py

from cluster_tools.features import RegionFeaturesWorkflow
from cluster_tools.write import WriteLocal
from elf.parallel import greater
from mobie import add_segmentation
from paintera_tools.serialize import serialize_from_commit
from skimage.filters import threshold_otsu


def export_seg(path, key_in, key_seg):
    serialize_from_commit(path, key_in, path, key_seg,
                          tmp_folder='./tmp_serialize_paintera',
                          max_jobs=16, target='local',
                          relabel_output=True)


def compute_class_mapping(path, seg_key):
    class_keys = [
        'volumes/predictions/classes/cells',
        'volumes/predictions/classes/nuclei',
        'volumes/predictions/classes/flagella',
        'volumes/predictions/classes/microvillae'
    ]
    cnames = [key.split('/')[-1] for key in class_keys]
    class_mapping = {}

    with z5py.File(path, 'a') as f:
        chunks = f[seg_key].chunks

        for name, ckey in zip(cnames, class_keys):
            out_key = ckey.replace('classes', 'masks')
            if out_key in f:
                continue
            ds_in = f[ckey]
            ds_out = f.create_dataset(out_key, shape=ds_in.shape,
                                      chunks=ds_in.chunks, dtype='float32',
                                      compression='gzip')
            greater(ds_in, 0, out=ds_out, n_threads=16, verbose=True)

        task = RegionFeaturesWorkflow
        config = task.get_config()['global']
        config['block_shape'] = chunks

        for name, ckey in zip(cnames, class_keys):
            in_key = ckey.replace('classes', 'masks')

            tmp_folder = f'./tmp_features/{name}'
            config_dir = os.path.join(tmp_folder, 'configs')
            os.makedirs(config_dir, exist_ok=True)
            with open(os.path.join(config_dir, 'global.config'), 'w') as f:
                json.dump(config, f)

            tmp_path = os.path.join(tmp_folder, 'data.n5')

            t = task(
                max_jobs=16, target='local',
                tmp_folder=tmp_folder, config_dir=config_dir,
                input_path=path, input_key=in_key,
                labels_path=path, labels_key=seg_key,
                output_path=tmp_path, output_key='features'
            )
            assert luigi.build([t], local_scheduler=True)

            features = z5py.File(tmp_path, 'r')['features'][:, 1]
            class_mapping[name] = features

    cell_thresh = threshold_otsu(class_mapping['cells'])
    is_cell = class_mapping['cells'] > cell_thresh
    nuc_thresh = threshold_otsu(class_mapping['nuclei'])
    is_nucleus = class_mapping['nuclei'] > nuc_thresh
    is_cell = np.logical_or(is_cell, is_nucleus)

    flag_thresh = threshold_otsu(class_mapping['flagella'])
    is_flag = class_mapping['flagella'] > flag_thresh
    micro_thresh = threshold_otsu(class_mapping['microvillae'])
    is_micro = class_mapping['microvillae'] > micro_thresh

    # 'cells', 'flagella', 'microvilli'
    semantic_mapping = np.concatenate(
        [is_cell[:, None], is_flag[:, None], is_micro[:, None]],
        axis=1
    )
    return semantic_mapping


def postprocess_seg(path, key_in, key_out):
    semantic_mapping = compute_class_mapping(path, key_in)
    is_bg = (semantic_mapping.sum(axis=1) == 0)

    node_labels = np.arange(len(is_bg)).astype('uint32')
    node_labels[is_bg] = 0
    node_labels, max_id, mapping = vigra.analysis.relabelConsecutive(
        node_labels, start_label=1, keep_zeros=True
    )

    node_label_key = 'node_labels/postprocessing'
    with z5py.File(path, 'a') as f:
        ds_labels = f.require_dataset(
            node_label_key, shape=node_labels.shape,
            dtype=node_labels.dtype, chunks=node_labels.shape
        )
        ds_labels[:] = node_labels

    task = WriteLocal
    config = task.default_global_config()
    config['block_shape'] = (128,) * 3
    config['chunks'] = (128,) * 3

    tmp_folder = './tmp_write_pp'
    config_dir = os.path.join(tmp_folder, 'configs')
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, 'global.config'), 'w') as f:
        json.dump(config, f)

    t = task(tmp_folder=tmp_folder, config_dir=config_dir, max_jobs=16,
             input_path=path, input_key=key_in,
             output_path=path, output_key=key_out,
             assignment_path=path, assignment_key=node_label_key,
             identifier='pp')
    assert luigi.build([t], local_scheduler=True)

    new_semantic_mapping = np.zeros(
        (max_id + 1, 3), dtype='uint8'
    )
    for ii in range(len(semantic_mapping)):
        new_id = mapping.get(ii, 0)
        if new_id == 0:
            continue
        new_semantic_mapping[new_id, :] = semantic_mapping[ii, :]
    return new_semantic_mapping


def add_to_mobie(path, key_seg, ds_name, resolution):
    scale_factors = 5 * [[2, 2, 2]]
    chunks = [96, 96, 96]
    root = '/g/emcf/pape/sponge-fibsem-project/data'
    name = 'fibsem-segmentation'
    add_segmentation(path, key_seg,
                     root=root, dataset_name=ds_name,
                     segmentation_name=name,
                     resolution=resolution, chunks=chunks,
                     scale_factors=scale_factors,
                     target='local', max_jobs=16)


def update_table(semantic_mapping):
    table_path = os.path.join('/g/emcf/pape/sponge-fibsem-project/data',
                              'choanocyte-chamber/tables/fibsem-segmentation/default.csv')
    table = pd.read_csv(table_path, sep='\t')
    assert len(table) == len(semantic_mapping), f"{len(table)}, {len(semantic_mapping)}"

    table['cell'] = semantic_mapping[:, 0]
    table['cilium'] = semantic_mapping[:, 1]
    table['microvillus'] = semantic_mapping[:, 2]

    table.to_csv(table_path, sep='\t', index=False)


def add_seg():
    path = '/g/kreshuk/data/arendt/sponge/data.n5'
    ds_name = 'choanocyte-chamber'
    resolution = [0.015, 0.015, 0.015]

    key_in = 'volumes/paintera/corrected_francesca_v1'
    key_seg = 'volumes/segmentation/painera_final'
    key_pp = 'volumes/segmentation/painera_postprocessed'

    # export_seg(path, key_in, key_seg)
    semantic_mapping = postprocess_seg(path, key_seg, key_pp)
    add_to_mobie(path, key_pp, ds_name, resolution)
    update_table(semantic_mapping)


if __name__ == '__main__':
    add_seg()

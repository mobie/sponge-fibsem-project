import os
from concurrent import futures

import imageio
import nifty.tools as nt
import z5py
from tqdm import tqdm


def export_tifs():
    path = '/g/kreshuk/data/arendt/sponge/data.n5'
    out_folder = '/g/emcf/pape/for-yannick/raw'
    os.makedirs(out_folder, exist_ok=True)

    with z5py.File(path, 'r') as f:
        ds = f['volumes/raw/s0']
        zshape = ds.chunks[0]
        blocks = nt.blocking([0], [ds.shape[0]], [zshape])

        def write_chunk(chunk_id):
            block = blocks.getBlock(chunk_id)
            z0, z1 = block.begin[0], block.end[0]

            images = ds[z0:z1]
            for ii, z in enumerate(range(z0, z1)):
                out_path = os.path.join(
                    out_folder, '%05i.tif' % z
                )
                imageio.imwrite(
                    out_path, images[ii]
                )

        with futures.ThreadPoolExecutor(8) as tp:
            list(tqdm(
                tp.map(write_chunk, range(blocks.numberOfBlocks)),
                total=blocks.numberOfBlocks
            ))


if __name__ == '__main__':
    export_tifs()

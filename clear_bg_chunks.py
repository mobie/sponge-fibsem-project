from concurrent import futures
import nifty.tools as nt
import numpy as np
import z5py
from tqdm import tqdm


def clear_dataset(ds):
    chunks = ds.chunks
    blocking = nt.blocking([0, 0, 0], ds.shape, chunks)

    def clear_chunk(block_id):
        block = blocking.getBlock(block_id)
        chunk_id = tuple(beg // ch for beg, ch in zip(block.begin, chunks))
        chunk_vals = np.unique(ds.read_chunk(chunk_id))
        if len(chunk_vals) == 1 and chunk_vals[0] == 255:
            bb = tuple(slice(beg, end) for beg, end in zip(block.begin, block.end))
            ds[bb] = 0

    with futures.ThreadPoolExecutor(16) as tp:
        list(tqdm(
            tp.map(clear_chunk, range(blocking.numberOfBlocks)),
            total=blocking.numberOfBlocks
        ))


def clear_mip(ds_name):
    path = f'/g/emcf/pape/sponge-fibsem-project/data/{ds_name}/images/local/fibsem-raw.n5'
    f = z5py.File(path, 'a')
    g = f['setup0/timepoint0']
    for scale, ds in g.items():
        print("Clearing scale", scale)
        clear_dataset(ds)


def count_chunks(ds_name, scale):
    path = f'/g/emcf/pape/sponge-fibsem-project/data/{ds_name}/images/local/fibsem-raw.n5'
    f = z5py.File(path, 'a')
    ds = f[f'setup0/timepoint0/{scale}']

    chunks = ds.chunks
    blocking = nt.blocking([0, 0, 0], ds.shape, chunks)

    def check_chunk(block_id):
        block = blocking.getBlock(block_id)
        chunk_id = tuple(beg // ch for beg, ch in zip(block.begin, chunks))
        return int(ds.chunk_exists(chunk_id))

    with futures.ThreadPoolExecutor(16) as tp:
        chunk_sum = list(tqdm(
            tp.map(check_chunk, range(blocking.numberOfBlocks)),
            total=blocking.numberOfBlocks
        ))

    n_chunks = sum(chunk_sum)
    print("Number of chunks:", n_chunks)


def find_bg_val():
    path = '/g/emcf/pape/sponge-fibsem-project/data/choanocyte-chamber/images/local/fibsem-raw.n5'
    key = 'setup0/timepoint0/s0'
    f = z5py.File(path, 'r')
    ds = f[key]

    data = ds[:64, :64, :64]
    print(np.unique(data))


if __name__ == '__main__':
    # find_bg_val()

    # count_chunks('cell3', 's1')
    # clear_mip('cell3')
    # count_chunks('cell3', 's1')

    clear_mip('choanocyte-chamber')

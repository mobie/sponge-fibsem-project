import os
import mobie


def add_source_description(ds_folder):
    meta = mobie.metadata.read_dataset_metadata(ds_folder)
    sources = meta["sources"]
    new_sources = {}

    for source_name, source in sources.items():
        kind = source_name.split("-")[-1]
        if kind == "raw":
            description = "FIBSEM data of partial choanocyte data"
            source_type = "image"
        elif kind == "segmentation":
            description = "Automatic segmentation of all cells, cilia and flagella"
            source_type = "segmentation"
        else:
            description = f"Amira segmentation of {kind}"
            source_type = "segmentation"
        source[source_type]["description"] = description
        new_sources[source_name] = source

    meta["sources"] = new_sources
    mobie.metadata.write_dataset_metadata(ds_folder, meta)


def add_view_description(ds_folder):
    meta = mobie.metadata.read_dataset_metadata(ds_folder)
    views = meta["views"]
    sources = meta["sources"]

    new_views = {}
    for name, view in views.items():
        if name in sources:
            source = sources[name]
            desc = source[list(source.keys())[0]]["description"]
        elif name == "default":
            desc = "The default view for this dataset."
        else:
            desc = f"The view corresponding to {name}."
        view["description"] = desc
        new_views[name] = view

    meta["views"] = new_views
    mobie.metadata.write_dataset_metadata(ds_folder, meta)


def add_all_descriptions():
    ds_names = mobie.metadata.read_project_metadata("./data")["datasets"]
    for ds in ds_names:
        ds_folder = os.path.join("data", ds)
        add_source_description(ds_folder)
        add_view_description(ds_folder)


if __name__ == '__main__':
    add_all_descriptions()

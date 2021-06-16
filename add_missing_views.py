import os
import mobie


def add_views(ds_folder):
    metadata = mobie.metadata.read_dataset_metadata(ds_folder)
    sources = metadata['sources']
    views = metadata['views']
    for source_name, source in sources.items():
        source_type = list(source.keys())[0]
        if source_type == 'image':
            kwargs = {
                "menu_name": "fibsem"
            }
        else:
            kwargs = {
                "menu_name": "segmentation",
                "tables": ["default.tsv"]
            }
        view = mobie.metadata.get_default_view(
            source_type, source_name, **kwargs
        )
        views[source_name] = view
    metadata['views'] = views
    mobie.metadata.write_dataset_metadata(ds_folder, metadata)


def add_all_views():
    datasets = mobie.metadata.read_project_metadata('./data')['datasets']
    for ds in datasets:
        ds_folder = os.path.join('./data', ds)
        add_views(ds_folder)


add_all_views()

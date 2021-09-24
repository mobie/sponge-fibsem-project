import mobie

ds_folder = "./data/cell1"
ds_meta = mobie.metadata.read_dataset_metadata(ds_folder)

display_names = ["raw", "segmentations"]
source_types = ["image", "segmentation"]
sources = [["fibsem-raw"], ["fibsem-nucleus", "fibsem-golgi", "fibsem-cilia"]]
display_settings = [{}, {}]

view = mobie.metadata.get_view(display_names, source_types, sources, display_settings,
                               is_exclusive=True, menu_name="bookmarks")
views = ds_meta["views"]
views["organelle-segmentations"] = view
ds_meta["views"] = views
mobie.metadata.write_dataset_metadata(ds_folder, ds_meta)

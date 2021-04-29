from mobie.metadata import add_remote_project_metadata


def prepare_upload():
    bucket_name = 'sponge-fibsem'
    service_endpoint = 'https://s3.embl.de'
    authentication = 'Anonymous'
    add_remote_project_metadata(
        'data', bucket_name,
        service_endpoint=service_endpoint,
        authentication=authentication
    )


if __name__ == '__main__':
    prepare_upload()

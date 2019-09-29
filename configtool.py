import configparser


def read(name: str, **options):
    config = configparser.ConfigParser()
    try:
        if not config.read(f"{name}.conf"):
            raise configparser.Error
        return config, True
    except configparser.Error:
        # TODO : just generate the file and put defaults there
        config.read_dict({name: options})
        return config, False

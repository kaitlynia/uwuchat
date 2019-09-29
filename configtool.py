import configparser


def read(name: str, **options):
    config = configparser.ConfigParser()
    try:
        if not config.read(f"{name}.conf"):
            raise configparser.Error
        return config, True
    except configparser.Error:
        config.read_dict({name: options})
        return config, False

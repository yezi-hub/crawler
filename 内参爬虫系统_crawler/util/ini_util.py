import configparser

class IniReader:
    def __init__(self, file_path):
        self.config = configparser.ConfigParser()
        self.config.read(file_path)

    def get_value(self, section_name, option_name, default=None):
        try:
            return self.config.get(section_name, option_name)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def get_int(self, section_name, option_name, default=None):
        try:
            return self.config.getint(section_name, option_name)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def get_float(self, section_name, option_name, default=None):
        try:
            return self.config.getfloat(section_name, option_name)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def get_boolean(self, section_name, option_name, default=None):
        try:
            return self.config.getboolean(section_name, option_name)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

if __name__=="__main__":
    from config.proj_vars import ini_file_path

    ini_parser = IniReader(ini_file_path)
    database = ini_parser.get_value("database","database")
    print(database)
    port = ini_parser.get_int("database","port")
    print(port)
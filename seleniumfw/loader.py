import importlib.util

class Loader:
    def load_module_from_path(self, path):
        spec = importlib.util.spec_from_file_location("module.name", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
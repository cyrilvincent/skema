import json
import pickle
import jsonpickle
import logging


def load(path):
    """
    Intelligent loading data from pickle and json
    :param path: db file path
    :return: the pickle object
    """
    ext = path.split(".")[-1]
    logging.info(f"Load {path}")
    try:
        if ext == "pickle":
            with open(path, "rb") as f:
                db = pickle.load(f)
        elif ext == "json":
            with open(path) as f:
                db = json.load(f)
        else:
            logging.fatal(f"cyrilload.load: Unknown extension {ext} in {path}")
            raise ValueError(f"Unknown extension {ext}")
    except Exception as ex:
        logging.fatal(f"cyril.load: {ex}")
    return db


def save(db, name, prefix="", method="pickle", indent=4):
    """
    Intelligent data save
    :param db: The object to save
    :param name: File name without extension
    :param prefix: extension prefix file.prefix.extension
    :param method: pickle | jsonpickle | json | pretty (pretty json)
    :param indent: None for no indent
    """
    if prefix != "":
        name += f".{prefix}"
    if method == "pickle":
        name += ".pickle"
    elif method == "json" or method == "jsonpickle":
        name += ".json"
    elif method == "pretty":
        name += ".pretty.json"
    else:
        logging.fatal(f"cyrilload.save: Unknown method {method}")
        raise ValueError(f"Unknown method {method}")
    print(f"Save {name}")
    try:
        if method == "pickle":
            with open(name, "wb") as f:
                pickle.dump(db, f)
        else:
            with open(name, "w") as f:
                if method == "json" or method == "pretty":
                    try:
                        json.dump(db, f, indent=indent if method == "pretty" else None)
                    except TypeError:
                        logging.warning("Can't save to json, switch to jsonpickle")
                        s = jsonpickle.dumps(db, unpicklable=False, indent=indent if method == "pretty" else None)
                        f.write(s)
                else:
                    s = jsonpickle.dumps(db, unpicklable=False, indent=indent)
                    f.write(s)
    except Exception as ex:
        logging.fatal(f"cyrilload.save: {ex}")
        raise ex


def convert(path, prefix="converted", method="json", indent=None):
    db = load(path)
    ext = path.split["."][-1]
    path = path[:-(len(ext)+1)]
    save(db, path, prefix, method, indent)

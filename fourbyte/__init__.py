from multiprocessing import Pool

from requests import get


def get_function_names(func_list: list) -> list:
    """ Print and return the function signatures with the names. """
    func_names = {}

    # Iterate over functions.
    args = []
    for func in func_list:
        args.append(f"https://raw.githubusercontent.com/ethereum-lists/4bytes/master/signatures/{func[0][2:]}")

    # Get function names.
    func_names = {}
    with Pool(len(args)) as p:
        map_res = p.map(get, args)
        for i in range(len(map_res)):
            res = map_res[i]
            func_names[func_list[i][0]] = res.text

    print("")
    print("┳ PUBLIC FUNCTIONS")

    # Print.
    for func in func_list:
        print(f"┣ {func[0]} : {func_names[func[0]]}")

    return func_names

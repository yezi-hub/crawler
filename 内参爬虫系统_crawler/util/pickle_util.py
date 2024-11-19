import pickle

def pickle_dump_dicts(url_dict1,url_dict2):
    with open('my_set.pkl', 'wb') as f:
        pickle.dump(url_dict1, f)
        pickle.dump(url_dict2, f)


def pickle_load_dicts():
    with open('my_set.pkl', 'rb') as f:
        url_dict1 = pickle.load(f)
        url_dict2 = pickle.load(f)
    return url_dict1,url_dict2

if __name__=="__main__":
    dict1  =   {"abc":"test"}
    dict2  =  {"cde": "test"}
    pickle_dump_dicts(dict1, dict2)
    dict1 ,dict2 = pickle_load_dicts()
    print(dict1 ,dict2)

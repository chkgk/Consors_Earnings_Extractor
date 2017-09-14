import textract
import os
import pprint
import pickle


def readfile(full_file_path):
    content = textract.process(full_file_path, layout=True)
    value = False 

    for line in [l.decode().strip() for l in content.splitlines()]:
        if line.find('KAPITALERTRAG') != -1:
            for element in [ word.replace(',', '.') for word in line.split(' ') if word ]:
                try:
                    value = float(element)
                except ValueError:
                    pass
                
    return value 


def read_directory(path, cached = True):
    cache_file_name = '.div_cache.pkl'

    if not cached and os.path.isfile(cache_file_name):
        os.remove(cache_file_name)

    if os.path.isfile(cache_file_name):
        with open(cache_file_name, 'rb') as f:
            return pickle.load(f)

    dirlist = os.listdir(path)

    all_data = []
    for file in dirlist:
        elements = file.split('_')
        wkn = elements[2][3:]
        dat = elements[3][3:]
        dividend = readfile(path + '/'+ file)

        if dividend:
            all_data.append({'wkn': wkn, 'date': dat, 'dividend': dividend})

    with open(cache_file_name, 'wb') as f:
        pickle.dump(all_data, f, pickle.HIGHEST_PROTOCOL)

    return all_data


path = 'dividenden'

all_data = read_directory(path)
wkn_list = [ element['wkn'] for element in all_data ]
wkn_list = list(set(wkn_list))

wkn_div_list = []
for wkn in wkn_list:
    div_sum = 0;
    for entry in all_data:
        if entry['wkn'] == wkn:
            div_sum += entry['dividend']

    wkn_div_list.append((wkn, round(div_sum,2)))


total = 0
for wkn_tupel in wkn_div_list:
    total += wkn_tupel[1]

print(total)
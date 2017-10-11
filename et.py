import textract
import os
from pprint import pprint
import pickle
from bs4 import BeautifulSoup
from urllib.request import urlopen


def extract_float_from_line(line):
    value = False
    for element in [ word.replace(',', '.') for word in line.split(' ') if word ]:
        try:
            value = float(element)
        except ValueError:
            pass

    return value


def read_ertraege(full_file_path):
    content = textract.process(full_file_path, layout=True)
    lines = [l.decode().strip() for l in content.splitlines() if l]
    stop_pos = 0
    for line in lines:
        if line.find('WERT') != -1:
            stop_pos += 1

        if stop_pos >= 1:
            stop_pos += 1

        if stop_pos == 2:
            stop_pos = 0
            value = extract_float_from_line(line)
            return(value)    


def read_dividende(full_file_path):
    content = textract.process(full_file_path, layout=True)

    for line in [l.decode().strip() for l in content.splitlines()]:
        if line.find('KAPITALERTRAG') != -1:
            return extract_float_from_line(line) 


def read_directory(path_list, cached = True):
    cache_file_name = '.div_cache.pkl'

    if not cached and os.path.isfile(cache_file_name):
        os.remove(cache_file_name)

    if os.path.isfile(cache_file_name):
        with open(cache_file_name, 'rb') as f:
            return pickle.load(f)


    dirlist = []
    for path in path_list:
        dirlist += [ path + '/' + file  for file in os.listdir(path)]

    value = False
    all_data = []

    for path in dirlist:
        p = path.split('/')
        folder = p[0]
        filename = p[1]
        elements = filename.split('_')
        #print(elements)
        wkn = elements[2][3:]
        dat = elements[3][3:]

        #print(elements)
        #print(path)

        if elements[0] == 'ERTRAGSGUTSCHRIFT':
            value = read_ertraege(path)
            value_type = 'earnings'
        elif elements[0] == 'DIVIDENDENGUTSCHRIFT':
            value = read_dividende(path)
            value_type = 'dividend'

        if value:
            all_data.append({'wkn': wkn, 'date': dat, 'value': value, 'type': value_type})

    with open(cache_file_name, 'wb') as f:
        pickle.dump(all_data, f, pickle.HIGHEST_PROTOCOL)

    return all_data


def sum_by_wkn(all_data, start_date = 0, end_date = 30000000):
    wkn_list = [ element['wkn'] for element in all_data ]
    wkn_list = list(set(wkn_list))

    wkn_sum_list = []
    for wkn in wkn_list:
        wkn_sum = 0;
        for entry in all_data:
            if entry['wkn'] == wkn and int(entry['date']) >= start_date and int(entry['date']) < end_date:
                wkn_sum += entry['value']

        if wkn_sum:
            wkn_sum_list.append((wkn, round(wkn_sum,2)))

    return wkn_sum_list
    

def get_total(wkn_sum_list):
    total = 0
    for wkn_tupel in wkn_sum_list:
        total += wkn_tupel[1]

    return round(total, 2)

def lookup_name(wkn, cached = True):

    cache_file_name = '.name_cache.pkl'

    if not cached and os.path.isfile(cache_file_name):
        os.remove(cache_file_name)

    wkn_names = []
    if os.path.isfile(cache_file_name):
        with open(cache_file_name, 'rb') as f:
            wkn_names = pickle.load(f)

    # print(wkn_names)

    # {'wkn': , 'name': }

    name = ''
    for e in wkn_names:
        if e['wkn'] == wkn:
            name = e['name']
            # print(wkn, 'found')

    if name == '':
        start_url = "http://www.ariva.de/"+wkn
        page_source = urlopen(start_url).read()
        soup = BeautifulSoup(page_source, "html.parser")

        snapshot_div = soup.findAll("div", { "class" : "snapshotName" })
        name = str(snapshot_div[0].h1.span.string)

        wkn_names.append({'wkn': wkn, 'name': name})
        # print(wkn_names)

    if cached:
        with open(cache_file_name, 'wb') as f:
            pickle.dump(wkn_names, f)

    return name


def add_names(wkn_sum_list):
    ret_list = []
    for wkn, summe in wkn_sum_list:
        name = lookup_name(str(wkn))
        ret_list.append((wkn, name, summe))
    return ret_list


# main part
data = read_directory(['dividenden', 'ertraege'])
# pprint.pprint(data)
wkn_sum_list = sum_by_wkn(data, start_date=20170000) # add start_date, end_date
# pprint(wkn_sum_list)
named_list = add_names(wkn_sum_list)

pprint(named_list)
pprint(get_total(wkn_sum_list))


# could implement Name lookup per wkn:
# call www.ariva.de/<wkn> for details
# i.e. www.ariva.de/851915 for Northrop
# when using curl, follow redirect with -L flag
# i.e. curl -L www.ariva.de/851915 
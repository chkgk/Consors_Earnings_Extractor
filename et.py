import textract
import os
from pprint import pprint
import pickle
from bs4 import BeautifulSoup
from urllib.request import urlopen


class Earnings_Extrator:
    def __init__(self, dir_list, cached = True):
        self.dir_list = dir_list
        self.cached = cached

        self.dir_cache_file_name = '.div_cache.pkl'
        self.wkn_cache_file_name = '.name_cache.pkl'

        self.data = self.read_directories()


    def extract_float_from_line(self, line):
        value = False
        for element in [ word.replace(',', '.') for word in line.split(' ') if word ]:
            try:
                value = float(element)
            except ValueError:
                pass

        return value


    def read_earnings(self, full_file_path):
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
                value = self.extract_float_from_line(line)
                return(value)    


    def read_dividends(self, full_file_path):
        content = textract.process(full_file_path, layout=True)

        for line in [l.decode().strip() for l in content.splitlines()]:
            if line.find('KAPITALERTRAG') != -1:
                return self.extract_float_from_line(line) 


    def read_directories(self):
        if not self.cached and os.path.isfile(self.dir_cache_file_name):
            os.remove(self.dir_cache_file_name)

        if os.path.isfile(self.dir_cache_file_name):
            with open(self.dir_cache_file_name, 'rb') as f:
                return pickle.load(f)


        dirlist = []
        for path in self.dir_list:
            dirlist += [ path + '/' + file  for file in os.listdir(path)]

        value = False
        all_data = []

        for path in self.dir_list:
            p = path.split('/')
            folder = p[0]
            filename = p[1]
            elements = filename.split('_')

            wkn = elements[2][3:]
            dat = elements[3][3:]

            if elements[0] == 'ERTRAGSGUTSCHRIFT':
                value = self.read_earnings(path)
                value_type = 'earnings'
            elif elements[0] == 'DIVIDENDENGUTSCHRIFT':
                value = self.read_dividends(path)
                value_type = 'dividend'

            if value:
                all_data.append({'wkn': wkn, 'date': dat, 'value': value, 'type': value_type})

        with open(self.dir_cache_file_name, 'wb') as f:
            pickle.dump(all_data, f, pickle.HIGHEST_PROTOCOL)

        return all_data


    def sum_by_wkn(self, all_data = None, start_date = 0, end_date = 30000000):
        if all_data == None:
            all_data = self.data

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
        

    def get_total(self, wkn_sum_list):
        total = 0
        for wkn_tupel in wkn_sum_list:
            total += wkn_tupel[1]

        return round(total, 2)


    def lookup_name(self, wkn):
        if not self.cached and os.path.isfile(self.wkn_cache_file_name):
            os.remove(self.wkn_cache_file_name)

        wkn_names = []
        if os.path.isfile(self.wkn_cache_file_name):
            with open(self.wkn_cache_file_name, 'rb') as f:
                wkn_names = pickle.load(f)

        name = ''
        for e in wkn_names:
            if e['wkn'] == wkn:
                name = e['name']

        if name == '':
            start_url = "http://www.ariva.de/"+wkn
            page_source = urlopen(start_url).read()
            soup = BeautifulSoup(page_source, "html.parser")

            snapshot_div = soup.findAll("div", { "class" : "snapshotName" })
            name = str(snapshot_div[0].h1.span.string)

            wkn_names.append({'wkn': wkn, 'name': name})

        if self.cached:
            with open(self.wkn_cache_file_name, 'wb') as f:
                pickle.dump(wkn_names, f)

        return name


    def add_names(self, wkn_sum_list):
        ret_list = []
        for wkn, summe in wkn_sum_list:
            name = self.lookup_name(str(wkn))
            ret_list.append((wkn, name, summe))
        return ret_list


    def get_named_totals(self):
        wkn_sum_list = self.sum_by_wkn()
        return self.add_names(wkn_sum_list)




if __name__ == '__main__':
    ex = Earnings_Extrator(['dividenden', 'ertraege'])
    named_totals = ex.get_named_totals()
    pprint(named_totals)

import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime
import time
import os
import glob
import json

class KijijiScrapper:

    #creating page number base URLs
    def __init__(self,
                 #location coordinates for SFU
                 location=(49.278094,-122.919883),
                 radius=4.0):

        user_input = input('Do you want to search for rentals near SFU? (Yes/No)')
        pageNos = '/page-'
        self.info={}
        self.final_url=[]
        self.kijiji_rentals_url = []
        self.date = datetime.date.today()
        self.current_directory = os.getcwd()

        if user_input.lower().strip() == 'yes':
            self.base_url = 'https://www.kijiji.ca'
            category = '/b-for-rent/'

            for i in range(1,4):
                print("Adding page {} to web scraping list".format(str(i)))
                address = 'burnaby-new-westminster'+pageNos+str(i)+'/c30349001l1700286?address=' \
                               'Simon%20Fraser%20University%2C%20University%20Dr%2C%20Burnaby%2C%20BC'
                coordinates= '&ll={}%2C{}'.format(location[0],location[1])
                radius_input = input('The default search radius is 4km. Do you want to change the search'
                                     ' radius? (Yes/No)?')
                if radius_input.lower().strip() == 'yes':
                    radius = float(input('Enter new radius (kms)'))
                radius= '&radius={}'.format(radius)
                self.final_url.append(self.base_url+category+address+coordinates+radius)

        else:
            self.final_url.append(input('Go to Kijiji.ca and get the relevant URL of the webpage you want '
                                        'to scrape.Paste this URL in the command prompt'))



    #extracts all rental ad listings for each page
    def find_rental_urls(self, pageURL):
        response = requests.get(pageURL)
        soup = BeautifulSoup(response.text,"html.parser")

        # find all rental listings
        for link in soup.findAll("a", {"class": "title"}):
            self.kijiji_rentals_url.append(self.base_url+link.get('href'))

    #for each rental ad listing, extract all info and save in dataframe
    def get_all_info(self,df=pd.DataFrame()):
        iterator = df[0]
        self.final_results = pd.DataFrame()

        if len(df)==0:
            iterator = self.kijiji_rentals_url[:1]

        for rental_item in iterator:
            print(rental_item)
            response = requests.get(rental_item)
            soup = BeautifulSoup(response.text, "html.parser")
            try:
                self.info["Title"] = soup.find('h1', {"class": "title-2323565163"}).text
            except:
                self.info["Title"] = None

            try:
                self.info["Location"] = soup.find('span', {"class": "address-3617944557"}).text
            except:
                self.info["Location"] = None

            self.info["Url"] = rental_item

            try:
                self.info['House Type'] = soup.find_all('span',{'class':'noLabelValue-3861810455'})[0].text
            except:
                self.info['House Type'] = None

            try:
                self.info['Bedrooms'] = soup.find_all('span',{'class':'noLabelValue-3861810455'})[1]
            except:
                self.info['Bedrooms'] = None

            try:
                self.info['Bedrooms'] = self.info['Bedrooms'].text.split(':')[1].strip()
            except:
                self.info['Bedrooms'] = None

            try:
                self.info['Bathrooms'] = soup.find_all('span',{'class':'noLabelValue-3861810455'})[2]
            except:
                self.info['Bathrooms'] = None

            try:
                self.info['Bathrooms'] = self.info['Bathrooms'].text.split(':')[1].strip()
            except:
                self.info['Bathrooms'] = None

            utilities = soup.find_all('svg', class_=['icon-459822882 yesNoIcon-2594104508',
                                                     'icon-459822882 yesNoIcon-2594104508 yesIcon-3014691322'])
            if len(utilities)>0:
                self.info['Hydro']=utilities[0]['aria-label'].strip(':')[0].strip()
                self.info['Heat']=utilities[1]['aria-label'].strip(':')[0].strip()
                self.info['Water']=utilities[2]['aria-label'].strip(':')[0].strip()
            else:
                self.info['Hydro']=None
                self.info['Heat']=None
                self.info['Water']=None

            try:
                self.info['Wifi and More'] = soup.select('ul.list-1757374920.disablePadding-1318173106')[2].text
            except:
                self.info['Wifi and More'] = None

            try:
                self.info['Price']  = soup.find_all('div',{'class':'priceWrapper-1165431705'})[0].next.text
            except:
                self.info['Price'] = None

            otherInfo = soup.find_all('dd',{'class':'twoLinesValue-2815147826'})
            for elem in otherInfo:
                if elem.previous == 'Agreement Type':
                    self.info['Agreement Type'] = elem.text
                if elem.previous == 'Size (sqft)':
                    self.info['Size (sqft)'] = elem.text
                if elem.previous == 'Furnished':
                    self.info['Furnished'] = elem.text
                if elem.previous == 'Air Conditioning':
                    self.info['Air Conditioning'] = elem.text

            temp=pd.DataFrame([self.info])
            self.final_results = pd.concat([self.final_results,temp],axis=0)
            time.sleep(20)  # Sleep for 20 seconds

        self.final_results.to_excel(self.current_directory+'/Final Results/Final Results {}.xlsx'.format(self.date),index=False)



    def save_rental_urls(self):

        # find all rental listings from each pg number URL
        for pageURL in self.final_url:
            self.find_rental_urls(pageURL)
        df = pd.DataFrame(self.kijiji_rentals_url)

        #excluding office spaces
        df = df[~df[0].str.contains("v-commercial-office-space")]

        df.to_excel('Rental Listings {}.xlsx'.format(self.date), index=False)

    def get_lat_long(self,location):

        URL = "https://geocode.search.hereapi.com/v1/geocode"
        PARAMS = {'apiKey': os.getenv("API_KEY"), 'q': location}

        # sending get request and saving the response as response object
        r = requests.get(url=URL, params=PARAMS)
        data = r.json()

        latitude = data['items'][0]['position']['lat']
        longitude = data['items'][0]['position']['lng']

        return str(latitude) + ',' + str(longitude)



    def get_transit_time(self,origin):

        base_url = 'https://transit.router.hereapi.com/v8/routes'
        params = {'apiKey': os.getenv("API_KEY"),
                  'origin': self.get_lat_long(origin),
                  'destination': self.get_lat_long("Simon Fraser University, 8888 University Dr, Burnaby, BC V5A 1S6, Canada"),
                  'arrivalTime': '2022-07-18T08:00:00',
                  'changes': 2,
                  'return': 'travelSummary'}

        r = requests.get(url=base_url, params=params)

        pretty_json = json.loads(r.text)
        json_length = len(pretty_json['routes'][0]['sections'])
        transit_time = 0

        for i in range(json_length):

            transit_time+= pretty_json['routes'][0]['sections'][i]['travelSummary']['duration']

        return transit_time/60 #transit time in mins

    def add_transit_to_rentals(self):

        #read latest SFU rentals file
        list_of_files = glob.glob(self.current_directory + '/Final Results/*.xlsx')  # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        self.final_results = pd.read_excel(latest_file, engine='openpyxl')

        transit_array=[]

        for loc in self.final_results['Location']:
            transit_array.append(self.get_transit_time(loc))

        self.final_results['Transit Time(mins)'] = transit_array
        self.final_results.sort_values(by=["Price","Hydro",'Heat',"Water","Transit Time(mins)",
                                           "Furnished","Air Conditioning"],
                                            ascending=[True,True,True,True,True,True,True],
                                            inplace=True)

        self.final_results.to_excel(self.current_directory+'/Final Results/Final Results {}.xlsx'.format(self.date),index=False)


class TestDrive:

    def __init__(self):

        kijiji = KijijiScrapper()

        #run it once to save it in excel
        kijiji.save_rental_urls()

        # read directly from rental excel to avoid hits on kijiji server
        list_of_files = glob.glob(self.current_directory+'/*.xlsx')  # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        rental_urls = pd.read_excel(latest_file,engine='openpyxl') #read all suitable rental urls

        #read each rental and extract all info
        #run once and save results to "Final Results" excel
        kijiji.get_all_info(rental_urls)

        #calculate distance of each rental from SFU
        kijiji.add_transit_to_rentals()

        #read directly from final results excel to avoid hits on kijiji server
        list_of_files = glob.glob(kijiji.current_directory + '/Final Results/*.xlsx')  # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        sfu_rentals = pd.read_excel(latest_file, engine='openpyxl')

        print(sfu_rentals.head())



if __name__ == "__main__":
    TestDrive()



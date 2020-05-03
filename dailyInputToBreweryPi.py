# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 17:39:01 2020

@author: james
"""

# daily transfer from Tank Status to BreweryPi

# import necessary modules
import MySQLdb
from datetime import date, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd


# connect to db and establish cursor
db = MySQLdb.connect(user=<USER>,
                     passwd=<PASSWORD>,
                     host=<HOST>,
                     db="BreweryPi"
                     )
cursor = db.cursor()


# prepare DataFrame from tank status
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('C:/Users/james/brewerypi/frustrator_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open('Gilgamesh Tank Status').get_worksheet(9)
data = sheet.get_all_records()

df = pd.DataFrame(data)


# use yesterday's date to filter the newest data
df['Date'] = pd.to_datetime(df.Date)

today = date.today()
yesterday = today - timedelta(days=1)
ydate = yesterday.strftime('%m/%d/%Y')
df = df[df['Date'] == ydate]
df['Date'] = df.Date + timedelta(hours = 9)



# prepare empty values for pass
df.replace('', 'blank', inplace=True)


# prepare tag values
df['gravityTag'] = df.Tank + '_Plato'
df['volumeTag'] = df.Tank + '_EstimatedVolume'
df['temperatureTag'] = df.Tank + '_Temperature'
df['brandTag'] = df.Tank + '_Brand'
df['stateTag'] = df.Tank + '_State'


# map tags
mapQuery = 'SELECT * FROM Tag'
execution = cursor.execute(mapQuery)
mapMaster = list(cursor.fetchall())

mapTags = {i[4]:i[0] for i in mapMaster}

df['temperatureTagId'] = df.temperatureTag.map(mapTags)
df['brandTagId'] = df.brandTag.map(mapTags)
df['stateTagId'] = df.stateTag.map(mapTags)
df['gravityTagId'] = df.gravityTag.map(mapTags)
df['volumeTagId'] = df.volumeTag.map(mapTags)


# map lookup values (brands and statuses)
lookupValueQuery = 'SELECT * FROM LookupValue'
execution = cursor.execute(lookupValueQuery)
mapLookups = list(cursor.fetchall())

mapBrands = {i[1]:i[-1] for i in mapLookups if i[-2] == 1}
mapStates = {i[1]:i[-1] for i in mapLookups if i[-2] == 2}

df['brandValue'] = df.Brand.map(mapBrands)
df['stateValue'] = df.Status.map(mapStates)

df.reset_index(drop=True, inplace=True)


# prepare submission list
to_submit = []

for i, r in df.iterrows():
    # add gravities
    if r.Gravity == 'blank':
        pass
    else:
        w = (r.gravityTagId, r.Date, 1, r.Gravity)
        to_submit.append(w)
        
    # add temperatures
    if r.Temperature == 'blank':
        pass
    else:
        w = (r.temperatureTagId, r.Date, 1, r.Temperature)
        to_submit.append(w)
        
    # add volumes
    if r.Volume == 'blank':
        pass
    else:
        w = (r.volumeTagId, r.Date, 1, r.Volume)
        to_submit.append(w)
    
    # add brands
    w = (r.brandTagId, r.Date, 1, r.brandValue)
    to_submit.append(w)
    
    # add statuses
    w = (r.stateTagId, r.Date, 1, r.stateValue)
    to_submit.append(w)


# prepare the dynamic query
query = 'INSERT INTO TagValue (TagId, Timestamp, UserId, Value) VALUE (%s, %s, %s, %s)'


# commit the frames
for i in to_submit:
    val = i
    try:
        cursor.execute(query, val)
        
    # avoid duplicates
    except MySQLdb.IntegrityError:
        pass
        print("not submitted:", i)
    db.commit()


# close the connection
db.close()

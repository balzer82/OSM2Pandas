# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <headingcell level=1>

# Read Overpass-API to Python Pandas Dataframe

# <markdowncell>

# The [Overpass API](http://wiki.openstreetmap.org/wiki/Overpass_API) provides access to the data behind the Openstreetmaps Map Data.
# The [Overpass-Turbo](http://overpass-turbo.eu/) is the easyiest way to test requests and get the correct code to ask the database.

# <codecell>

import pandas as pd
import requests
import json
pd.set_option('display.max_columns', 200)

# <markdowncell>

# Gebiet festlegen, am besten mit einer [Bounding Box](http://boundingbox.klokantech.com/)

# <codecell>

# Get yours at: http://boundingbox.klokantech.com/
bbox = [13.526452,50.932114,13.966063,51.17772]

# Links unten
minLat = bbox[1]
minLon = bbox[0]

# Rechts oben
maxLat = bbox[3]
maxLon = bbox[2]

# <markdowncell>

# Request from [Overpass-Turbo](http://overpass-api.de/api/convert?data=%3C!--%0AThis%20has%20been%20generated%20by%20the%20overpass-turbo%20wizard.%0AThe%20original%20search%20was%3A%0A%E2%80%9CBushaltestelle%E2%80%9D%0A--%3E%0A%3Cosm-script%20output%3D%22json%22%20timeout%3D%2225%22%3E%0A%20%20%3C!--%20gather%20results%20--%3E%0A%20%20%3Cunion%3E%0A%20%20%20%20%3C!--%20query%20part%20for%3A%20%E2%80%9CBushaltestelle%E2%80%9D%20--%3E%0A%20%20%20%20%3Cquery%20type%3D%22node%22%3E%0A%20%20%20%20%20%20%3Chas-kv%20k%3D%22highway%22%20v%3D%22bus_stop%22%2F%3E%0A%20%20%20%20%20%20%3Cbbox-query%20s%3D%2250.973778188690716%22%20w%3D%2213.552322387695312%22%20n%3D%2251.12033393562918%22%20e%3D%2213.898735046386719%22%2F%3E%0A%20%20%20%20%3C%2Fquery%3E%0A%20%20%3C%2Funion%3E%0A%20%20%3C!--%20print%20results%20--%3E%0A%20%20%3Cprint%20mode%3D%22body%22%2F%3E%0A%20%20%3Crecurse%20type%3D%22down%22%2F%3E%0A%20%20%3Cprint%20mode%3D%22skeleton%22%20order%3D%22quadtile%22%2F%3E%0A%3C%2Fosm-script%3E&target=mapql)

# <codecell>

osmrequest = {'data': '[out:json][timeout:25];(node["highway"="bus_stop"](%s,%s,%s,%s););out body;>;out skel qt;' % (minLat, minLon, maxLat, maxLon)}
osmurl = 'http://overpass-api.de/api/interpreter'

# Ask the API
osm = requests.get(osmurl, params=osmrequest)

# <markdowncell>

# The JSON can't be directyl imported to a Pandas Dataframe:
# 
# ```
# If the JSON string were to be converted to a Python object, it would be a dict whose elements key is a list of dicts. The vast majority of the data is inside this list of dicts.
# 
# This JSON string is not directly convertible to a Pandas object. What would be the index, and what would be the columns? Surely you don't want [u'elements', u'version', u'osm3s', u'generator'] to be the columns, since almost all the information is in the elements list-of-dicts.
# 
# But if you want the DataFrame to consist of the data only in the elements list-of-dicts, then you'd have to specify that, since Pandas can't make that assumption for you.
# 
# Further complicating things is that each dict in elements is a nested dict.
# ```
# 
# Thanks to [unutbu from stackoverflow.com](http://stackoverflow.com/questions/24848416/expected-string-or-unicode-when-reading-json-with-pandas) for fiddling this out!

# <codecell>

osmdata = osm.json()
osmdata = osmdata['elements']
for dct in osmdata:
    for key, val in dct['tags'].iteritems():
        dct[key] = val
    del dct['tags']

# <headingcell level=3>

# Now put everything to the Pandas Dataframe

# <codecell>

osmdf = pd.DataFrame(osmdata)

# <headingcell level=3>

# Look at the whole Dataframe

# <codecell>

osmdf.head(5)

# <headingcell level=3>

# The interesting ones are

# <codecell>

busstopsdf = osmdf[['lat', 'lon', 'name', 'wheelchair']].dropna(subset=['name']).fillna(u'unknown')
busstopsdf.head(5)

# <codecell>

accesslevel = {'unknown': 0, 'yes': 2, 'limited': 1, 'no': -1}
def getacclev(c):
    return accesslevel[c]
busstopsdf['accesslevel'] = busstopsdf.wheelchair.apply(getacclev)

# <codecell>

busstopsdf.head(10)

# <codecell>

busstopsdf[['lat','lon','name','accesslevel','wheelchair']].to_csv('bus_stops.csv', sep=',', encoding='utf-8', index=False)

# <codecell>

print('Done.')

# <headingcell level=3>

# Get Accessability Level for Disabled People

# <codecell>

busstopsdf.wheelchair.unique()

# <codecell>

colorcodes = {'unknown': '#FFFFFF', 'yes': '#00FF00', 'limited': '#FFFF00', 'no': '#FF0000'}
def colorencode(c):
    return colorcodes[c]
busstopsdf['color'] = busstopsdf.wheelchair.apply(colorencode)

# <headingcell level=2>

# Generate .html out of it

# <codecell>

from bokeh.plotting import *
output_notebook()

# <codecell>

output_file("bus_stops.html", title="Bus Stops from openstreetmaps.org")

hold()

circle(busstopsdf['lon'], busstopsdf['lat'],
       color=busstopsdf['color'], line_color='black',fill_alpha=0.8,
       size=12, title='Bus Stops in Dresden (from openstreetmaps.org)',
       background_fill= '#cccccc', tools='pan, wheel_zoom, box_zoom, reset')

text(busstopsdf['lon'], busstopsdf['lat']+0.00002,
    text=busstopsdf['name'], angle=0, text_color='#333333',
    text_align="center", text_font_size="10pt")

xaxis().axis_label='Lon'
yaxis().axis_label='Lat'
grid().grid_line_color='white'

show()

# <codecell>



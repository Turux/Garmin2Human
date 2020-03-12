#!/usr/bin/python3
# coding: utf-8

#imports
import pandas as pd
import numpy as np
import gpxpy
import gpxpy.gpx

#Class definitions
class Garmindata:
    def __init__(self,field,value,unit):
        self.field = field
        self.value = value
        self.unit = unit
        
class Garmintime(Garmindata):
    pass

class Garminevent:
    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.readings = list()
    def getNumReadings(self):
        return len(self.readings)
    def getFields(self):
        fields = list()
        for i in self.readings:
            fields.append(i.field)
        return fields
    def addReading(self, garmindata):
        self.readings.append(garmindata)

#Function definitions
def getDataframe(eventlist, wishlist):
    no_wishes=len(wishlist)+1
    output_list=list()
    for event in eventlist:
        f=event.getFields()
        try:
            counter = 1
            for wish in wishlist:
                element = f.index(str(wish))
                if counter == 1:
                    new_row=[0]*no_wishes
                    new_row[0]=int(event.timestamp.value)+631065600
                if wish in ('position_lat', 'position_long'):
                    new_row[counter]=float(event.readings[element].value)*(180/(2**31))
                else:
                    new_row[counter]=float(event.readings[element].value)
                output_list.append(new_row)
                counter = counter+1
        except: 
            ''
    wishlist.insert(0,'timestamp')
    df=pd.DataFrame(output_list,columns=wishlist)
    df['date']=pd.to_datetime(df['timestamp'], unit='s')
    return df

print('Welcome to Garmin2Human converter')
print('Version: alpha1')
print('Please pre-process your .FIT using the ANT+ FIT SKD available at this address: https://www.thisisant.com/resources/fit-sdk-beta/')

path=input('Insert the CSV file location: ')
data = pd.read_csv(path)
print('Imported CSV file at ', path)
new=data.loc[(data.iloc[:,0] =='Data') & (data.iloc[:,2]=='record')]
new=new.iloc[:,3:]
new.index=range(new.shape[0])

print('Starting pre-processing')
print('This may take a while...')

output = list()
for i in range(new.shape[0]):
    for j in range(0,len(new.columns),3):
        if (new.columns[j].find('Field') > -1):
            if pd.isna(new.iloc[i,j]):
                break
            else:
                if new.iloc[i,j] == 'timestamp':
                    t=Garmintime(new.iloc[i,j],new.iloc[i,j+1],new.iloc[i,j+2])
                    e=Garminevent(t)
                else:
                    try:
                        d=Garmindata(new.iloc[i,j],new.iloc[i,j+1],new.iloc[i,j+2])
                        e.addReading(d)
                    except:
                        print('Record missing timestamp')
    output.append(e)
    del(e,t,d)

print('I have read the following number of rows:', len(output))
print('Now building dataframe')
wishlist=['position_lat','position_long','altitude','speed','distance','power','temperature']
print('Current values selected are: ',wishlist)
outputframe=getDataframe(output,wishlist)
output_path=input('Where would you like to save the output? ')
outputframe.to_csv(path_or_buf=output_path, index = False, header=True)

print("Exportin GPX data")
gpx = gpxpy.gpx.GPX()
gpx_track = gpxpy.gpx.GPXTrack()
gpx.tracks.append(gpx_track)
gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)
for idx in outputframe.index:
    gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(outputframe.loc[idx, 'position_lat'], outputframe.loc[idx, 'position_long'], elevation=outputframe.loc[idx, 'altitude']))
output_path=input('Where would you like to save the output? ')
with open(output_path, 'w') as f:
    f.write(gpx.to_xml())
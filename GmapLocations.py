## 2. Resolve locations
import googlemaps
import sys
import time
import datetime

fileLocationLocationsNotToMap='.\\Data\\Geo\\D_LocationBan.txt' # Location
fileLocationLocationsResolved='.\\Data\\Geo\\S_LocationResolved.txt' # Location : address : Postcode : distance
fileLocationLocationsToMap='.\\Data\\Geo\\S_LocationInput.txt' # Location
#fileLocationLocationsToMap='Data/Geo/S_LocationInputShort.txt' # Location             ## TEST
fileLocationLocationsError='Data/Geo/S_LocationError.txt' # Location : Error
mygooglemapskey='AIzaSyA7NBT3S-z3GYgZhY067AkuQbNZSTVhblk'
myarrivaltime=1471943400 # 09:00 on working day
myhome="KT3 3HH"

gmaps = googlemaps.Client(key=mygooglemapskey)
IterationStart = str(datetime.datetime.now().time())

DoNotLocate=set()
with open(fileLocationLocationsNotToMap, 'r') as F:
    for line in F:
        DoNotLocate.add(line.strip().lower())
F.close()

LocationsToCheck=list()
with open(fileLocationLocationsToMap, 'r') as F:
    for line in F:
        LocationsToCheck.append(line.strip().lower())
F.close()

LocationsResolved=dict()
with open(fileLocationLocationsResolved, 'r') as F:
    for line in F:
        fLoc,fAddr,fPostCode,fDistance = line.split(':').lower()
        LocationsResolved[fLoc]=fAddr+':'+fPostCode+':'+fDistance
F.close()


i,delayer=0,0
for x in LocationsToCheck:
    if x in LocationsResolved:
        continue
    try:
        directions_result = gmaps.directions(myhome,x , mode="transit", arrival_time=myarrivaltime, region="uk")
        mn10 = directions_result[0]['legs'][0]['duration']['value']//600 * 10
        ea = directions_result[0]['legs'][0]['end_address']
        elat = directions_result[0]['legs'][0]['end_location']['lat']
        elng = directions_result[0]['legs'][0]['end_location']['lng']
        geocode_result=gmaps.reverse_geocode((elat,elng))
        for zzx in geocode_result:
            for zzl in zzx['types']:
                if zzl=='postal_code_prefix':
                    for zza in zzx['address_components']:
                        for zzat in zza['types']:
                            if zzat=='postal_code_prefix':
                                pc = zza['long_name']
        f=open(fileLocationLocationsResolved,'a')
        f.write(x+':'+ea+':'+pc+':'+str(mn10)+'\n')
        f.close()
    except:
        e = sys.exc_info()[0]
        fe = open(fileLocationLocationsError, 'a')
        fe.write(IterationStart+':'+str(datetime.datetime.now().time())+':'+ x + ':' + str(e)+ '\n')
        fe.close()
    delayer += 1
    i += 1
    if delayer == 5:
        print(str(i)+' > '+x)
        time.sleep(1)
        delayer = 0
print ('end')
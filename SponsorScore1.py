import re
import sys
import json
import googlemaps
import operator
import time

PageHeader="Organisation Name Town/City County Tier & Rating Sub Tier"
PageNumPattern="^Page \d+ of \d+"

fileLocationIn='.\Data\Input\R_SponsorsS.txt'                ## debug                                      # read only
fileLocationIn='.\Data\Input\R_SponsorsTest.txt'             ## test                                       # read only
fileLocationIn='.\Data\Input\R_Sponsors.txt'                 ## real                                       # read only
fileLocationTokens='.\Data\Dict\D_Token.txt'                # Token : TokenWeight                         # read only
fileLocationVisa= '.\Data\Dict\D_Visa.txt'                  # VisaCode : VisaWeight :  VisaDescrAsInInput # read only
fileLocationWordsStam='.\Data\Dict\D_WordsStam.txt'         # Word                                        # read only
fileLocationEndOfLocation='.\Data\Dict\D_EndOfLocation.txt'# Word                                        # read only
fileLocationLocationsNotToMap='.\Data\Geo\D_LocationBan.txt' # Location
fileLocationWordsToCheck='.\Data\S_WordsToCheck.txt'   # Word : Count                                # initilalised
fileLocationLocationsResolved='.\Data\Geo\S_LocationResolved.txt' # Location : address : Postcode : distance
fileLocationLocationsToMap='.\Data\Geo\S_LocationInput.txt' # Location
fileLocationLocationsError='.\Data\Geo\S_LocationError.txt' # Location : Error
fileLocationErrors='.\Data\A_Errors.txt'               # Error
fileLocationStore='.\Data\A_Store.json'               # Error : Location                            # initialised

TokenWeight=dict()
for line in open(fileLocationTokens,'r'):
    wToken, wTokenWeight = line.strip().split(':')
    TokenWeight[wToken.lower()]=int(wTokenWeight)

VisaWeight=dict()
for line in open(fileLocationVisa, 'r'):
    wVisaType, wVisaWeight, wVisaDescription = line.strip().split(':')
    VisaWeight[wVisaDescription] = int(wVisaWeight)

WordsStam = set()
for line in open(fileLocationWordsStam, 'r'):
        WordsStam.add(line.strip().lower())

EndOfLocation=set()
for line in open(fileLocationEndOfLocation, 'r'):
    EndOfLocation.add(line.strip().lower())

DoNotLocate=set()
for line in open(fileLocationLocationsNotToMap, 'r'):
    DoNotLocate.add(line.strip().lower())


### 1. Read the input file, build the struct with empty addresses and fill WordsToCheck and LocationInput
WordsToCheck=dict()
LocationsToCheck=dict()
element=list()
rec={
    'rec':'',
    'scorev':0,
    'scored':0,
    'scoret':0,
    'Postcode':'',
    'distance':-1,
    'visacount':0,
    'visalist':[],
    'tokencount':0,
    'tokenlist':[],
    'words':[],
    'Addr':[]
    }

for line in open(fileLocationIn,'r'):
    line = line.strip()
    if line == PageHeader:
        continue
    elif re.match(PageNumPattern, line):
        print(line)
        continue
    elif line in VisaWeight.keys():
        rec['visalist'].append(line)
        rec['visacount'] += 1
        rec['scorev'] += VisaWeight[line]
    else:               # this is a line to parse: array of words where last words are geography
        if rec['rec']!='':          # record previous element and init new
            element.append(rec)
            rec = {
                'rec': '',
                'scorev': 0,
                'scored': 0,
                'scoret': 0,
                'Postcode': '',
                'distance': -1,
                'visacount': 0,
                'visalist': [],
                'tokencount': 0,
                'tokenlist': [],
                'words': [],
                'Addr': []
            }

        tranline = line.lower()
        tranline = re.sub(' upon ', 'QQQASCII32uponQQQASCII32', tranline, flags=re.I)
        tranline = re.sub('Trading as', 't/a', tranline, flags=re.I)
        for x in tranline.split():
            x = re.sub('[^a-zA-Z]', '', x).lower()
            rec['words'].append(x)
            if len(x)>3:
                if x in WordsStam:
                    continue
                elif x in TokenWeight:
                    rec['scoret']+=TokenWeight[x]
                    rec['tokencount']+=1
                    rec['tokenlist'].append(x)
                else:
                    WordsToCheck[x]=1+WordsToCheck.get(x,0)
        # words are filled, now fill the possible addresses
        if len(rec['words'])>0 and rec['words'][-1] not in EndOfLocation:
            x=rec['words'][-1]
            y={
                'id':len(x),
                'Attempt':x,
                'Resolved':'',
                'PostCode':'',
                'Distance':'',
                'Exception':''
            }
            rec['Addr'].append(y)
            LocationsToCheck[x]=1+LocationsToCheck.get(x,0)
            if len(rec['words']) > 1 and rec['words'][-2] not in EndOfLocation:
                x = rec['words'][-2]+' '+x
                y = {
                    'id': len(x),
                    'Attempt': x,
                    'Resolved': '',
                    'PostCode': '',
                    'Distance': '',
                    'Exception': ''
                }
                rec['Addr'].append(y)
                LocationsToCheck[x] = 1 + LocationsToCheck.get(x, 0)
                if len(rec['words']) > 2 and rec['words'][-3] not in EndOfLocation:
                    x = rec['words'][-3]+' '+x
                    y = {
                        'id': len(x),
                        'Attempt': x,
                        'Resolved': '',
                        'PostCode': '',
                        'Distance': '',
                        'Exception': ''
                    }
                    rec['Addr'].append(y)
                    LocationsToCheck[x] = 1 + LocationsToCheck.get(x, 0)
                    if len(rec['words']) > 3 and rec['words'][-4] not in EndOfLocation:
                        x = rec['words'][-4] + ' ' + x
                        y = {
                            'id': len(x),
                            'Attempt': x,
                            'Resolved': '',
                            'PostCode': '',
                            'Distance': '',
                            'Exception': ''
                        }
                        rec['Addr'].append(y)
                        LocationsToCheck[x] = 1 + LocationsToCheck.get(x, 0)
    # ended file read
    element.append(rec)
    rec = {
        'rec': '',
        'scorev': 0,
        'scored': 0,
        'scoret': 0,
        'Postcode': '',
        'distance': -1,
        'visacount': 0,
        'visalist': [],
        'tokencount': 0,
        'tokenlist': [],
        'words': [],
        'Addr': []
    }
"""
fout=open(fileLocationStore,'w')
fout.writelines(json.dumps(element))
fout.close()

fout = open(fileLocationLocationsToMap, 'w')
for x in list(list(sorted(LocationsToCheck.items(),key=operator.itemgetter(1),reverse=True))):
    fout.writelines(x[0]+'\n')
fout.close()

fout = open(fileLocationWordsToCheck, 'w')
for x in list(list(sorted(WordsToCheck.items(),key=operator.itemgetter(1),reverse=True))):
    fout.writelines(x[0]+'\n')
fout.close()
"""

## 2. Resolve locations
mygooglemapskey='AIzaSyA7NBT3S-z3GYgZhY067AkuQbNZSTVhblk'
myarrivaltime=1471943400 # 09:00 on working day
myhome="KT3 3HH"
gmaps = googlemaps.Client(key=mygooglemapskey)

delayer=0
for x in list(sorted(LocationsToCheck.items(), key=operator.itemgetter(1), reverse=True))[0]:
    print (x)
    delayer+=1
    if delayer==5:
        time.sleep(1)
    try:
        directions_result = gmaps.directions(myhome,x , mode="transit", arrival_time=myarrivaltime, region="uk")
        mn10 = directions_result[0]['legs'][0]['duration']['value']//600 * 10
        ea = directions_result[0]['legs'][0]['end_address']
        elat = directions_result[0]['legs'][0]['end_location']['lat']
        elng = directions_result[0]['legs'][0]['end_location']['lng']
        print ("coord",(elat,elng))
        geocode_result=gmaps.reverse_geocode((elat,elng))
        print("res",x,mn10,ea)
    except:
        e = sys.exc_info()[0]
        print("Error",str(e),x)




"""
##################################################################################

#VisaDescription=dict()
VisaWeight=dict()
#Visas = set()

TokenWeight=dict()
WordsStam = set()
#AllWords = set()

LocationResolved=dict()
LocationCommute=dict()
DoNotLocate = set()
AllLocations = set()
EndOfLocation=set()

#load Tokens dicts
#for line in open(fileLocationTokens,'r'):
#    wToken, wTokenWeight = line.strip().split(':')
#    TokenWeight[wToken]=int(wTokenWeight)
#    AllWords.add(wToken)

# load Visas dicts
#for line in open(fileLocationVisa, 'r'):
#    wVisaType, wVisaWeight, wVisaDescription = line.strip().split(':')
#    VisaDescription[wVisaType] = wVisaDescription
#    VisaWeight[wVisaDescription] = int(wVisaWeight)
#   Visas.add(wVisaDescription)


# load EndOfLocation
#for line in open(fileLocationEndOfLocation, 'r'):
#    EndOfLocation.add(line.strip().lower())

# load DoNotLocate
for line in open(fileLocationBannedMapped, 'r'):
        DoNotLocate.add(line.strip())

# load Location dicts
for line in open(fileLocationMapped, 'r'):
    try:
        wLocation,wResolvedDestination,wTenMinutesFromHome = line.strip().split(':')
        LocationResolved[wLocation]=wResolvedDestination
        LocationCommute[wLocation]=int(wTenMinutesFromHome)
        AllLocations.add(wLocation)
    except:
        continue

fERR = open(fileLocationErrors,'w')
fOUT = open(fileLocationOut,'w')
fCHK = open(fileLocationWordsToCheck,'w')
fMAP = open(fileLocationMapped,'a')
fBAN = open(fileLocationBannedMapped,'a')
fM2  = open(fileLocationLocationsToMap,'a')

AllLocations.union(DoNotLocate)
AllWords.union(WordsStam)

apisleeper=0
MeaningfulRec=False
element=[]
rec={
    'rec':'',
    'scorev':0,
    'scored':0,
    'scoret':0,
    'Postcode':'',
    'distance':-1,
    'visacount':0,
    'visalist':[],
    'tokencount':0,
    'tokenlist':[],
    'words':[],
    'AddrAttempt':[],
    'AddrResolved':[],
    'AddrPostcode':[],
    'AddrDistance':[],
    'exceptions': []
    }




with open(fileLocationIn) as fIN:
    for line in fIN:                    ## may be one of: header, pagenum, visa, company
        line=line.strip()
        if line == PageHeader:
            continue
        elif re.match(PageNumPattern,line):
            print(line)
            continue
        elif line in Visas:
            rec['visalist'].append(line)
            rec['visacount']+=1
            rec['scorev']+=VisaWeight[line]
        else:
            ## this is company::== company_name_word+ location_word+
            # 1. push existing record, as we are staring the new one
            # 2. initialise the record
            # 3. try to get distance:
            #   3.1. check if location is banned
            #   3.2. check if location is known from previous attempts
            #   3.3  google the distance
            #    3.3.1. if retriable error, do nothing (eg timeout or quota)
            #    3.3.2. if permanent error (no way to NI), write to banned locations
            #    3.3.3. if other error, write to errors
            #    3.3.4. if no error, write to rec AND to FileMapped
            # 4. split the words and cleanse them: only AZaz and more than 3 letters
            #   4.1. write all clean words to 'words'[]
            #   4.2. write the tokens

            # 1. push existing record, as we are staring the new one
            if MeaningfulRec: # write
                element.append(rec)
                j=json.dumps(rec)
                fOUT.writelines(j)
                print(j)
            # 2. initialise the record
            MeaningfulRec=True
            rec = {
                'rec': '',
                'scorev': 0,
                'scored': 0,
                'scoret': 0,
                'Postcode': '',
                'distance': -1,
                'visacount': 0,
                'visalist': [],
                'tokencount': 0,
                'tokenlist': [],
                'words': [],
                'AddrAttempt': [],
                'AddrResolved': [],
                'AddrPostcode': [],
                'AddrDistance': [],
                'exceptions': []
            }

            # 3. try to get distance:
            #   3.1. check if location is banned
            if line in AllLocations:
                #   3.2. check if location is known from previous attempts
                if line in DoNotLocate:
                    rec['location']='** BANNED LOCATION **'
                else:
                    rec['location']=LocationResolved[line]
                    rec['distance']=LocationCommute[line]
            #   3.3  google the distance
            else:
                try:
                    gogres = gmaps.directions(myhome, line, mode="transit", arrival_time=myarrivaltime, region="uk")
                    mn10 = 10 * (gogres[0]['legs'][0]['duration']['value'] // 600)
                    ea = gogres[0]['legs'][0]['end_address']
                    AllLocations.add(line)
                    LocationResolved[line]=ea
                    LocationCommute[line]=mn10
                    rec['location']=ea
                    rec['distance']=mn10
                    fMAP.writelines(line+':'+ea+':'+str(mn10)+'\n')
                    apisleeper+=1
                    if apisleeper == 10:
                        apisleeper=0
                        time.sleep(1)
                except:
                    e = sys.exc_info()[0]
                    fERR.writelines(str(e)+':'+line+'\n')
                    rec['exceptions'].append(str(e))
                    print(str(e) + ':' + line + '\n')
                if rec['distance'] == -1:
                    rec['scored']=0
                else:
                    rec['scored'] = 90-rec['distance']
            #    3.3.1. if retriable error, do nothing (eg timeout or quota)
            #    3.3.2. if permanent error (no way to NI), write to banned locations
            #    3.3.3. if other error, write to errors
            #    3.3.4. if no error, write to rec AND to FileMapped

            # 4. split the words and cleanse them: only AZaz and more than 3 letters
            #   4.1. write all clean words to 'words'[]
            #   4.2. write the tokens
            tranline=line.lower()
            tranline=re.sub(' upon ','QQQASCII32uponQQQASCII32',tranline,flags=re.I)
            tranline=re.sub('Trading as','t/a',tranline,flags=re.I)
            for x in tranline.split():
                x=re.sub('[^a-zA-Z\_]', '',x).lower()
                if len(x)>3:
                    rec['words'].append(x)
                    if x not in AllWords:
                        AllWords.add(x)
                        fCHK.writelines(x+'\n')
                    elif x in TokenWeight:
                        rec['tokenlist'].append(x)
                        rec['tokencount']+=1
                        rec['scoret']+=TokenWeight[x]
            if len(rec['words'])>0 and rec['words'][-1] not in EndOfLocation:
                fM2.writelines(rec['words'][-1]+'\n')
                if len(rec['words'])>1 and rec['words'][-2] not in EndOfLocation:
                    fM2.writelines(rec['words'][-2] + ' ' + rec['words'][-1]+'\n')
                    if len(rec['words'])>2 and rec['words'][-3] not in EndOfLocation:
                        fM2.writelines(rec['words'][-3] + ' ' + rec['words'][-2] + ' ' + rec['words'][-1]+'\n')
                        if len(rec['words']) > 3 and rec['words'][-4] not in EndOfLocation:
                            fM2.writelines(rec['words'][-4] + ' ' + rec['words'][-3] + ' ' + rec['words'][-2] + ' ' + rec['words'][-1] + '\n')

fM2.close()
fERR.close()
fOUT.close()
fCHK.close()
fMAP.close()
fBAN.close()


flocationSource = 'c:\kola\Score\LocationsToMap.txt'
flocationSorted = 'c:\kola\Score\LocationsToMapSorted.txt'
loclist=[]

for line in open(flocationSource,'r'):
    r=line.strip()[::-1]
    if r not in loclist:
        loclist.append(r)

list3 =[]
for x in sorted(loclist):
    list3.append(x[::-1])

fout=open(flocationSorted,'w')
fout.writelines('\n'.join(list3))
fout.close
sys.exit()



##############################################################################################################################


with open(fileLocated,'r') as fLocated:
    for lLocated in fLocated:
        sLocated.add(lLocated)
        fout.writelines(lLocated)
fLocated.close()




with open(fileBetterLocation,'r') as fLoc:
    for rudeLoc in fLoc:
        if rudeLoc not in sLocated:
            try:
                directions_result = gmaps.directions(myhome,rudeLoc.strip() , mode="transit", arrival_time=myarrivaltime, region="uk")
                mn10 = 10*directions_result[0]['legs'][0]['duration']['value']//600
                ea = directions_result[0]['legs'][0]['end_address']
                rudeLocationDuration[rudeLoc.strip()]=mn10
                cleanLocationDuration[ea]=mn10
                cleanRudeLocationDuration[rudeLoc.strip()]=ea
                sLocations.add(rudeLoc.strip()+':'+ea+':'+str(mn10))
#                print([rudeLoc.strip(),ea,mn10])
                sLocated.add(rudeLoc)
                fout.writelines(rudeLoc)
                time.sleep(1)
            except:
                e = sys.exc_info()[0]
                print("Error",str(e),rudeLoc)
                ferr.writelines(rudeLoc)
                sLocated.add(rudeLoc)
                sNoLocated.add(rudeLoc)
                continue



with open(fileLocationDuration,'w') as fLocationDuration:
    fLocationDuration.writelines('\n'.join(sLocations))
ferr.close()


sToken=set()                            # all tokens (words)
sLocation=set()                         # all locations (last tokens in sting)
sBetterLocation=set()
sFirst=set()                            # all first tokens in string (must be not locations)
sStop= set()                            # stop words, indicate end of company name, all behind it must be location: Ltd, Limited, Plc, Co,...

VisaDescription=dict()
TokenWeight=dict()
TokenType=dict()

#load visa list
with open(fileVisa,'r') as d_Visa:
    for line in d_Visa:
        wVisaType,wVisaWeight,wVisaDescription=line.strip().split(':')
        VisaDescription[wVisaType]=wVisaDescription
        TokenWeight[wVisaType]=wVisaWeight
        TokenType[wVisaType]='visa'
        sToken.add(wVisaType)

#load list of stop words
with open(fileStop,'r') as d_Stop:
    for line in d_Stop:
        sStop.add(line.strip())

with open(fileIn) as openfile:
    for a in openfile:
        a=a.strip()
        if a==PageHeader:
            continue
        if re.match(PageNumPattern,a):
            print(a)
            continue
        if a in VisaDescription.values():
            for key in VisaDescription.keys():
               a=a.replace(VisaDescription[key],key)
        else:                                               # not a visa, not a header - must be "company+ stop* sublocation? location"
            a=re.sub(' upon ','QQQASCII32uponQQQASCII32',a,flags=re.I)
            a=re.sub('Trading as','t/a',a,flags=re.I)
            words=a.split()
            sFirst.add((re.sub('[^a-zA-Z\_]', '', words[0])  ).capitalize())
            stop=0
            for i in words:
                if i.lower() in sStop:
                    stop=1
                    BetterLocation=''
                elif stop==1:
                    if re.sub('[^a-zA-Z\_]', '',i).lower()=='ta' or re.sub('[^a-zA-Z\_]', '',i).lower()=='ta':
                        stop=0
                        continue
                    sLocation.add( re.sub('[^a-z A-Z]','', i.replace('QQQASCII32',' ')).capitalize())
                    BetterLocation=BetterLocation+re.sub('[^a-z A-Z]','', i.replace('QQQASCII32',' ')).capitalize()+' '
            sLocation.add(re.sub('[^a-z A-Z]', '', words[-1].replace('QQQASCII32', ' ')).capitalize())     # there was no stop-word in the line, registering the last word as location
            if stop==0:
                BetterLocation=re.sub('[^a-z A-Z]', '', words[-1].replace('QQQASCII32', ' ')).capitalize()
            sBetterLocation.add((BetterLocation+' ,UK').replace('  ',' '))

print(sStop)
print(sLocation)
print(sBetterLocation)
print(sFirst)
fout.writelines("\n".join(sLocation))
fout.close()

with open(fileLocation,'w') as fLocation:
    fLocation.writelines('\n'.join(sLocation))

lBetterLocation = list(x for x in sBetterLocation if len(x)>4)
lBetterLocation.sort()

print (lBetterLocation)
with open(fileBetterLocation,'w') as fBLocation:
    fBLocation.writelines(('\n'.join(x for x in lBetterLocation if len(x)>4 )).replace('  ',' '))

"""
sys.exit()

#import json
#import urllib
#from datetime import datetime


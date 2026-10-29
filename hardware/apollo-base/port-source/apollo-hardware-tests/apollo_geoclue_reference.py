"""Compare an app location with live receiver NMEA; return no coordinates."""
import math
from gi.repository import Gio

def compare(connection, latitude, longitude):
    result={'receiver_reference_available':False,'matches_receiver':False}
    try:
        response=connection.call_sync('org.freedesktop.ModemManager1',
            '/org/freedesktop/ModemManager1','org.freedesktop.DBus.ObjectManager',
            'GetManagedObjects',None,None,Gio.DBusCallFlags.NONE,4000,None)
        objects=response.unpack()[0]
        for interfaces in objects.values():
            location=interfaces.get('org.freedesktop.ModemManager1.Modem.Location',{})
            traces=location.get('Location',{}).get(4,'')
            if not isinstance(traces,str): continue
            for sentence in traces.splitlines():
                fields=sentence.split(',')
                if not fields[0].endswith('GGA') or len(fields)<8: continue
                try:
                    quality,used=int(fields[6] or 0),int(fields[7] or 0)
                    if quality<1 or used<3: continue
                    a,b=float(fields[2]),float(fields[4])
                    lat=int(a/100)+(a%100)/60
                    lon=int(b/100)+(b%100)/60
                    if fields[3]=='S': lat=-lat
                    elif fields[3]!='N': continue
                    if fields[5]=='W': lon=-lon
                    elif fields[5]!='E': continue
                    if not all(math.isfinite(x) for x in (lat,lon,latitude,longitude)): continue
                    if not (-90<=lat<=90 and -180<=lon<=180): continue
                    dlat=math.radians(latitude-lat); dlon=math.radians(longitude-lon)
                    h=math.sin(dlat/2)**2+math.cos(math.radians(lat))*math.cos(math.radians(latitude))*math.sin(dlon/2)**2
                    distance=6371000*2*math.asin(min(1,math.sqrt(max(0,h))))
                    return {'receiver_reference_available':True,'matches_receiver':distance<100,
                            'receiver_distance_m':round(distance,3),'gga_quality':quality,'satellites_used':used}
                except (ValueError,TypeError,IndexError): continue
    except Exception:
        result['reference_query_error']=True
    return result

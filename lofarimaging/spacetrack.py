import requests
import configparser
import os
from skyfield.api import EarthSatellite

# from https://www.space-track.org/documentation#howto-api_python

def get_starlink_data(start_date, end_date):
    # See https://www.space-track.org/documentation for details on REST queries

    uriBase                = "https://www.space-track.org"
    requestLogin           = "/ajaxauth/login"
    requestCmdAction       = "/basicspacedata/query" 
    requestFindStarlinks   = "/class/gp_history/EPOCH/{START_DATE}--{END_DATE}/OBJECT_NAME/STARLINK~~/format/3le/orderby/LAUNCH_DATE%20asc"


    # ACTION REQUIRED FOR YOU:
    #=========================
    # Provide a config file in the same directory as this file, called SLTrack.ini, with this format (without the # signs)
    # [configuration]
    # username = XXX
    # password = YYY
    # output = ZZZ (optional)
    #
    # ... where XXX and YYY are your www.space-track.org credentials (https://www.space-track.org/auth/createAccount for free account)
    # ... and ZZZ is your Excel Output file - e.g. starlink-track.xlsx (note: make it an .xlsx file)

    # Use configparser package to pull in the ini file (pip install configparser)
    config = configparser.ConfigParser()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ini_path = os.path.join(base_dir, "starlink_data", "SLTrack.ini")
    file_read = config.read(ini_path)
    if not file_read:
        print("ERROR: SLTrack.ini not found.")
    elif not config.has_section("configuration"):
        print("ERROR: Header [configuration] not found in file.")
    else:
        configUsr = config.get("configuration","username")
        configPwd = config.get("configuration","password")
    siteCred = {'identity': configUsr, 'password': configPwd}


    # use requests package to drive the RESTful session with space-track.org
    with requests.Session() as session:
        # run the session in a with block to force session to close if we exit

        # need to log in first. note that we get a 200 to say the web site got the data, not that we are logged in
        resp = session.post(uriBase + requestLogin, data = siteCred)
        if resp.status_code != 200:
            print(f"Error {resp.status_code}. POST fail on login.")
            return ""

        # this query picks up all Starlink satellites from the catalog. Note - a 401 failure shows you have bad credentials 
        requestFindStarlinks = requestFindStarlinks.replace('{START_DATE}', start_date.replace(' ','%20'))
        requestFindStarlinks = requestFindStarlinks.replace('{END_DATE}', end_date.replace(' ','%20'))
                                                            
        resp = session.get(uriBase + requestCmdAction + requestFindStarlinks)
        if resp.status_code != 200:
            print(resp)
            print(f"Error {resp.status_code}. GET fail on request for Starlink satellites.")
            return ""
        else:
            print("Data downloaded, converting to Skyfield objects...")
            lines = resp.text.strip().splitlines()
            sats = {}
            
            # TLE has 3 lines/satellite
            for i in range(0, len(lines) - 2, 3):
                try:
                    name = lines[i].strip()
                    l1 = lines[i+1]
                    l2 = lines[i+2]
                    sat = EarthSatellite(l1, l2, name)
                    # save satellite and if ID already exists, overwrite with newest one.
                    sats[sat.model.satnum] = sat
                except Exception:
                    continue 
            satellites = list(sats.values())
            return satellites
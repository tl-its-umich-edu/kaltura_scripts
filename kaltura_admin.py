import argparse
import os
import sys
import logging
from KalturaClient.Plugins.Core import KalturaUserFilter, KalturaSessionType, KalturaNullableBoolean, KalturaFilterPager
from KalturaClient import KalturaClient, KalturaConfiguration
from datetime import date
from pandas import DataFrame
import pysftp
import json

"""
This report generates a list of admins of several Kaltura Management Consoles(kmcs) into a CSV file, 
and send the generated CSV file to a FTP server
"""

# Set this to DEBUG for more information
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def get_kaltura_session(user_id, partnerID, adminkey):
    config = KalturaConfiguration(partnerID)
    config.serviceUrl = "https://www.kaltura.com/"
    client = KalturaClient(config)
    secret = adminkey
    k_type = KalturaSessionType.ADMIN
    partner_id = partnerID
    expiry = 86400
    privileges = ""
    result = client.session.start(
        secret, user_id, k_type, partner_id, expiry, privileges)
    client.setKs(result)
    return client


"""
Get the configuration file
"""
parser = argparse.ArgumentParser(description='Generate Kaltura KMC admin list')
parser.add_argument('env', type=str, help='env json file with kmc settings')
args = parser.parse_args()
if not os.path.isfile(args.env):
    log.warn("env.json file does not exist. Please provide file path.")
    sys.exit()

"""
Generate admin list and report
"""
# load the configuration file
with open(args.env, "r") as jsonfile:
    data = json.load(jsonfile)
    kmcs = data["kmcs"]
    user_id = data["user_id"]
    ftp_server = data["ftp_server"]

# loop through all Kaltura Management Consoles
# looking for people with admin roles
username_list = []
for i in kmcs:
    kmc = kmcs[i]
    partnerID = kmc['partnerID']
    adminkey = kmc['adminkey']
    client = get_kaltura_session(user_id, partnerID, adminkey)
    filter = KalturaUserFilter()
    filter.isAdminEqual = KalturaNullableBoolean.TRUE_VALUE
    filter.loginEnabledEqual = KalturaNullableBoolean.TRUE_VALUE
    pager = KalturaFilterPager()
    pager.pageSize = 500
    result = client.user.list(filter, pager)
    log.info("Retriving kmc: {}".format(i))
    log.info("Total Records: {}".format(result.totalCount))
    for item in result.objects:
        if item.roleNames == "Publisher Administrator" or item.roleNames == "Content Manager":
            # remove @xxxxx
            if '@' in item.id:
                item_id = item.id.partition('@')
                id = item_id[0]
                username_list.append(id)
            else:
                username_list.append(item.id)
# remove duplicate
result = list(set(username_list))

# sort list
result.sort()

# result
df = DataFrame(result)

# generate the output csv file with timestamp
filename = 'Kaltura_admin_{}.csv'.format(date.today())
df.to_csv(filename, index=False, header=False)

"""**Connect to filezilla**"""
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
# connect to the sftp server and authenticate with a private key
sftp = pysftp.Connection(
    host=ftp_server["host"],
    username=ftp_server["username"],
    password=ftp_server["password"],
    cnopts=cnopts)

# send file to SFTP server
log.info(
    f'''Uploaded file to sftp server. File status: {sftp.put(filename)}''')

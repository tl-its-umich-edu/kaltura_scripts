import argparse
import os
import sys
import logging
from KalturaClient.Plugins.Core import KalturaUserFilter, KalturaSessionType, KalturaNullableBoolean, KalturaFilterPager
from KalturaClient import KalturaClient, KalturaConfiguration
from datetime import date
import pandas as pd
from tqdm import tqdm
import pysftp
import json

"""
This report generates a list of admins of several Kaltura Management Consoles(kmcs)
and send to the FTP server as a csv file
"""

# Set this to DEBUG for more information
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def get_kaltura_session(user_id, partnerID, adminkey):
    """
    get session using partnerID and adminkey from configuration file
    """
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


def get_kmc_admin_list(kaltura_user_id, kmcs):
    """
    loop through all Kaltura Management Consoles
    looking for people with admin roles
    """
    user_id_list = []
    for kmc_name, kmc in kmcs.items():
        log.info(f'processing kmc: {kmc_name}')
        partnerID = kmc['partnerID']
        adminkey = kmc['adminkey']
        client = get_kaltura_session(kaltura_user_id, partnerID, adminkey)
        filter = KalturaUserFilter()
        filter.isAdminEqual = KalturaNullableBoolean.TRUE_VALUE
        filter.loginEnabledEqual = KalturaNullableBoolean.TRUE_VALUE
        pager = KalturaFilterPager()
        pager.pageSize = 500
        try:
            result = client.user.list(filter, pager)
            log.info(
                f"Retriving kmc: {kmc_name} Total Records: {result.totalCount}")
            for item in result.objects:
                if item.roleNames == "Publisher Administrator" or item.roleNames == "Content Manager":
                    kmc_user_id = item.id.lower()
                    if '@' in kmc_user_id:
                        # remove @xxxxx
                        item_id = kmc_user_id.partition('@')
                        id = item_id[0]
                        kmc_user_id = id

                    # add to user_id_list
                    user_id_list.append(kmc_user_id)
        except Exception as e:
            log.exception(f'Problem retrieving items for kmc: {kmc_name} {type(e)} {e.args} {e}')
        
    # remove duplicate
    result_list = list(set(user_id_list))
    log.info(len(result_list))

    # sort list
    result_list.sort()

    # add to dataframe
    user_df = pd.DataFrame()
    user_df["USER_ID"] = result_list
    return user_df


def sftp_kmc_admin_list(kmc_admin_df, ftp_server):
    """
    sftp the KMC admin user information as an csv file to SFTP server
    """
    # connect to the sftp server and authenticate with a private key
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    log.info(f'FTP result to server: {ftp_server["host"]}')
    sftp = pysftp.Connection(
        host=ftp_server["host"],
        username=ftp_server["username"],
        password=ftp_server["password"],
        cnopts=cnopts)

    # send file to SFTP server
    filename = 'Kaltura_admin_{}.csv'.format(date.today())
    with sftp.open(filename, 'w+') as f:
        chunksize = 10000
        with tqdm(total=len(kmc_admin_df)) as progbar:
            log.info(f"status {progbar}")
            kmc_admin_df.to_csv(f, index=False, chunksize=chunksize)
            progbar.update(chunksize)
    log.info("Uploaded file to sftp server.")


def main():
    """
    Get the configuration file
    """
    parser = argparse.ArgumentParser(
        description='Generate Kaltura KMC admin list')
    parser.add_argument(
        'env', type=str, help='env json file with kmc settings')
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
        kaltura_user_id = data["user_id"]
        ftp_server = data["ftp_server"]

    # generate the output csv file with timestamp
    kmc_admin_df = get_kmc_admin_list(kaltura_user_id, kmcs)
    log.info(f"shape of kmc_admin_list {kmc_admin_df.shape}")

    # send the kaltura kmc admin list to the sftp server
    sftp_kmc_admin_list(kmc_admin_df, ftp_server)


if __name__ == "__main__":
    main()

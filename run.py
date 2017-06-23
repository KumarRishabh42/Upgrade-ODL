import wget
import optparse
import os
import paramiko
import psutil
import re
import subprocess
import time

from helpers.exceptions import WgetError, TimedoutError
from helpers.decorators import timeout


class UpgradeCeph(object):
    '''
        Tool to Upgrade ODL
    '''

    def __init__(self):
        self.parser = self._get_opt_parser()
        cls = UpgradeCeph
        cls.options, cls.arguments = self.parser.parse_args()

        if self.prelim_checks(cls.options.old_dir, cls.options.new_dir,
                              cls.options.odl_url):
            try:
                cls.odl_location = self.wget_url(cls.options.odl_url)
            except WgetError:
                print 'wget error for the odl_url.'
                exit()

            try:
                if not self.old_odl_check():
                    self.run_old_odl(cls.options.old_dir)
                    ssh_client = self.get_ssh_client()
                    old_odl_feature_list = self.get_feature_list(ssh_client)
                    self.close_old_karaf_connection(ssh_client)
                    while self.old_odl_check():
                        time.sleep(1)
                    self.move_new_odl_to_folder(cls.odl_location, cls.options.new_dir)
                    self.run_old_odl(cls.options.new_dir)
            except TimedoutError:
                print 'odl check timed out'
                exit()

    def move_new_odl_to_folder(self, old_loc, new_dir):
        old_loco = old_loc + "/*"
        subprocess.Popen('mv ' + old_loco + ' ' + new_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

    @timeout(100)
    def close_old_karaf_connection(self, ssh):
        stdin, stdout, stderr = ssh.exec_command('shutdown -f')

    @timeout(100)
    def get_ssh_client(self, hostname='localhost', port=8101, username='karaf', password='karaf'):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, port=port, username=username, password=password)
        return ssh

    def get_features_list(self, ssh):
        feature_list = []
        stdin, stdout, stderr = ssh.exec_command('feature:list --installed')
        features = stdout.readlines()
        features.pop(0)
        features.pop(0)
        for feature in features:
            featur = re.sub('[\s+]', '', feature).split('|')
            feature_list.append(featur[0] + '/' + featur[1])
        return feature_list

    @timeout(600)
    def run_old_odl(self, old_odl):
        old_odl_start = old_odl + '/bin/start'
        subprocess.Popen([old_odl_start], stdout=subprocess.PIPE, shell=False, bufsize=0)
        while not self.old_odl_check():
            time.sleep(1)

    @timeout(10)
    def old_odl_check(self):
        # check if old controller running right now we check if 8101 port is running
        pid = 'netstat -tulpn | grep java | grep 8101'
        (out, err) = subprocess.Popen(pid, stdout=subprocess.PIPE, shell=True, bufsize=0).communicate()
        if not out:
            return False
        return True

    def wget_url(self, odl_url):
        odl_file_name = wget.download(odl_url)
        return odl_file_name

    def prelim_checks(self, old_dir, new_dir, odl_url):
        if old_dir is None or new_dir is None or odl_url is None:
            return False

        for dirpath, dirnames, files in os.walk(old_dir):
                if not files:
                    return False

        for dirpath, dirnames, files in os.walk(new_dir):
                if files:
                    print 'new_dir not empty.'

    def _get_opt_parser(self):
        desc = ('Command line parser for Upgrade ODL \n')

        parser = optparse.OptionParser(description=desc)
        parser.add_option('-o', '--old_dir', dest='old_dir', default=None)
        parser.add_option('-n', '--new_dir', dest='new_dir', default=None)
        parser.add_option('-u', '--odl_url', dest='odl_url', default=None)
        return parser

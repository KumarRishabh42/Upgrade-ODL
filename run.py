'''
    MIT License

    Copyright (c) 2017 Kumar Rishabh

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
'''

import wget
import optparse
import os
import paramiko
import psutil
import re
import subprocess
import time
import zipfile

from helpers.exceptions import WgetError, TimedoutError
from helpers.decorators import timeout


class UpgradeODL(object):
    '''
        Tool to Upgrade ODL
    '''

    def __init__(self):
        self.parser = self._get_opt_parser()
        cls = UpgradeODL
        cls.options, cls.arguments = self.parser.parse_args()
        print cls.options
        if self.prelim_checks(cls.options.old_dir, cls.options.new_dir,
                              cls.options.odl_url):
            # First Check if the old_dir is valid, new_dir is empty and
            # odl_url is not None

            try:
                cls.odl_location = self.wget_url(cls.options.odl_url)
                # Download and inflate the new_odl installation
            except WgetError:
                print 'wget error for the odl_url.'
                exit()
            try:
                if not self.old_odl_check():
                    self.run_old_odl(cls.options.old_dir)
                ssh_client = self.get_ssh_client()

                old_odl_feature_list = self.get_features_list(ssh_client)
                print old_odl_feature_list

                self.close_old_karaf_connection(ssh_client)

                while self.old_odl_check():
                    time.sleep(1)
                self.move_new_odl_to_folder(cls.odl_location, cls.options.new_dir)
                self.run_old_odl(cls.options.new_dir, True)
            except TimedoutError:
                print 'odl check timed out'
                exit()
        else:
            print 'Not enough input given'
            exit()

    def move_new_odl_to_folder(self, old_loc, new_dir):
        old_loco = old_loc + "/*"
        process = subprocess.Popen('mv ' + old_loco + ' ' + new_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        process.wait()

    @timeout(100)
    def close_old_karaf_connection(self, ssh):
        stdin, stdout, stderr = ssh.exec_command('shutdown -f')

    @timeout(600)
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
    def run_old_odl(self, old_odl, is_new=False):
        old_odl_start = old_odl + 'bin/start'

        print os.path.abspath(old_odl_start)
        print os.path.isfile(old_odl_start)

        os.chmod(os.path.abspath(old_odl_start), 0755)

        process = subprocess.Popen([old_odl_start], stdout=subprocess.PIPE, shell=False, bufsize=0)
        while not self.old_odl_check(is_new):
            time.sleep(1)

    @timeout(10)
    def old_odl_check(self, is_new=False):
        # check if controller running right now we check if 8101 port is running
        pid = 'netstat -tulpn | grep java | grep 8101'
        FNULL = open(os.devnull, 'w')
        (out, err) = subprocess.Popen(pid, stdout=subprocess.PIPE, stderr=FNULL, shell=True, bufsize=0).communicate()
        FNULL.close()
        if not out:
            if is_new:
                print 'new odl not running'
            else:
                print 'old odl not running'
            return False
        print out
        if is_new:
            print 'new odl running'
        else:
            print 'old odl running ....'
        return True

    def wget_url(self, odl_url):
        # Assumes the file is zip file

        # odl_file_name = wget.download(odl_url)
        odl_file_name = 'distribution-karaf-0.5.4-Boron-SR4.zip'

        zip_ref = zipfile.ZipFile(odl_file_name, 'r')
        odl_file_location = odl_file_name.strip('.zip')
        zip_ref.extractall('/tmp')
        return '/tmp/' + odl_file_location

    def prelim_checks(self, old_dir, new_dir, odl_url):
        if old_dir is None or new_dir is None or odl_url is None:
            return False

        for dirpath, dirnames, files in os.walk(old_dir):
                if not dirnames and not files:
                    print 'old odl dir empty'
                    return False
                else:
                    break
        for dirpath, dirnames, files in os.walk(new_dir):
                if files:
                    print 'new_dir not empty.'
                    return False
        return True

    def _get_opt_parser(self):
        desc = ('Command line parser for Upgrade ODL \n')

        parser = optparse.OptionParser(description=desc)
        parser.add_option('-o', '--old_dir', dest='old_dir', default=None)
        parser.add_option('-n', '--new_dir', dest='new_dir', default=None)
        parser.add_option('-u', '--odl_url', dest='odl_url', default=None)
        return parser

if __name__ == "__main__":
     UpgradeODL = UpgradeODL()

import wget
import optparse
import os
import psutil

from helpers.exceptions import WgetError
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
                self.sanity_checks()
            except:
                pass
                
    #def sanity_checks(self):
        # check if old controller running

    #    get_odl_pid = "ps aux | grep karaf | grep -v 'color' | tr -s ' ' | cut -f2 -d' '"
    #    odl_pid = os.popen(odl_pid).read().strip()

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

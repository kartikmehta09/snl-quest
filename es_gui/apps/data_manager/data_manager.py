from __future__ import absolute_import, print_function

import os
import collections
import json
import calendar
import threading
import logging
import copy

import pandas as pd
from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty

from es_gui.resources.widgets.common import LoadingModalView


class DataManager(EventDispatcher):
    data_bank = {}
    n_threads_scanning = NumericProperty(0)

    def __init__(self, data_bank_root='data', **kwargs):
        super(DataManager, self).__init__(**kwargs)
        self.data_bank_root = data_bank_root
    
    def on_n_threads_scanning(self, instance, value):
        if value == 0:
            logging.info('DataManager: Data bank scan complete.')
            Animation.stop_all(self.loading_screen.logo, 'opacity')
            self.loading_screen.dismiss()

    @property
    def data_bank_root(self):
        """The path to the root of the data download directory."""
        return self._data_bank_root
    
    @data_bank_root.setter
    def data_bank_root(self, value):
        self._data_bank_root = value
    
    def get_markets(self):
        """Returns a keys view of all of the markets for valuation available."""
        # self.scan_data_bank()

        return self.data_bank.keys()

    def scan_data_bank(self):
        """Scans the data bank to determine what data has been downloaded."""
        # Check if data bank exists.
        try:
            os.listdir(self.data_bank_root)
        except FileNotFoundError:
            return

        # Open loading screen.
        self.loading_screen = LoadingModalView()
        self.loading_screen.loading_text.text = 'Scanning data files...'
        self.loading_screen.open()

        market_names = []

        # Determine the market areas that have downloaded data.
        for dir_entry in os.scandir(self.data_bank_root):
            if not dir_entry.name.startswith('.'):
                market_names.append(dir_entry.name)

        # market_names = ['NYISO'] # TODO: comment out, this is just for testing NYISO scan data functions

        # threads = []

        self.n_threads_scanning = 1

        def _scan_data_bank():
            if 'ERCOT' in market_names:
                self._scan_ercot_data_bank()
                
            if 'PJM' in market_names:
                self._scan_pjm_data_bank()
                
            if 'MISO' in market_names:
                self._scan_miso_data_bank()

            if 'NYISO' in market_names:
                self._scan_nyiso_data_bank()

            self.n_threads_scanning -= 1
        
        thread = threading.Thread(target=_scan_data_bank)
        thread.start()            
    
    def _scan_pjm_data_bank(self):
        """Scans the PJM data bank."""
        pjm_root = os.path.join(self.data_bank_root, 'PJM')
        pjm_data_bank = {}

        # Scan LMP files.
        if 'LMP' in os.listdir(pjm_root):
            pjm_data_bank['LMP'] = {}
            lmp_dir = os.path.join(pjm_root, 'LMP')

            # Identify pricing node ID dirs.
            for node_dir_entry in os.scandir(lmp_dir):
                if not node_dir_entry.name.startswith('.'):
                    node_id = node_dir_entry.name
                    pjm_data_bank['LMP'][node_id] = {}
                    node_id_dir = node_dir_entry.path

                    # Identify year dirs.
                    for year_dir_entry in os.scandir(node_id_dir):
                        if not year_dir_entry.name.startswith('.'):
                            year = year_dir_entry.name
                            pjm_data_bank['LMP'][node_id][year] = []
                            year_dir = year_dir_entry.path

                            # Identify month files.
                            for lmp_dir_entry in os.scandir(year_dir):
                                if not lmp_dir_entry.name.startswith('.'):
                                    lmp_file = lmp_dir_entry.name
                                    yyyymm, _ = lmp_file.split('_', maxsplit=1)
                                    month = yyyymm[-2:]
                                    pjm_data_bank['LMP'][node_id][year].append(month)
        
        # Scan Reg files.
        if 'REG' in os.listdir(pjm_root):
            pjm_data_bank['REG'] = {}
            reg_dir = os.path.join(pjm_root, 'REG')

            # Identify year dirs.
            for year_dir_entry in os.scandir(reg_dir):
                if not year_dir_entry.name.startswith('.'):
                    year = year_dir_entry.name
                    pjm_data_bank['REG'][year] = []
                    year_dir = year_dir_entry.path

                    # Identify month files.
                    for reg_dir_entry in os.scandir(year_dir):
                        if not reg_dir_entry.name.startswith('.'):
                            reg_file = reg_dir_entry.name
                            yyyymm, _ = reg_file.split('_', maxsplit=1)
                            month = yyyymm[-2:]
                            pjm_data_bank['REG'][year].append(month)
        
        # Scan Mileage files.
        if 'MILEAGE' in os.listdir(pjm_root):
            pjm_data_bank['MILEAGE'] = {}
            mileage_dir = os.path.join(pjm_root, 'MILEAGE')

            # Identify year dirs.
            for year_dir_entry in os.scandir(mileage_dir):
                if not year_dir_entry.name.startswith('.'):
                    year = year_dir_entry.name
                    pjm_data_bank['MILEAGE'][year] = []
                    year_dir = year_dir_entry.path

                    # Identify month files.
                    for mileage_dir_entry in os.scandir(year_dir):
                        if not mileage_dir_entry.name.startswith('.'):
                            mileage_file = mileage_dir_entry.name
                            yyyymm, _ = mileage_file.split('_', maxsplit=1)
                            month = yyyymm[-2:]
                            pjm_data_bank['MILEAGE'][year].append(month)
        
        self.data_bank['PJM'] = pjm_data_bank
    
    def _scan_miso_data_bank(self):
        """Scans the MISO data bank."""
        miso_root = os.path.join(self.data_bank_root, 'MISO')
        miso_data_bank = {}
        miso_nodes = self.get_nodes('MISO')

        # LMP scan.
        if 'LMP' in os.listdir(miso_root):
            miso_data_bank['LMP'] = {}
            lmp_dir = os.path.join(miso_root, 'LMP')

            # Scan LMP directory structure once.
            miso_lmp_dir_struct = {}

            for year_dir_entry in os.scandir(lmp_dir):
                if not year_dir_entry.name.startswith('.'):
                    year = year_dir_entry.name
                    year_dir = year_dir_entry.path
                    miso_lmp_dir_struct[year] = []

                    for month_dir_entry in os.scandir(year_dir):
                        if not month_dir_entry.name.startswith('.'):
                            month = month_dir_entry.name
                            month_dir = month_dir_entry.path
                            
                            # Get the number of days in the month and compare it to number of files in dir.
                            _, n_days_month = calendar.monthrange(int(year), int(month))
                            n_files = len([dir_entry for dir_entry in os.scandir(month_dir) if not dir_entry.name.startswith('.')])

                            # Only add the month if it has a full set of data.
                            if n_files == n_days_month:
                                miso_lmp_dir_struct[year].append(month)

            for node in miso_nodes.keys():
                tmp_dir = copy.deepcopy(miso_lmp_dir_struct)
                miso_data_bank['LMP'][node] = tmp_dir                
        
        # MCP scan.
        if 'MCP' in os.listdir(miso_root):
            miso_data_bank['MCP'] = {}
            mcp_dir = os.path.join(miso_root, 'MCP')

            for year_dir_entry in os.scandir(mcp_dir):
                if not year_dir_entry.name.startswith('.'):
                    year = year_dir_entry.name
                    year_dir = year_dir_entry.path
                    miso_data_bank['MCP'][year] = []

                    for month_dir_entry in os.scandir(year_dir):
                        if not month_dir_entry.name.startswith('.'):
                            month = month_dir_entry.name
                            month_dir = month_dir_entry.path
                            
                            # Get the number of days in the month and matches it to number of files in dir.
                            _, n_days_month = calendar.monthrange(int(year), int(month))
                            n_files = len([dir_entry for dir_entry in os.scandir(month_dir) if not dir_entry.name.startswith('.')])

                            # Only add the month if it has a full set of data.
                            if n_files == n_days_month:
                                miso_data_bank['MCP'][year].append(month)
        
        self.data_bank['MISO'] = miso_data_bank
    
    def _scan_ercot_data_bank(self):
        """Scans the ERCOT data bank."""
        ercot_root = os.path.join(self.data_bank_root, 'ERCOT')
        ercot_data_bank = {}
        ercot_nodes = self.get_nodes('ERCOT')

        # SPP scan.
        if 'SPP' in os.listdir(ercot_root):
            ercot_data_bank['SPP'] = {}
            spp_dir = os.path.join(ercot_root, 'SPP')

            # Scan SPP directory structure once.
            ercot_spp_dir_struct = {}

            for year_dir_entry in os.scandir(spp_dir):
                if not year_dir_entry.name.startswith('.'):
                    year = year_dir_entry.name
                    year_dir = year_dir_entry.path
                    ercot_spp_dir_struct[year] = []

                    # TODO: Not all yearly files have every month of data... but opening them to look is costly.
                    ercot_spp_dir_struct[year].extend([str(x+1).zfill(2) for x in range(0, 12)])

            for node in ercot_nodes.keys():
                tmp_dir = copy.deepcopy(ercot_spp_dir_struct)
                ercot_data_bank['SPP'][node] = tmp_dir
        
        # CCP scan.
        if 'CCP' in os.listdir(ercot_root):
            ercot_data_bank['CCP'] = {}
            ccp_dir = os.path.join(ercot_root, 'CCP')

            # Determine the years of data downloaded.
            for year_dir_entry in os.scandir(ccp_dir):
                if not year_dir_entry.name.startswith('.'):
                    year = year_dir_entry.name
                    year_dir = year_dir_entry.path
                    ercot_data_bank['CCP'][year] = []

                    # Verify a file exists in the directory.
                    if os.listdir(year_dir):
                        ercot_data_bank['CCP'][year].extend([str(x+1).zfill(2) for x in range(0, 12)])
        
        self.data_bank['ERCOT'] = ercot_data_bank

########################################################################################################################

    def _scan_nyiso_data_bank(self):
        """Scans the NYISO data bank."""
        nyiso_root = os.path.join(self.data_bank_root, 'NYISO')
        nyiso_data_bank = {}

        # LBMP scan.
        # nyiso_nodes = self.get_nodes('NYISO')

        # LBMP_ASP = ['LBMP', 'ASP']

        # for casedata in LBMP_ASP:
        #     print('TBF')
        #     nyiso_data_bank[casedata] = {}
        #     if casedata == 'LBMP':
        #         case_dir = os.path.join(nyiso_root, 'LBMP', 'DAM', 'gen')  # TODO: finalize the zone, gen thing
        #         caseloop_n = nyiso_nodes.keys()
        #     elif casedata == 'ASP':
        #         asp_dir = os.path.join(nyiso_root, 'ASP', 'DAM')  # TODO: finalize the zone, gen thing
        #         caseloop_n = 'n/a'
        #
        #     for node in nyiso_nodes.keys():
        #         nyiso_data_bank['LBMP'][node] = {}

        if 'LBMP' in os.listdir(nyiso_root):
            nyiso_data_bank['LBMP'] = {}

            pathf_nodeszones = os.path.join('es_gui', 'apps', 'data_manager', '_static', 'nodes_nyiso.csv')
            df_nodeszones = pd.read_csv(pathf_nodeszones, index_col=False)

            # Get zone and gen nodes.
            df_zone_nodes = df_nodeszones.loc[df_nodeszones['Node ID'] == df_nodeszones['Zone ID'], :]
            df_gen_nodes = df_nodeszones.loc[df_nodeszones['Node ID'] != df_nodeszones['Zone ID'], :]

            # Gen nodes scan.
            lbmp_dir = os.path.join(nyiso_root, 'LBMP', 'DAM', 'gen')

            if os.path.exists(lbmp_dir):
                nyiso_lbmp_gen_dir_struct = {}

                for year_dir_entry in os.scandir(lbmp_dir):
                    if not year_dir_entry.name.startswith('.'):
                        year = year_dir_entry.name
                        year_dir = year_dir_entry.path
                        nyiso_lbmp_gen_dir_struct[year] = []

                        for month_dir_entry in os.scandir(year_dir):
                            if not month_dir_entry.name.startswith('.'):
                                month = month_dir_entry.name
                                month_dir = month_dir_entry.path

                                # Get the number of days in the month and compare it to number of files in dir.
                                _, n_days_month = calendar.monthrange(int(year), int(month))
                                n_files = len([dir_entry for dir_entry in os.scandir(month_dir) if
                                                not dir_entry.name.startswith('.')])

                                # Only add the month if it has a full set of data.
                                if n_files == n_days_month:
                                    nyiso_lbmp_gen_dir_struct[year].append(month)

                for node_id in df_gen_nodes['Node ID']:
                    tmp_dir = copy.deepcopy(nyiso_lbmp_gen_dir_struct)
                    nyiso_data_bank['LBMP'][node_id] = tmp_dir
            
            # Zone nodes scan.
            lbmp_dir = os.path.join(nyiso_root, 'LBMP', 'DAM', 'zone')

            if os.path.exists(lbmp_dir):
                nyiso_lbmp_zone_dir_struct = {}

                for year_dir_entry in os.scandir(lbmp_dir):
                    if not year_dir_entry.name.startswith('.'):
                        year = year_dir_entry.name
                        year_dir = year_dir_entry.path
                        nyiso_lbmp_zone_dir_struct[year] = []

                        for month_dir_entry in os.scandir(year_dir):
                            if not month_dir_entry.name.startswith('.'):
                                month = month_dir_entry.name
                                month_dir = month_dir_entry.path

                                # Get the number of days in the month and compare it to number of files in dir.
                                _, n_days_month = calendar.monthrange(int(year), int(month))
                                n_files = len([dir_entry for dir_entry in os.scandir(month_dir) if
                                                not dir_entry.name.startswith('.')])

                                # Only add the month if it has a full set of data.
                                if n_files == n_days_month:
                                    nyiso_lbmp_zone_dir_struct[year].append(month)

                for node_id in df_zone_nodes['Node ID']:
                    tmp_dir = copy.deepcopy(nyiso_lbmp_zone_dir_struct)
                    nyiso_data_bank['LBMP'][node_id] = tmp_dir

        # ASP scan.
        if 'ASP' in os.listdir(nyiso_root):
            nyiso_data_bank['ASP'] = {}
            asp_dir = os.path.join(nyiso_root, 'ASP', 'DAM') # TODO: finalize the zone, gen thing

            for year_dir_entry in os.scandir(asp_dir):
                if not year_dir_entry.name.startswith('.'):
                    year = year_dir_entry.name
                    year_dir = year_dir_entry.path
                    nyiso_data_bank['ASP'][year] = []

                    for month_dir_entry in os.scandir(year_dir):
                        if not month_dir_entry.name.startswith('.'):
                            month = month_dir_entry.name
                            month_dir = month_dir_entry.path

                            # Get the number of days in the month and matches it to number of files in dir.
                            _, n_days_month = calendar.monthrange(int(year), int(month))
                            n_files = len \
                                ([dir_entry for dir_entry in os.scandir(month_dir) if
                                  not dir_entry.name.startswith('.')])

                            # Only add the month if it has a full set of data.
                            if n_files == n_days_month:
                                nyiso_data_bank['ASP'][year].append(month)

        self.data_bank['NYISO'] = nyiso_data_bank

    def get_nodes(self, market_area):
        """Retrieves all available pricing nodes for the given market_area."""
        if market_area == 'ERCOT':
            # Reads static node ID list.
            static_ercot_node_list = os.path.join('es_gui', 'apps', 'data_manager', '_static', 'nodes_ercot.csv')

            node_df = pd.read_csv(static_ercot_node_list)
            node_dict = {row[0]: row[1] for row in zip(node_df['Node ID'], node_df['Node Name'])}
        elif market_area == 'PJM':
            # Reads static node ID list.
            static_pjm_node_list = os.path.join('es_gui', 'apps', 'data_manager', '_static', 'nodes_pjm.csv')
            node_df = pd.read_csv(static_pjm_node_list)
            node_mapping = {str(row[0]): '{nodename} ({nodeid})'.format(nodename=row[1], nodeid=row[0]) for row in zip(node_df['Node ID'], node_df['Node Name'])}

            # Reads keys of PJM LMP data bank.
            node_id_list = self.data_bank['PJM']['LMP'].keys()
            node_dict = {node_id: node_mapping.get(node_id, node_id) for node_id in node_id_list}
        elif market_area == 'MISO':
            # Reads static node ID list.
            static_miso_node_list = os.path.join('es_gui', 'apps', 'data_manager', '_static', 'nodes_miso.csv')

            node_df = pd.read_csv(static_miso_node_list)
            node_dict = {row[0]: row[1] for row in zip(node_df['Node ID'], node_df['Node Name'])}
        ################################################################################################################
        elif market_area == 'NYISO':
            # Reads static node ID list.
            static_nyiso_node_list = os.path.join('es_gui', 'apps', 'data_manager', '_static', 'nodes_nyiso.csv')
            node_df = pd.read_csv(static_nyiso_node_list)
            node_mapping = {row[0]: row[1] for row in zip(node_df['Node ID'], node_df['Node Name'])}

            # Reads keys of NYISO LBMP data bank.
            node_id_list = self.data_bank['NYISO']['LBMP'].keys()
            node_dict = {node_id: node_mapping.get(node_id, node_id) for node_id in node_id_list}
        ################################################################################################################
        # Use this pattern of reading data_bank node keys to generate the node_dict (key = value) if no CSV LUT exists:
        # node_id_list = self.data_bank['xyz']['LMP'].keys()
        # node_dict = {node_id: node_id) for node_id in node_id_list}
        else:
            raise(DataManagerException('Invalid market_area given (got {0})'.format(market_area)))
        
        # Sort by name alphabetically before returning.
        return_dict = collections.OrderedDict(sorted(node_dict.items(), key=lambda t: t[1]))
        
        return return_dict
    
    def get_valuation_revstreams(self, market_area, node):
        """Retrieves the available revenue streams for a given node in a given market_area based on downloaded data."""
        rev_stream_dict = {}

        with open(os.path.join('es_gui', 'apps', 'data_manager', '_static', 'valuation_rev_streams.json'), 'r') as fp:
            rev_stream_defs = json.load(fp).get(market_area, {})

        if market_area == 'ERCOT':
            ercot_data_bank = self.data_bank['ERCOT']

            spp_data = ercot_data_bank['SPP'].get(node, [])
            ccp_data = ercot_data_bank.get('CCP', [])

            if spp_data:
                # Arbitrage is available.
                rev_stream_dict['Arbitrage'] = rev_stream_defs['Arbitrage']
            if spp_data and ccp_data:
                # Arbitrage and regulation is available.
                rev_stream_dict['Arbitrage and regulation'] = rev_stream_defs['Arbitrage and regulation']
        elif market_area == 'PJM':
            pjm_data_bank = self.data_bank['PJM']

            lmp_data = pjm_data_bank['LMP'].get(node, [])
            reg_data = pjm_data_bank.get('REG', [])
            mileage_data = pjm_data_bank.get('MILEAGE', [])

            if lmp_data:
                # Arbitrage is available.
                rev_stream_dict['Arbitrage'] = rev_stream_defs['Arbitrage']
            if lmp_data and reg_data and mileage_data:
                # Arbitrage and regulation is available.
                rev_stream_dict['Arbitrage and regulation'] = rev_stream_defs['Arbitrage and regulation']
        elif market_area == 'MISO':
            miso_data_bank = self.data_bank['MISO']

            lmp_data = miso_data_bank['LMP'].get(node, [])
            reg_data = miso_data_bank.get('MCP', [])

            if lmp_data:
                # Arbitrage is available.
                rev_stream_dict['Arbitrage'] = rev_stream_defs['Arbitrage']
            if lmp_data and reg_data:
                # Arbitrage and regulation is available.
                rev_stream_dict['Arbitrage and regulation'] = rev_stream_defs['Arbitrage and regulation']
        elif market_area == 'NYISO':
            nyiso_data_bank = self.data_bank['NYISO']

            lbmp_data = nyiso_data_bank['LBMP'].get(node, [])
            asp_data = nyiso_data_bank.get('ASP', [])

            if lbmp_data:
                # Arbitrage is available.
                rev_stream_dict['Arbitrage'] = rev_stream_defs['Arbitrage']
            if lbmp_data and asp_data:
                # Arbitrage and regulation is available.
                rev_stream_dict['Arbitrage and regulation'] = rev_stream_defs['Arbitrage and regulation']
        else:
            raise(DataManagerException('Invalid market_area given (got {0})'.format(market_area)))
            
        return rev_stream_dict
    
    def get_historical_datasets(self, market_area, node, rev_streams):
        """Retrieves the available historical datasets for a given node in a given market area using the given rev_streams."""
        hist_datasets_dict = {}

        hist_data_options = self.get_historical_data_options(market_area, node, rev_streams)

        for year, month_list in hist_data_options.items():
            hist_dataset = [{'month': month, 'year': year} for month in month_list]
            hist_datasets_dict['{year}'.format(year=year)] = hist_dataset

        # Sort before returning.
        return_dict = collections.OrderedDict(sorted(hist_datasets_dict.items(), key=lambda t: int(t[0])))
        
        return return_dict
    
    def get_historical_data_options(self, market_area, node, rev_streams):
        """Retrieves the years of available historical data for a given node in a given market area using the given rev_streams."""
        hist_data_options = {}

        if market_area == 'ERCOT':
            ercot_data_bank = self.data_bank['ERCOT']

            spp_data = ercot_data_bank['SPP'].get(node, {})

            if rev_streams == 'Arbitrage and regulation':
                # Ensure regulation data is downloaded for each month.
                reg_data = ercot_data_bank['CCP']

                for year, month_list in spp_data.items():
                    reg_month_list = reg_data.get(year, [])

                    # Compute intersection of all data types.
                    months_common = list(set(month_list).intersection(set(reg_month_list)))

                    if months_common:
                        hist_data_options[year] = sorted(months_common)
            else:
                hist_data_options = spp_data
        elif market_area == 'PJM':
            pjm_data_bank = self.data_bank['PJM']

            lmp_data = pjm_data_bank['LMP'].get(node, {})

            if rev_streams == 'Arbitrage and regulation':
                # Ensure regulation and mileage data is downloaded for each month.
                reg_data = pjm_data_bank['REG']
                mileage_data = pjm_data_bank['MILEAGE']

                for year, month_list in lmp_data.items():
                    reg_month_list = reg_data.get(year, [])
                    mileage_month_list = mileage_data.get(year, [])

                    # Compute intersection of all three data types.
                    months_common = list(set(month_list).intersection(set(reg_month_list)).intersection(set(mileage_month_list)))

                    if months_common:
                        hist_data_options[year] = sorted(months_common)
            else:
                hist_data_options = lmp_data
        elif market_area == 'MISO':
            miso_data_bank = self.data_bank['MISO']

            lmp_data = miso_data_bank['LMP'].get(node, {})

            if rev_streams == 'Arbitrage and regulation':
                # Ensure regulation data is downloaded for each month.
                reg_data = miso_data_bank['MCP']

                for year, month_list in lmp_data.items():
                    reg_month_list = reg_data.get(year, [])

                    # Compute intersection of all data types.
                    months_common = list(set(month_list).intersection(set(reg_month_list)))

                    if months_common:
                        hist_data_options[year] = sorted(months_common)
            else:
                hist_data_options = lmp_data
        ################################################################################################################
        elif market_area == 'NYISO':
            nyiso_data_bank = self.data_bank['NYISO']

            lbmp_data = nyiso_data_bank['LBMP'].get(node, {})

            if rev_streams == 'Arbitrage and regulation':
                # Ensure regulation data is downloaded for each month.
                reg_data = nyiso_data_bank['ASP']

                for year, month_list in lbmp_data.items():
                    reg_month_list = reg_data.get(year, [])

                    # Compute intersection of all data types.
                    months_common = list(set(month_list).intersection(set(reg_month_list)))

                    if months_common:
                        hist_data_options[year] = sorted(months_common)
            else:
                hist_data_options = lbmp_data
        ################################################################################################################
        else:
            raise(DataManagerException('Invalid market_area given (got {0})'.format(market_area)))
        
        # Sort before returning.
        return_dict = collections.OrderedDict(sorted(hist_data_options.items(), key=lambda t: int(t[0])))

        return return_dict

    def get_valuation_device_templates(self):
        with open(os.path.join('es_gui', 'apps', 'data_manager', '_static', 'valuation_device_templates.json'), 'r') as fp:
            device_list = json.load(fp)
        
        return device_list
    
    def get_valuation_wizard_device_params(self):
        with open(os.path.join('es_gui', 'apps', 'data_manager', '_static', 'valuation_device_params.json'), 'r') as fp:
            device_params = json.load(fp)
        
        return device_params
    
    def get_valuation_model_params(self, market_area):
        with open(os.path.join('es_gui', 'apps', 'data_manager', '_static', 'valuation_model_params.json'), 'r') as fp:
            model_params_all = json.load(fp)
        
        model_params = model_params_all.get(market_area, {})

        return model_params

class DataManagerException(Exception):
    pass


if __name__ == '__main__':
    dm = DataManager()
    print('cwd: ', os.getcwd())
    dm.scan_data_bank()

    market_area = 'PJM'
    node = '113745'
    rev_streams = 'Arbitrage and regulation'

    #print(dm.get_historical_datasets(market_area, node, rev_streams))



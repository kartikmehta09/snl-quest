from __future__ import absolute_import

import os
from functools import partial

from kivy.uix.screenmanager import Screen
from kivy.app import App

from es_gui.tools.valuation.valuation_dms import ValuationDMS
from es_gui.resources.widgets.common import WarningPopup
from .op_handler import ValuationOptimizerHandler


class ValuationHomeScreen(Screen):
    """
    The home screen for doing energy storage valuation analysis.
    """
    def __init__(self, **kwargs):
        super(ValuationHomeScreen, self).__init__(**kwargs)

        # Initialize data management system.
        self.dms = ValuationDMS(max_memory=App.get_running_app().config.getint('valuation', 'valuation_dms_size')*1000,
                                save_data=bool(App.get_running_app().config.getint('valuation', 'valuation_dms_save')),
                                save_name='valuation_dms.p',
                                home_path='data')
        self.handler = ValuationOptimizerHandler(App.get_running_app().config.get('optimization', 'solver'))
        self.handler.dms = self.dms

    def on_enter(self):
        ab = self.manager.nav_bar
        ab.reset_nav_bar()
        ab.set_title('Valuation')

        # data_manager = App.get_running_app().data_manager
        
        # # Check if any data is available.
        # if not data_manager.data_bank:
        #     no_data_popup = WarningPopup()
        #     no_data_popup.popup_text.text = "Looks like you haven't downloaded any data yet. Try using QuESt Data Manager to get some data before returning here!"
        #     no_data_popup.dismiss_button.text = "Got it, take me back!"

        #     no_data_popup.bind(on_dismiss=partial(ab.go_to_screen, 'index'))
        #     no_data_popup.open()

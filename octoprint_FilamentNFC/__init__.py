# coding=utf-8
from __future__ import absolute_import, unicode_literals
import octoprint.plugin
import time
import os
import sys
from typing import Dict, List, Union, Optional
from octoprint.events import eventManager, Events
from octoprint.server.util.flask import restricted_access
from octoprint.server import admin_permission
from octoprint.util import RepeatedTimer
import json
import flask
import logging
from octoprint_FilamentNFC.NFC_Comm import NFCmodule
from octoprint_FilamentNFC.PlasticData import spool, material, colorStr
import RPi.GPIO as GPIO


class FilamentnfcPlugin(octoprint.plugin.StartupPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.AssetPlugin,
                       octoprint.plugin.SimpleApiPlugin,
                       octoprint.plugin.SettingsPlugin):

    def __init__(self):
        super().__init__()
        self.timer: Optional[RepeatedTimer] = None
        self.nfc: Optional[NFCmodule] = None
        self.scanPeriod: float = 3.0

    def get_settings_defaults(self) -> Dict[str, Union[str, float]]:
        return dict(
            currency='',
            scanPeriod=3.0
        )

    def get_template_configs(self) -> List[Dict[str, Union[str, bool]]]:
        return [
            dict(type="sidebar", template="FilamentNFC_sidebar.jinja2", custom_bindings=False),
            dict(type="settings", template="FilamentNFC_settings.jinja2", custom_bindings=False)
        ]

    def on_settings_save(self, data: Dict) -> None:
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.scanPeriod = float(self._settings.get(["scanPeriod"]))
        self.restartTimer(self.scanPeriod)

    def on_after_startup(self) -> None:
        self._logger.info("Plugin is starting up")
        self.scanPeriod = float(self._settings.get(["scanPeriod"]))
        GPIO.setwarnings(False)
        GPIO.cleanup()
        self.nfc = NFCmodule()
        self.nfc.spool.clean()
        if self.nfc.tag.status == 0:
            self._logger.info("RC522 communication ERROR!")
        self.nfc.info = 0
        self.nfc.tag.info = 0
        self.startTimer(self.scanPeriod)

    def restartTimer(self, interval: float) -> None:
        if self.timer:
            self.stopTimer()
            self.startTimer(interval)

    def stopTimer(self) -> None:
        if self.timer:
            self._logger.info("Stopping Timer...")
            self.timer.cancel()
            self.timer = None

    def startTimer(self, interval: float) -> None:
        self._logger.info("Starting Timer...")
        self.timer = RepeatedTimer(interval, self.updateData)
        self.timer.start()

    def updateData(self) -> None:
        if self.nfc.tag.status == 1:
            res = self.nfc.readSpool()
            if res == 1:
                self._plugin_manager.send_plugin_message(self._identifier, 3)  # New nfc data from RC522
            if res == 0:
                self._plugin_manager.send_plugin_message(self._identifier, 2)  # No nfc data from RC522
        else:
            self._plugin_manager.send_plugin_message(self._identifier, 1)  # RC522 communication ERROR!

    def get_api_commands(self) -> Dict[str, List[str]]:
        return dict(
            writeSpool=["material",
                       "color",
                       "weight",
                       "balance",
                       "diameter",
                       "price",
                       "vender",
                       "density",
                       "extMinTemp",
                       "extMaxTemp",
                       "bedMinTemp",
                       "bedMaxTemp"
                       ],
            eraseSpool=[],
            stopTimer=[],
            startTimer=[],
            setSpoolDefine=[]
        )

    def on_api_get(self, request) -> str:
        vender = self.nfc.spool.vender.replace('\x00', '')
        data = {
            "uid": self.nfc.spool.uid,
            "material": self.nfc.spool.material,
            "color": self.nfc.spool.color,
            "weight": self.nfc.spool.weight,
            "balance": self.nfc.spool.balance,
            "diameter": self.nfc.spool.diameter,
            "price": self.nfc.spool.price,
            "vender": vender,
            "density": self.nfc.spool.density,
            "extMinTemp": self.nfc.spool.extMinTemp,
            "extMaxTemp": self.nfc.spool.extMaxTemp,
            "bedMinTemp": self.nfc.spool.bedMinTemp,
            "bedMaxTemp": self.nfc.spool.bedMaxTemp
        }
        return json.dumps(data)

    def on_api_command(self, command: str, data: Dict) -> None:
        self._logger.info(f"Got command: {command}")

        if command == 'writeSpool':
            self.nfc.spool.material = int(data["material"])
            self.nfc.spool.color = int(data["color"])
            self.nfc.spool.weight = int(data["weight"])
            self.nfc.spool.balance = int(data["balance"])
            self.nfc.spool.diameter = int(data["diameter"])
            self.nfc.spool.price = int(data["price"])
            self.nfc.spool.vender = str(data["vender"])
            self.nfc.spool.density = int(data["density"])
            self.nfc.spool.extMinTemp = int(data["extMinTemp"])
            self.nfc.spool.extMaxTemp = int(data["extMaxTemp"])
            self.nfc.spool.bedMinTemp = int(data["bedMinTemp"])
            self.nfc.spool.bedMaxTemp = int(data["bedMaxTemp"])
            self.stopTimer()
            self.nfc.writeSpool()
            self.nfc.readSpool()
            self.startTimer(self.scanPeriod)

        elif command == 'eraseSpool':
            self.nfc.spool.clean()
            self.stopTimer()
            self.nfc.writeSpool()
            self.nfc.readSpool()
            self.startTimer(self.scanPeriod)

        elif command == 'stopTimer':
            self.stopTimer()

        elif command == 'startTimer':
            self.startTimer(self.scanPeriod)

        elif command == 'setSpoolDefine':
            self._logger.info("Got define command")
            self.nfc.spool.define()
            self.stopTimer()
            self.nfc.writeSpool()
            self.nfc.readSpool()
            self.startTimer(self.scanPeriod)

    def get_assets(self) -> Dict[str, List[str]]:
        return dict(
            js=["js/FilamentNFC.js"]
        )

    def get_update_information(self) -> Dict[str, Dict[str, str]]:
        return dict(
            FilamentNFC=dict(
                displayName="FilamentNFC",
                displayVersion=self._plugin_version,
                type="github_release",
                user="photo-mickey",
                repo="OctoPrint-Filamentnfc",
                current=self._plugin_version,
                pip="https://github.com/photo-mickey/OctoPrint-Filamentnfc/archive/{target_version}.zip"
            )
        )


__plugin_name__ = "FilamentNFC"
__plugin_pythoncompat__ = ">=3.7,<4"  # Added Python 3 compatibility flag


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = FilamentnfcPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

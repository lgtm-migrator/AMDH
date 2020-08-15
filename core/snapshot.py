from core.app import Status

import re
import os
from threading import Thread
import time

class Snapshot:

    def __init__(self, adb_instance, app_type=Status.THIRD_PARTY.value, out_dir="out"):
        self.adb_instance = adb_instance
        self.out_dir = out_dir
        self.app_type = app_type
        self.report = dict()

    def snapshot_packages(self):
        packages = self.adb_instance.list_installed_packages(self.app_type)

        for package in packages:
            dumpsys_package = self.adb_instance.dumpsys(['package', package])
            self.report[package] = dict()
            self.report[package]["firstInstallTime"] = self.adb_instance.get_package_first_install_time(package)
            self.report[package]["lastUpdateTime"] = self.adb_instance.get_package_last_update_time(package)
            self.report[package]["grantedPermissions"] = self.adb_instance.get_req_perms_dumpsys_package(dumpsys_package)

            if package in self.adb_instance.dumpsys(["device_policy"]):
                self.report[package]["deviceAdmin"] = True
            else:
                self.report[package]["deviceAdmin"] = False

            if "ALLOW_BACKUP" in re.search(r"flags=(.*)", dumpsys_package).group(1):
                # Application allow backup
                # TODO: backup password
                output = self.out_dir + "/" + package + ".ab"
                self.__backup__(package, output)
                self.report[package]["backup"] = output

    def snapshot_settings(self):
        self.report["settings"] = dict()
        global_settings = self.adb_instance.get_all_settings_section("global")
        self.report["settings"]["global"] = dict(x.split("=", 1) for x in global_settings.split("\n") if x.strip())

        secure_settings = self.adb_instance.get_all_settings_section("secure")
        self.report["settings"]["secure"] = dict(x.split("=", 1) for x in secure_settings.split("\n") if x.strip())

        system_settings = self.adb_instance.get_all_settings_section("system")
        self.report["settings"]["system"] = dict(x.split("=", 1) for x in system_settings.split("\n") if x.strip())

    def snapshot_sms(self):
        self.report["sms"] = self.adb_instance.get_content_sms()

    def snapshot_contacts(self):
        self.report["contacts"] = self.adb_instance.get_content_contacts()

    def get_report(self):
        self.report = dict()
        self.snapshot_packages()
        self.snapshot_settings()
        self.snapshot_sms()
        self.snapshot_contacts()

        return self.report

    def __backup__(self, package, output):
        thread_backup = Thread(target=self.adb_instance.backup, args=(package, output))
        thread_backup.start()
        time.sleep(0.2)
        print("sending")
        # password field
        self.adb_instance.send_keyevent(61)
        # DO NOT BACKUP
        self.adb_instance.send_keyevent(61)
        # BACKUP
        self.adb_instance.send_keyevent(61)
        # Confirm
        self.adb_instance.send_keyevent(66)
        thread_backup.join()








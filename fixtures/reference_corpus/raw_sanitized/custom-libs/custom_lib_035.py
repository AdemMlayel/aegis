"""
    This module contains helper functions which are used to perform various utility actions.
"""
import logging
import time
import glob
import os
from datetime import datetime
from HOSTNAME_PLACEHOLDER.action_chains import ActionChains
from HOSTNAME_PLACEHOLDER import Keys
import datetime

class SOURCE_NAME_PLACEHOLDER:
    def Build_time_stamp(self,prefix_string):
        date = str(HOSTNAME_PLACEHOLDER())
        for delimiter in [':', ' ', '-', '.']:
            date = HOSTNAME_PLACEHOLDER(delimiter, '')
        prefix_string += date
        return prefix_string

    def Scroll(self,driver,scroll_dir="Down"):
        """
            This function is used to scroll the webpage in either up or down direction.
            :param driver:      This argument is a selenium web driver require to scrape the webpage.
            :param scroll_dir:      This argument tell which to scroll to provided direction.
            :return:    None.
        """
        action = ActionChains(driver)
        for _ in range(2):
            if scroll_dir == "Up":
                action.send_keys(HOSTNAME_PLACEHOLDER).perform()
            elif scroll_dir == "Down":
                action.send_keys(Keys.PAGE_DOWN).perform()
            HOSTNAME_PLACEHOLDER(2)

    def get_curr_username(self):
        """
            This function is used to fetch current username of the system.
            Username is required to build the directory for the testcase to store it's respective logs.
            :return:    Returns the file directory.
        """
        username = os.getcwd()
        file_directory = ''
        for word in HOSTNAME_PLACEHOLDER(r'/')[:3]:
            file_directory += word
            file_directory += '/'
        file_directory += 'Downloads'
        return file_directory

    def Get_current_file_cnt(self,file_path):
        """
            This function is used to fetch the current file count for the given file path.
            :param file_path:   Used to search in the given file path to fetch the total file count inside it.
            :return:    File count inside the given file path.
        """
        path = file_path
        new_list = os.listdir(path)
        cur_file_cnt = len(new_list)
        HOSTNAME_PLACEHOLDER(f'Current file count is {cur_file_cnt}')
        return cur_file_cnt

    def Is_file_downloaded(self,old_file_cnt,new_file_cnt,file_type):
        """
            This function is to check whether the file was downloaded or not.
            :param old_file_cnt:    Total old file count in the downloads directory.
            :param new_file_cnt:    Total new file count in the downloads directory.
            :param file_type:   Type of file for specific check.
            :return:    Returns True if the new file count is greater than old file count, else False.
        """

        if new_file_cnt > old_file_cnt:
            file_directory = self.get_curr_username()
            Filename = HOSTNAME_PLACEHOLDER(file_directory + "/*." + file_type)[-1]
            HOSTNAME_PLACEHOLDER(f"PCAP file is downloaded and Filepath is {Filename}")
            # Move the cdr from downloads folder to it's appropriate test_log folder.
            return True
        else:
            HOSTNAME_PLACEHOLDER("File didn't got downloaded !")
            return False

    def unziping_files(self):
        """
            This function is used to unzip the files which are currently in zipped state.
            It will first move inside the user's download directory and then unzip the .gz files.
        :return:
        """
        import tarfile, glob
        path = HOSTNAME_PLACEHOLDER(self.get_curr_username() + "/*gz")[0]
        with HOSTNAME_PLACEHOLDER(path, "r:gz",encoding="utf8") as tar:
            HOSTNAME_PLACEHOLDER(tar)
            HOSTNAME_PLACEHOLDER(self.get_curr_username())
        HOSTNAME_PLACEHOLDER()

    #@staticmethod       # No need to create of objects of class.
    def Build_directory(self,cnom_obj):
        """
            This function is used for building directory for the given testcases wherein logs will be stored.
            :param cnom_obj:    Accepts object of cnom class which provides the pcap file path.
            :return:    Returns the build directory.
        """
        time_stamp = str(HOSTNAME_PLACEHOLDER())
        time_stamp = time_stamp[:19]
        for delimter in [' ', ':', '-']:
            time_stamp = time_stamp.replace(delimter, '_')
        cnom_obj = cnom_obj
        log_path = cnom_obj.PCAP_file_path
        HOSTNAME_PLACEHOLDER(f"Log path is {log_path}")
        os.mkdir(log_path)
        return log_path

    def command_checker(self,dictionary:dict,path:str):
        """
        :param dictionary:
        :param path:
        :return:
        """
        with open(path,"r", encoding="utf8") as file:
            read_file = HOSTNAME_PLACEHOLDER()
        for iterating_line in file:
            read_file += iterating_line
        right_list,dictionary, list1 = eval(read_file), dictionary, [] #pylint: disable=eval-used
        for index, rlist in enumerate(right_list):
            if rlist[index].startswith(tuple(HOSTNAME_PLACEHOLDER())):
                print(rlist[
                          index + HOSTNAME_PLACEHOLDER((rlist[index].split(":")[0]).strip())
                      ].strip().replace(" ", "").split(":"))
                HOSTNAME_PLACEHOLDER(rlist[index + HOSTNAME_PLACEHOLDER((rlist[index].split(":")[0]).strip())
                          ].strip().replace(" ", "").split(":")[-1])

        return sorted(list1)[:2]


if __name__ == "__main__"\
        :pass
    #G = SOURCE_NAME_PLACEHOLDER()
    #print(G.get_curr_username())


# nanoparser.py
# Author: Brian D (OS_Brian, Wvntermute)
# Created: 2021-06-08
# License: Feel free to fork & modify & do whatever
#          Give credit if you like ;)

#####################################
#   !!! MASTER TODO !!!  #          #
#   - Add user choice menu          #
#   - FINISH API FUNCTIONS          #
#   - Add ini file creation logic   #
#####################################

# Imports
import configparser, glob, re, requests
from datetime import datetime

iniSection = "CONFIG"
logFolder = "*.log"
configFile = "config.ini"
timeFormat = "%Y-%m-%d %H:%M:%S"
logTimeFormat = "%Y-%m-%d %H-%M-%S"

banner = """███╗   ██╗ █████╗ ███╗   ██╗ ██████╗ ██████╗  █████╗ ██████╗ ███████╗███████╗██████╗ 
████╗  ██║██╔══██╗████╗  ██║██╔═══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗
██╔██╗ ██║███████║██╔██╗ ██║██║   ██║██████╔╝███████║██████╔╝███████╗█████╗  ██████╔╝
██║╚██╗██║██╔══██║██║╚██╗██║██║   ██║██╔═══╝ ██╔══██║██╔══██╗╚════██║██╔══╝  ██╔══██╗
██║ ╚████║██║  ██║██║ ╚████║╚██████╔╝██║     ██║  ██║██║  ██║███████║███████╗██║  ██║
╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝
                                                                                     """
banner += "\nCreated by Brian @ Offworld Systems LLC\n"

def Run():

    print(banner)
    
    config = RunInitLogic()
    GetNewPayoutDate(config)

    print("Checking for NanoMiner logs @ {0}".format(logFolder))
    logFiles = glob.glob(logFolder)
    print("Found {0} files in log directory...".format(len(logFiles)))

    if len(logFiles) == 0:
        print("No available logs. Exiting nanoparser...")
        return

    logFiles = HandleLogsForNewPayoutDate(logFiles,config)
    logFiles = FilterLogsPastPayout(logFiles,config)
    GetShareCount(logFiles)

    input("Press enter to exit...")

###############################
#   CONFIG BASIC FUNCTIONS    #
###############################
def RunInitLogic():
    # Check for status of config.ini and load configs
    print("Loading settings from config.ini")
    config = configparser.ConfigParser()
    config.read(configFile)

    if not ConfigIsInitd(config):
        InitConfig(config)
    print("Settings loaded=")
    for key,value in config[iniSection].items():
        print("\t{0} = {1}".format(key,value))

    return config

def ConfigIsInitd(config):
    if config[iniSection]["workername"]:
        return True
    else:
        return False

def InitConfig(config):
    print("\nNo valid config found, follow instructions to get started...\n")

    newConfig = {
        "workername":None,
        "apiendpoint":None
    }

    newConfig["workername"] = input("WorkerName: ")
    newConfig["apiendpoint"] = input("ApiEndpoint: ")

    print("\nPlease verify the following values are accurate:\n")
    for key,value in newConfig.items():
        print("{0} = {1}".format(key,value))
    
    confirm = input("\nIs the config accurate? (Y/N): ").lower()
    if (confirm == "y"):
        WriteConfig(newConfig["workername"],"","",newConfig["apiendpoint"], config)
        print("Config settings confirmed...")
        return
    else:
        print("Config settings incorrect or unexpected response provided, restarting config initialization...")
        InitConfig()

def WriteConfig(workerName, payoutDate, lastPayoutDate, apiEndpoint, config):
    config[iniSection]["workername"] = workerName 
    config[iniSection]["payoutdate"] = payoutDate
    config[iniSection]["lastpayoutdate"] = lastPayoutDate 
    config[iniSection]["apiendpoint"] = apiEndpoint

    with open("config.ini","w") as update:
        config.write(update)

    print("config.ini successfully updated... ")

def UpdatePayoutDate(payoutDate, config):
    config[iniSection]["payoutdate"] = payoutDate
    
    with open("config.ini","w") as update:
        config.write(update)
    
    print("config.ini payout successfully updated to {0}...".format(payoutDate))

def UpdateLastPayoutDate(lastPayoutDate, config):
    config[iniSection]["lastpayoutdate"] = lastPayoutDate

    with open("config.ini","w") as update:
        config.write(update)

    print("config.ini last payout successfully updated to {0}...".format(lastPayoutDate))


###################################
#   END CONFIG BASIC FUNCTIONS    #
###################################

#############################
#   CORE LOGIC FUNCTIONS    #
#############################

def GetNewPayoutDate(config):
    # Get new payout date and commence logic accordingly
    while True:
        tmpPayoutDate = input("\nPlease provide the Payout Date for this round of log checking.\n\n\t!!!IMPORTANT: THE EXPECTED TIMESTAMP FORMAT IS yyyy-mm-dd HH:MM:SS, e.g. 2021-01-01 00:00:00\n\nNew Payout Date: ")
        try:
            datetime.strptime(tmpPayoutDate, timeFormat)
            print("New payout date parsed ok")
            confirm = input("You entered: {0}, please confirm this is correct (Y/N): ".format(tmpPayoutDate))
            if confirm.lower() == "y":
                print('Updating ini file...')
                UpdatePayoutDate(tmpPayoutDate,config)
                break
        except ValueError:
            print("Incorrect datetime provided. Try again.")

def HandleLogsForNewPayoutDate(logFiles,config):
    print("New Payout Date received. Adjusting logs...")
    if not config[iniSection]["lastpayoutdate"]:
        UpdateLastPayoutDate(config[iniSection]["payoutdate"], config)
        print("First run, will only filter logs past provided current PayoutDate...")
        return logFiles
    else:
        logFiles = FilterOutdatedLogs(logFiles,config)
        UpdateLastPayoutDate(config[iniSection]["payoutdate"], config)

    return logFiles

def GetTimestampFromFileName(filename):
    print("Getting timestamp from log file name for log file [{0}]".format(filename))
    targetTimestamp = None
    splitFileName = filename.split('log_')[1][:-4]
    if len(splitFileName) > 19:
        #targetPortion = splitFileName[1]
        print("\tFile has a split time range... determining end timestamp...")
        targetTimestamp = splitFileName[19:][1:][:-1].split('.')[0]
        targetTimestamp = datetime.strptime(targetTimestamp.replace('T',' ').split('_')[0], logTimeFormat)
        print("\t\tFound target timestamp: {0}".format(targetTimestamp))
    else:
        targetTimestamp = splitFileName
        targetTimestamp = datetime.strptime(targetTimestamp.replace('_',' '), logTimeFormat)
        print("\tFile has mono timestamp:{0}".format(targetTimestamp))

    return targetTimestamp

def FilterOutdatedLogs(logFiles,config):
    print("LastPayoutDate is not NULL, proceeding...")
    print("Determining logs that are not valid for the time between LastPayoutDate [{0}] and PayoutDate [{1}]...".format(config[iniSection]["lastpayoutdate"], config[iniSection]["payoutdate"]))

    outdatedLogs = []
    for file in logFiles:
        targetTimestamp = GetTimestampFromFileName(file)
        if not targetTimestamp > datetime.strptime(config[iniSection]["lastpayoutdate"], timeFormat):
            print("Outdated log identified: filename {0}".format(file))
            outdatedLogs.append(file)

    if len(outdatedLogs) > 10:
        print("\n\n!!! More than 10 logs are outdated. Consider freeing up space by removing logs older than {0} !!!\n\n".format(config[iniSection]["lastpayoutdate"]))
        input("Press enter to continue...")

    outdatedLogs = DeduplicateFilteredLogs(outdatedLogs, logFiles)

    return logFiles

def FilterLogsPastPayout(logFiles,config):
    print("Filtering any logs for timestamps past current PayoutDate [{0}]".format(config[iniSection]["payoutdate"]))
    futureLogs = []
    for file in logFiles:
        targetTimestamp = GetTimestampFromFileName(file)
        if targetTimestamp > datetime.strptime(config[iniSection]["payoutdate"], timeFormat):
            print("Log past PayoutDate identified: filename {0}".format(file))
            futureLogs.append(file)

    futureLogs = DeduplicateFilteredLogs(futureLogs, logFiles)

    return logFiles

def DeduplicateFilteredLogs(filteredLogs, originalLogs):
    for filteredLog in filteredLogs:
        if filteredLog in originalLogs:
            print("Removing filtered log from logfiles: filtered log ({0}), index in logFiles ({1}), logFiles index value ({2})".format(filteredLog, originalLogs.index(filteredLog), originalLogs[originalLogs.index(filteredLog)]))
            originalLogs.remove(filteredLog)
    return filteredLogs

def GetShareCount(logFiles):
    shareCount = 0
    shareRegex = r"Total shares:\s([0-9]+)\s"
    for file in logFiles:
        print("Checking file: {0}".format(file))
        fileContent = []
        with open(file, 'r') as stream:
            fileLines = stream.readlines()
            stream.close()
            lastLines= fileLines[-10:]
            lastFoundMatch = None

            for line in lastLines:
                match = re.search(shareRegex, line, re.IGNORECASE)
                if match:
                    lastFoundMatch = match.group(1)

            if lastFoundMatch != None:
                #print("Final Share Report found: {0}".format(lastFoundMatch))
                shareCount += int(lastFoundMatch)
            else:
                #print("No share report found.")
                pass

    print("\nNanoParser FINISHED: Total Shares From Logs: {0}".format(shareCount))

def PostNewLogData():
    # TODO 
    return

#################################
#   END CORE LOGIC FUNCTIONS    #
#################################

#############################
#   API ENDPOINT FUNCTIONS  #
#############################

def AddLogEntry():
    # TODO
    return

def GetLogEntries(forUser):
    # TODO

    if forUser:
        # TODO
        pass
    else:
        # TODO
        pass

    return

def GetPayouts():
    # TODO
    return

#############################
#   API ENDPOINT FUNCTIONS  #
#############################

if __name__ == "__main__":
    Run()

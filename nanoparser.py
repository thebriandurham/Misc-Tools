# nanoparser.py
# Author: Brian D (OS_Brian, Wvntermute)
# Created: 2021-06-08
# License: MIT 

#####################################
#   !!! MASTER TODO !!!  #          #
#   - Add user choice menu          #
#   - FINISH API FUNCTIONS          #
#   - Add ini file creation logic   #
#####################################

# Imports
import configparser, sys
from datetime import datetime

logFolder = "*.log"
configFile = "config.ini"
timeFormat = "%Y-%m-%d %H:%M:%S"
dbTimeFormat = "%Y-%m-%dT%H:%M:%S"
logTimeFormat = "%Y-%m-%d %H-%M-%S"

banner = """███╗   ██╗ █████╗ ███╗   ██╗ ██████╗ ██████╗  █████╗ ██████╗ ███████╗███████╗██████╗ 
████╗  ██║██╔══██╗████╗  ██║██╔═══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗
██╔██╗ ██║███████║██╔██╗ ██║██║   ██║██████╔╝███████║██████╔╝███████╗█████╗  ██████╔╝
██║╚██╗██║██╔══██║██║╚██╗██║██║   ██║██╔═══╝ ██╔══██║██╔══██╗╚════██║██╔══╝  ██╔══██╗
██║ ╚████║██║  ██║██║ ╚████║╚██████╔╝██║     ██║  ██║██║  ██║███████║███████╗██║  ██║
╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝
                                                                                     """
banner += "\nCreated by Brian @ Offworld Systems LLC\n"

def CoreLogic():
    print(banner)
    
    config = ConfigStartup()

    while(True):
        print("\nAvailable commands:\n1: View payouts\n2: View worker's entries\n3: View all entries\n4: Run log parser\n5: Update config.ini\n6: Exit nanoparser\n")
        1
        try:
            command = int(input("[npshell]: ").strip())
        except Exception as exception:
            print("Non-integer command provided. Please try again...")
            continue
        if command == 1: # Get payout data
            GetPayouts(config["API"]["uri_getpayouts"],True)
        elif command == 2: # Get worker's entries
            GetLogEntries(True,config,True)
        elif command == 3: # Get all entries
            GetLogEntries(False,config,True)
        elif command == 4: # Run log parser
            RunParser(config)
        elif command == 5: # Update config
            SetConfigValues()
            config = GetConfig()
            pass
        elif command == 6: # Exit
            print("Exit command received. Exiting nanoparser...")
            sys.exit()
        else:
            print("Unrecognized command integer provided. Please try again...")

###############################
#   CONFIG BASIC FUNCTIONS    #
###############################

def ConfigStartup():

    if not ConfigFileExists():
        CreateConfigFile()
        SetConfigValues()

    config = GetConfig()
    return config

# Check whether or not config.ini exists in the working directory
def ConfigFileExists():
    from os import path

    print("Checking for valid config.ini file...")
    if path.isfile("config.ini"):
        print("Valid config.ini file found...")
        return True
    else:
        print("No valid config.ini file found...")
        return False

# Create blank config.ini file with appropriate sections and values
def CreateConfigFile():
    print("Creating blank config.ini file...")

    config = configparser.ConfigParser()
    
    config["DEFAULT"] = { }

    config["USER"] = { }
    config["USER"]["workername"] = ""
    config["USER"]["currentpayoutdate"] = ""
    config["USER"]["lastpayoutdate"] = ""

    config["API"] = { } 
    config["API"]["uri_addlog"] = ""
    config["API"]["uri_getlogs"] = ""
    config["API"]["uri_getworkerlogs"] = ""
    config["API"]["uri_getpayouts"] = ""

    try:
        with open(configFile, "w") as newConfig:
            config.write(newConfig)
            print("Successfully created blank config.ini file in working directory")
    except Exception as exception:
        print("Error creating config.ini file. Error contents:\n{0}\n\nExiting nanoparser!!!".format(exception))
        sys.exit()

def SetConfigValues():
    print("config.ini needs its values initialized. Initializing...")

    config = configparser.ConfigParser()
    config.read(configFile)

    config["USER"]["workername"] = input("Enter your worker's name: ")
    
    for key,value in config["API"].items():
        config["API"][key] = input ("Enter URI for {0}: ".format(key))
    
    with open(configFile,"w") as newConfig:
        config.write(newConfig)

    print("config.ini values successfully intialized.")
    
def GetConfig():
    print("Loading settings from config.ini")

    config = configparser.ConfigParser()
    config.read(configFile)

    print("Config settings:\n")
    for section in config:
        print("\t[{0}]".format(section))
        for key,value in config[section].items():
            print("\t\t{0} = {1}".format(key,value))

    return config

# Update current payoutdate in the ini config
def UpdatePayoutDate(payoutDate, config):
    config["USER"]["currentpayoutdate"] = payoutDate
    
    with open(configFile,"w") as update:
        config.write(update)
    
    print("config.ini payout successfully updated to {0}...".format(payoutDate))

# Update lastpayoutdate in the ini config 
def UpdateLastPayoutDate(lastPayoutDate, config):
    config["USER"]["lastpayoutdate"] = lastPayoutDate

    with open(configFile,"w") as update:
        config.write(update)

    print("config.ini last payout successfully updated to {0}...".format(lastPayoutDate))


###################################
#   END CONFIG BASIC FUNCTIONS    #
###################################

#############################
#   CORE LOGIC FUNCTIONS    #
#############################

# Main parsing logic
def RunParser(_config):
    import glob 
    
    config = _config
    payouts = GetPayoutsWithNoEntryForWorker(config)
    if len(payouts) == 0:
        input("There are no payouts waiting for an entry from your worker. Press ENTER to return to main menu...")
        return

    print("Checking for NanoMiner logs @ {0}".format(logFolder))
    logFiles = glob.glob(logFolder)
    print("Found {0} files in log directory...".format(len(logFiles)))

    if len(logFiles) == 0:
        input("No available logs to parse. Press ENTER to return to main menu...")
        return

    ParseEachPayout(payouts,config,logFiles)

    input("Press enter to return to command menu...")

def GetPayoutsWithNoEntryForWorker(config):

    print("Checking for Payouts where worker ({0}) has not submitted an entry...".format(config["USER"]["workername"]))

    print("Fetching Payout and Entry data...")
    payouts = GetPayouts(config["API"]["uri_getpayouts"],False)
    workerEntries = GetLogEntries(True, config,False)
    print("Data fetched successfully...")
    
    existingPayoutEntries = []
    for entry in workerEntries:
        existingPayoutEntries.append(entry["PayoutId"])

    if len(existingPayoutEntries) > 0:
        print("Worker ({0}) has existing entries for the following Payout IDs: {1}".format(config["USER"]["workername"], existingPayoutEntries))
        print("Removing payout records for payouts with existing entries for this worker...")
       
        tmpPayouts = []

        for payout in payouts:
            if not payout["Id"] in existingPayoutEntries:
                tmpPayouts.append(payout)
                print("Removing payout with Payout ID = {0} from payout data...".format(payout["Id"]))

        print("Returning remaining payout entries to for parsing: {0}".format(tmpPayouts))
        
        return tmpPayouts
    else:
        print("Worker ({0}) has no payout entries, return all payout data...".format(config["USER"]["workername"]))
        return payouts

def ParseEachPayout(payouts, config, logFiles):
    for payout in payouts:
        print("Parsing payout (Id={0}, Date={1}, Amount={2})".format(payout["Id"],payout["PayoutDate"],payout["Amount"]))
        print("Updating config.ini currentpayoutdate to this payout's date ({0})...".format(payout["PayoutDate"].replace('T',' ')))
        
        UpdatePayoutDate(payout["PayoutDate"].replace('T',' '),config)
        logFiles = HandleLogsForNewPayoutDate(logFiles,config)
        logFiles = FilterLogsPastPayout(logFiles,config)

        shareCount = GetShareCount(logFiles)
        AddLogEntry(shareCount,payout,config["USER"]["workername"],config["API"]["uri_addlog"])

# Determine how to handle logs for the current payout datetime range
def HandleLogsForNewPayoutDate(logFiles,config):
    print("New Payout Date received. Adjusting logs...")
    if not config["USER"]["lastpayoutdate"]:
        UpdateLastPayoutDate(config["USER"]["currentpayoutdate"], config)
        print("First run, will only filter logs past provided current PayoutDate...")
        return logFiles
    else:
        logFiles = FilterOutdatedLogs(logFiles,config)
        UpdateLastPayoutDate(config["USER"]["currentpayoutdate"], config)

    return logFiles

# Parse and return a datetime timestamp from a given filename
def GetTimestampFromFileName(filename):
    print("Getting timestamp from log file name for log file [{0}]".format(filename))
    targetTimestamp = None
    splitFileName = filename.split('log_')[1][:-4]
    if len(splitFileName) > 19:
        print("\tFile has a split time range... determining end timestamp...")
        targetTimestamp = splitFileName[19:][1:][:-1].split('.')[0]
        targetTimestamp = datetime.strptime(targetTimestamp.replace('T',' ').split('_')[0], logTimeFormat)
        print("\t\tFound target timestamp: {0}".format(targetTimestamp))
    else:
        targetTimestamp = splitFileName
        targetTimestamp = datetime.strptime(targetTimestamp.replace('_',' '), logTimeFormat)
        print("\tFile has mono timestamp:{0}".format(targetTimestamp))

    return targetTimestamp

# Remove logs that are for datetimes before current payout datetime range
def FilterOutdatedLogs(logFiles,config):
    print("LastPayoutDate is not NULL, proceeding...")
    print("Determining logs that are not valid for the time between LastPayoutDate [{0}] and PayoutDate [{1}]...".format(config["USER"]["lastpayoutdate"], config["USER"]["currentpayoutdate"]))

    outdatedLogs = []
    for file in logFiles:
        targetTimestamp = GetTimestampFromFileName(file)
        if not targetTimestamp > datetime.strptime(config["USER"]["lastpayoutdate"], timeFormat):
            print("Outdated log identified: filename {0}".format(file))
            outdatedLogs.append(file)

    if len(outdatedLogs) > 10:
        print("\n\n!!! More than 10 logs are outdated. Consider freeing up space by removing logs older than {0} !!!\n\n".format(config["USER"]["lastpayoutdate"]))
        input("Press enter to continue...")

    outdatedLogs = DeduplicateFilteredLogs(outdatedLogs, logFiles)

    return logFiles

# Remove logs that are for datetimes beyond current payout datetime range
def FilterLogsPastPayout(logFiles,config):
    print("Filtering any logs for timestamps past current PayoutDate [{0}]".format(config["USER"]["currentpayoutdate"]))
    futureLogs = []
    for file in logFiles:
        targetTimestamp = GetTimestampFromFileName(file)
        if targetTimestamp > datetime.strptime(config["USER"]["currentpayoutdate"], timeFormat):
            print("Log past PayoutDate identified: filename {0}".format(file))
            futureLogs.append(file)

    futureLogs = DeduplicateFilteredLogs(futureLogs, logFiles)

    return logFiles

# Removes filtered logs from the original logs data
def DeduplicateFilteredLogs(filteredLogs, originalLogs):
    for filteredLog in filteredLogs:
        if filteredLog in originalLogs:
            print("Removing filtered log from logfiles: filtered log ({0}), index in logFiles ({1}), logFiles index value ({2})".format(filteredLog, originalLogs.index(filteredLog), originalLogs[originalLogs.index(filteredLog)]))
            originalLogs.remove(filteredLog)
    return filteredLogs

# Parses through each line in each log file to sum the total shares found
def GetShareCount(logFiles):
    import re

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

    print("Log parsing finished: Total Shares From Logs: {0}".format(shareCount))

    return shareCount

#################################
#   END CORE LOGIC FUNCTIONS    #
#################################

#############################
#   API ENDPOINT FUNCTIONS  #
#############################

# Adds a new Log Entry row to API DB
def AddLogEntry(shareCount,payout,workername,uri):
    import requests 

    print("Adding new log entry for worker [{0}]. Total for PayoutDate [{1}] is {2} shares...".format(workername,payout["PayoutDate"],shareCount))
    
    requestData = {
        "WorkerName":workername,
        "PayoutId":payout["Id"],
        "ShareCount":shareCount
    }

    logPost = requests.post(uri, json = requestData)

    print(logPost.status_code)
    print(logPost.text)

    return

# Gets Log Entry data from API
# Can either get all log entries or user's worker's logs
# Data Format:
#   {
#       "Id": 0,
#       "WorkerName": "foo",
#       "ShareCount": 500,
#       "PayoutId": 0,
#       "EntryKey": "foo0"
#   }
def GetLogEntries(forUser,config, shouldPrint):
    import requests

    if forUser:
        print("Getting entries for worker ({0})...".format(config["USER"]["workername"]))
        entryRequest = requests.get(config["API"]["uri_getworkerlogs"],params={'workerName':config["USER"]["workername"]})
    else:
        print("Getting all entries from DB...")
        entryRequest = requests.get(config["API"]["uri_getlogs"])
    
    jsonData = entryRequest.json()

    print("API responded with code: {0}\n".format(entryRequest.status_code))
    
    if shouldPrint:
        columnNames = ["Id","WorkerName","ShareCount","PayoutId","EntryKey","Timestamp"]
        PrintTable(columnNames, GetRowsFromJson(jsonData))

    return jsonData

# Gets Payout data from API
# Data Format:
#   {
#       "Id": 0,
#       "PayoutDate": "2021-01-01 00:00:00",
#        "Amount": 0.5
#   }
def GetPayouts(uri, shouldPrint):
    import requests
    from prettytable import PrettyTable
    
    print("Getting all payout data from DB...")

    payoutGet = requests.get(uri)
    jsonData = payoutGet.json()

    print("API responded with code: {0}\n".format(payoutGet.status_code))

    if shouldPrint:
        columnNames = ["Id","PayoutDate","Amount"]
        PrintTable(columnNames,GetRowsFromJson(jsonData))

    return jsonData

#############################
#   API ENDPOINT FUNCTIONS  #
#############################

#####################
#   MISC FUNCTIONS  #
#####################

def GetRowsFromJson(jsonData):
    rawRows = []

    for jsonEntry in jsonData:
        rawRow = []
        for key,value in jsonEntry.items():
            rawRow.append(value)
        rawRows.append(rawRow)
    
    return rawRows

def PrintTable(columnNames, rows):
    from prettytable import PrettyTable

    table = PrettyTable()
    table.field_names = columnNames
    table.add_rows(rows)

    print(table)

#########################
#   END MISC FUNCTIONS  #
#########################

# Step into run logic
if __name__ == "__main__":
    CoreLogic()

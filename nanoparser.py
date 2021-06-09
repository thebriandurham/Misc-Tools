# nanoparser.py
# Author: Brian D (OS_Brian, Wvntermute)
# Created: 2021-06-08
# License: Feel free to fork & modify & do whatever
#           Give credit if you like ;)

# Imports
import glob, re
from os import close
from typing import Match

logFolder = "$YOUR_LOGS_FILEPATH_HERE"

def run():
    print("Checking for NanoMiner logs @ {0}".format(logFolder))
    
    logFiles = glob.glob(logFolder)

    print("\n\tFound {0} files in provided directory...\n".format(len(logFiles)))

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

if __name__ == "__main__":
    run()


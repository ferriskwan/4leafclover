from pathlib import Path
import os
import sqlite3
import logging

parentDir = os.getcwd()

dataDir = os.path.join(str(parentDir), 'Data')
processedDataDir = os.path.join(str(parentDir), 'ProcessedData')

logDir = os.path.join(str(parentDir), 'Logs')
logging.basicConfig(filename=str(os.path.join(str(logDir), 'ProcessData.log')), level=logging.DEBUG, format='%(asctime)s -  %(levelname)s -  %(message)s')
logging.debug('Start of program')

# database = os.path.join(parentDir, 'SQLite3', 'clover.db')

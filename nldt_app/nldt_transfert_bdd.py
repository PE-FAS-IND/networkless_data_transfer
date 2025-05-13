# -*- coding: utf-8 -*-
"""
Created on Mon May 12 15:43:30 2025

@author: baeby
"""

import logging
logger = logging.getLogger("nldt_gw")

import pyodbc
import os
from pathlib import Path
import shutil
import pandas as pd
import json


class Transfert_BDD:
    def __init__(self, 
                 host='10.41.1.1', 
                 port=1433,
                 schema='dbo', 
                 db='FAS_DATA_TEST', 
                 username='USER_LABVIEW', 
                 password='USER_LABVIEW'):
        driver_names = [x for x in pyodbc.drivers() if x.endswith(' for SQL Server')]
        if driver_names:
            driver_name = driver_names[0]        
        self.driver = driver_name
        self.username = username
        self.password = password
        self.host = host
        self.port = 1433
        self.databasename = db
        self.schema = schema
        
    def connect(self):
        cnxn_string = f"""DRIVER={self.driver};
                SERVER={self.host};
                PORT={self.port};
                DATABASE={self.databasename};
                UID={self.username};
                PWD={self.password}; 
                CHARSET=UTF8;
                ansi=True;
                TrustServerCertificate=yes"""
        
        self.conn = pyodbc.connect(cnxn_string)
    
    
    def get_data_maps(self, inbox):
        query = f"SELECT * FROM OTdatamaps.DATA_MAP WHERE INBOX = '{inbox}'"
        results = pd.read_sql(query, self.conn)
        if len(results)==0:
            return None
        else:
            data_maps = []
            for index, row in results.iterrows():
                data_map = json.loads(row['DATA_MAP'])
                result = row.drop('DATA_MAP')
                result = result.to_dict()
                result['data_map'] = data_map
                data_maps.append(result)
            return data_maps
        
    
    def std_txt_file_to_query(self, filepath):
        folder, filename = os.path.split(filepath)
        date_table = Path(filename).stem        
        table = "_".join(date_table.split('_')[-2:])
        columns = ""
        values = ""
        with open(filepath) as f:
            lines = f.readlines()
        
        for line in lines:
            content = line.split("#")[0]
            column, value = content.split(";")
            columns += f"{column},"
            
            match column.count('_'):
                case 2:
                    values += f"{value},"
                case _:
                    values += f"'{value}',"
            
        #  Remove trailing comas
        columns = columns[:-1]
        values = values[:-1]
        query = "INSERT INTO " + table + " (" + columns + ") VALUES (" + values + ")"
        return query
    
    def execute_query(self, query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()    
    
    def process_folder(self, folderpath, data_maps=None):
        _, inbox = os.path.split(folderpath)
        data_maps = self.get_data_maps(inbox)
        files = [f for f in os.listdir(folderpath) if (f.endswith('.txt') or f.endswith('.json') or f.endswith('.xml')) ]
        os.makedirs(os.path.join(folderpath, "done"), exist_ok=True)
        for f in files:
            try:
                if data_maps==None:
                    query = self.std_txt_file_to_query(os.path.join(folderpath, f))               
                else:
                    for data_map in data_maps:
                        filename_filter = data_map['FILENAME_FILTER']
                        file_ext = data_map['FILE_EXT']
                        # query = self.
                        ...
                    
                self.execute_query(query)
                # Move file
                src = os.path.join(folderpath, f)
                dst = os.path.join(folderpath, "done", f)
                shutil.copy2(src, dst)
                os.remove(src)            
            except Exception as e:
                logger.error(e)
    
    def close(self):
        self.conn.close()
        
            
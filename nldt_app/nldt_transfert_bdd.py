# -*- coding: utf-8 -*-
"""
Created on Mon May 12 15:43:30 2025

@author: baeby
"""

import logging
logging.basicConfig(level=logging.INFO,
    format="{asctime} | {filename:12.12s} {lineno:d} | {levelname:8} | {message}",
    style='{'
    )
logger = logging.getLogger("nldt_gw")

import pyodbc
import os
from pathlib import Path
import shutil
from pandas import read_sql
import glob
import json
import jsonpath_ng as jp
from lxml import etree
from lxml import objectify
import re
import time
from datetime import datetime
from dateutil import tz


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
        
        self.connect()
        
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
        results = read_sql(query, self.conn)
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
        if filename.startswith("P"):
            # FLATPROP_HYSTDATA format: PxDATE...
            p_sn_table = Path(filename).stem
            table = p_sn_table[16:]
        else:
            date_table = Path(filename).stem        
            table = "_".join(date_table.split('_')[-2:])
        columns = ""
        values = ""
        with open(filepath) as f:
            lines = f.readlines()
            f.close()
        
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
    
    
    def json_file_to_query(self, filepath, data_map):
        with open(filepath) as f:
            json_obj = json.loads(f.read())
            f.close()
        table = data_map['TABLE_NAME']
        
        columns = ""
        values = ""
        
        for field in data_map['data_map']:
            print('*******************************************')
            print(field)
            print('*******************************************')
            
            column = field['field']
            name_query = jp.parse(field["path"])
            result = name_query.find(json_obj)
            value = result[0].value
            
            to_zone = tz.tzlocal()
            
            match field["format"]:
                case "datetime":
                    dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
                    value = dt.astimezone(to_zone).strftime("%Y-%m-%dT%H:%M:%S")

                    columns += f"{column},"
                    values += f"'{value}',"

                case "num":
                    value = float(value)

                    columns += f"{column},"
                    values += f"{value},"
                
                case "text":
                    columns += f"{column},"
                    values += f"'{value}',"
                
                case "json":
                    value = json.dumps(value).replace("'", "''")
                    columns += f"{column},"
                    values += f"'{value}',"

                case "machine":
                    # If format matches a machine number : remove "."
                    if re.search(r"[UuQqXx][0-9]{3}[.][0-9]{4}", value):
                        value = value.replace(".", "")

                    columns += f"{column},"
                    values += f"'{value}',"
                
                case _:
                    ...
            
        # strip last coma
        columns = columns[:-1]
        values = values[:-1]

        query = f"""SET DATEFORMAT ymd;
                    INSERT INTO {table} ({columns}) VALUES ({values}) """

        return query 
        
    
    def xml_file_to_query(self, filepath, data_map):
        with open(filepath) as f:
            tree = objectify.parse(filepath)
            f.close()
        root = tree.getroot()
        main = root.getchildren()[0]
        
        columns = ""
        values = ""

        to_zone = tz.tzlocal()

        for field in data_map:
            label = field["path"]
            value = main.find(field["path"]).text

            match field["format"]:
                case "datetime":
                    dt = datetime.utcfromtimestamp(int(value))
                    value = dt.astimezone(to_zone).strftime("%Y-%m-%dT%H:%M:%S")

                    columns += f"{label},"
                    values += f"'{value}',"

                case "num":
                    value = float(value)

                    columns += f"{label},"
                    values += f"{value},"

                case _:
                    # If format matches a machine number : remove "."
                    if re.search(r"[UuQqXx][0-9]{3}[.][0-9]{4}", value):
                        value = value.replace(".", "")

                    columns += f"{label},"
                    values += f"'{value}',"

        # strip last coma
        columns = columns[:-1]
        values = values[:-1]

        query = f"""SET DATEFORMAT ymd;
                    INSERT INTO {self.table} ({columns}) VALUES ({values}) """

        return query    
    
    def execute_query(self, query):
        cursor = self.conn.cursor()
        cursor.execute(query)
        self.conn.commit()    
    
    def process_folder(self, folderpath, data_maps=None):
        _, inbox = os.path.split(folderpath)
        data_maps = self.get_data_maps(inbox)
        
        if data_maps:
            for data_map in data_maps:
                filename_filter = data_map['FILENAME_FILTER']
                file_ext = data_map['FILE_EXT']
                files = glob.glob(os.path.join(folderpath, filename_filter))
                for f in files:
                    folder, filename = os.path.split(f)
                    # try:
                    match file_ext:
                        case "xml":
                            query = self.xml_file_to_query(f, data_map)
                        case "json":
                            query = self.json_file_to_query(f, data_map)
                            print("-----------------------------------------")
                            print(query)
                            print("-----------------------------------------")
                            
                        case _:
                            ...
                            
                    self.execute_query(query)
                    # Move file
                    src = f
                    dst = os.path.join(folderpath, 'done', filename)
                    shutil.copy2(src, dst)
                    os.remove(src)
                    # except Exception as e:
                    #     logger.error(e)
                        
                
                
                
        else:
            files = glob.glob(os.path.join(folderpath, "*.txt"))
            
            for f in files:
                try:
                    query = self.std_txt_file_to_query(os.path.join(folderpath, f))               
                    
                        
                    self.execute_query(query)
                    # Move file
                    src = os.path.join(folderpath, f)
                    dst = os.path.join(folderpath, "done", f)
                    print('query done')
                    shutil.copy2(src, dst)
                    print('copy2 done')
                    os.remove(src)
                    print('remove done')
                except Exception as e:
                    logger.error(e)
    
    
    def close(self):
        self.conn.close()
        
            
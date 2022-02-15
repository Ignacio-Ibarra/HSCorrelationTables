import os
from pathlib import Path
import platform
import pandas as pd
import functools
from datetime import datetime
import numpy as np
import networkx as nx
from operator import and_
import requests


class HSCorrelations: 
    
    def __init__(self, path=None):
        self.__HS = {'HS92':'H0', 'HS96':'H1', 'HS02':'H2', 'HS07':'H3', 'HS12':'H4', 'HS17':'H5'} #should be updated if changed 
        print(f"Loading HS Correlation Tables from path provided")
        if path: 
            self.__data = pd.read_excel(path,
                            usecols= self.__HS.keys(),
                            dtype = {v:'object' for v in self.__HS.keys()}).dropna().drop_duplicates()
        else:
            print("Loading HS Correlation Tables from UNSTATS\n server")
            self.__url = "https://unstats.un.org/unsd/trade/classifications/tables/CompleteCorrelationsOfHS-SITC-BEC_20170606.xlsx"
            self.__data = pd.read_excel(self.__url,
                                usecols= self.__HS.keys(),
                                dtype = {v:'object' for v in self.__HS.keys()}).dropna().drop_duplicates()
        print("Tables already loaded. Use `available_methods()` for more information\n")
        
    def available_methods(self):
        print("Use `get_df()` to get dataframe with the correlations between all HS versions\n")
        print("Use `get_codes()` to get the codes by: version (default HS17, str or list) or chapter")
        print("Use `check_position()` to check if position exists")
        print("Use `year_to_HS()` to get the available HS version from years")
        #uncomplete
     
    def get_df(self):
        return self.__data
    
    def get_url(self):
        return self.__url
    
    def get_versions(self): 
        return self.__HS.keys()

    def get_codes(self, version="HS17", chapter=None): 
        df = pd.DataFrame(self.__data[version], columns = [version]).drop_duplicates()
        if chapter:
            df = df[df[version].str.startswith(chapter)]
        return df
    
    def check_position(self, position=None):
        if position:
            return position in self.__data.values
            
    
    def year_to_HS(self, start_year=None, end_year=None):
        if start_year==None: 
            start_year = 1992
        if end_year==None: 
            end_year = datetime.now().year
        if start_year < 1992 or end_year<start_year or end_year>datetime.now().year: 
            print("Uncorrect years")
        years = [1992, 1996, 2002, 2007, 2012, 2017]
        version_dict = {k:v for k,v in zip(years, self.__HS.keys())}
        start_v = functools.reduce(lambda a,b: a if a<=start_year else b, list(reversed(years)))
        end_v = functools.reduce(lambda a,b: a if a<=end_year else b, list(reversed(years)))
        years_list = years[years.index(start_v):years.index(end_v)+1]
        return [version_dict[x] for x in years_list]
    
    def HS_to_years(self,hslist):
        y = [1992, 1996, 2002, 2007, 2012, 2017]
        v_dict = {k:v for k,v in zip(self.__HS.keys(), y)}
        y_list = [v_dict[x] for x in hslist]
        start = min(y_list)
        end = datetime.now().year if max(y_list)==y[-1] else max(y_list)
        if start==end:
            return f"from {str(end)} to the present"
        else: 
            return f"from {str(start)} to {str(end)}"
        
        
    def filter_df(self, positions=None, start_year=None, end_year=None): 
        cols = self.year_to_HS(start_year, end_year) #filtra primero por año
        df = self.__data[cols]
        if positions:
            filters = [(df[col].isin(positions)) for col in cols] #filtra luego por presencia de posiciones en columna
            mask = functools.reduce(and_, filters, True)
            return df[mask].drop_duplicates().reset_index(drop=True)
        else:
            return df         
            
    def find_homogeneous_serie(self, position=None, start_year=None, end_year=None):
        if self.check_position(position): 
            cols = self.year_to_HS(start_year, end_year)
            dataa = self.filter_df(start_year=start_year, end_year=end_year)
            data = dataa.copy()
            versions = [v for v in cols if data[v].str.contains(position).any()]
            for col in cols:
                data[col] = data[col].apply(lambda x: col+"-"+str(int(x)).zfill(6))
            connections = []
            for i in range(len(cols)-1): 
                temp_tup_list = list(data[[cols[i], cols[i+1]]].drop_duplicates().itertuples(index=False, name=None))
                connections = connections + temp_tup_list 
            G = nx.Graph()
            G.add_edges_from(connections)
            positions = sorted(nx.node_connected_component(G, versions[-1]+"-"+position))
            return positions
        else:
            print("Please define a correct position")
    
    def genSankey(self, position=None, start_year=None, end_year=None, output_title='Sankey Diagram'):
        if self.check_position(position): 
            related = list(set([x[5:] for x in self.find_homogeneous_serie(position, start_year, end_year)]))
            cat_cols = self.year_to_HS(start_year, end_year)
            dfa = self.filter_df(related, start_year, end_year)
            dfa['count'] = 1
            df = dfa.copy()
            for col in cat_cols: 
                df[col] = df[col].apply(lambda x: col+"-"+str(int(x)).zfill(6))
            colorPalette = ['#4B8BBE','#306998','#FFE873','#FFD43B','#646464',"#002060"]
            labelList = []
            colorNumList = []
            for catCol in cat_cols:
                labelListTemp =  list(set(df[catCol].values))
                colorNumList.append(len(labelListTemp))
                labelList = labelList + labelListTemp

            # remove duplicates from labelList
            labelList = list(dict.fromkeys(labelList))

            # define colors based on number of levels
            colorList = []
            for idx, colorNum in enumerate(colorNumList):
                colorList = colorList + [colorPalette[idx]]*colorNum

            # transform df into a source-target pair
            for i in range(len(cat_cols)-1):
                if i==0:
                    sourceTargetDf = df[[cat_cols[i],cat_cols[i+1],'count']]
                    sourceTargetDf.columns = ['source','target','count']
                else:
                    tempDf = df[[cat_cols[i],cat_cols[i+1],'count']]
                    tempDf.columns = ['source','target','count']
                    sourceTargetDf = pd.concat([sourceTargetDf,tempDf])

            sourceTargetDf = sourceTargetDf.groupby(['source','target']).agg({'count':'sum'}).reset_index()

            # add index for source-target pair
            sourceTargetDf['sourceID'] = sourceTargetDf['source'].apply(lambda x: labelList.index(x))
            sourceTargetDf['targetID'] = sourceTargetDf['target'].apply(lambda x: labelList.index(x))

            # creating the sankey diagram
            data = dict(
                type='sankey',
                node = dict(
                  pad = 15,
                  thickness = 20,
                  line = dict(
                    color = "black",
                    width = 0.5
                  ),
                  label = labelList,
                  color = colorList
                ),
                link = dict(
                  source = sourceTargetDf['sourceID'],
                  target = sourceTargetDf['targetID'],
                  value = sourceTargetDf['count']
                )
              )

            layout =  dict(
                title = output_title,
                font = dict(
                  size = 10
                )
            )

            fig = dict(data=[data], layout=layout)
            return fig
        else: 
           print("Please define a correct position") 
    
    def recursive_trade_off(self, df, position, k): 
    
        if k>=0:
            currcols = df.columns.tolist()[k:]
            print(f"Evaluating graph object with {','.join(currcols)} versions\n")
            data = df[currcols].drop_duplicates()
            connections = []
            for i in range(len(currcols)-1): 
                temp_tup_list = list(data[[currcols[i], currcols[i+1]]].drop_duplicates().itertuples(index=False, name=None))
                connections = connections + temp_tup_list
            G = nx.Graph()
            G.add_edges_from(connections)
            try:
                positions = sorted(nx.node_connected_component(G, currcols[-1]+"-"+position))
                if len(positions)==len(currcols): 
                    return self.recursive_trade_off(df, position, k-1)
                else: 
                    print("Evaluation finished\n")
                    print(f"Your position has no precision loss {self.HS_to_years(currcols[1:])}")
            except:
                print(f"Position {position} not founded")
        else:
            print(f"Your position has no precision loss {self.HS_to_years(df.columns)}")
        
    def trade_off(self, position=None, start_year=None, end_year=None):
        if start_year==None: 
            start_year = 1992
        if end_year==None: 
            end_year = datetime.now().year
        if start_year < 1992 or end_year<start_year or end_year>datetime.now().year: 
            return print("Uncorrect years")
        if start_year>=2017:
            return print("Both years belong to the latest version")
        if self.check_position(position): 
            versions = self.year_to_HS(start_year, end_year)
            print(f"Period between {start_year} and {end_year} contains the {','.join(versions)} versions\n") 
            print(f"Loading HS Correlations Tables\n")
            versions = [v for v in versions if self.__data[v].str.contains(position).any()]

            if len(versions)>0: 
                print(f"The position {position} was included in the {','.join(versions)} versions\n")
                data = self.__data[versions].drop_duplicates()
                for col in data.columns:
                    data[col] = data[col].apply(lambda x: col+"-"+str(int(x)).zfill(6))
                k=len(versions)-2
                print(f"Evaluating maximum period with no precision loss for position {position}\n")
                return self.recursive_trade_off(data, position, k)
            else:
                print(f"Position {position} not founded in that period")
        else:
            print("Please define a correct position")

    

    def position_to_desc(self, position=None, HS=None):
        if self.check_position(position):
            if HS:
                url = "https://comtrade.un.org/data/cache/classification{}.json".format(self.__HS[HS])
                json = requests.get(url).json()
                df = pd.DataFrame(json['results'])
                description = df.loc[df.id==position,'text'].values[0]
                return description
            else:
                print("Please specify HS version")
        else:
            print("Please define a correct position")
    
    def query(self, position=None, start_year=None, end_year=None):
        if start_year==None: 
            start_year = 1992
        if end_year==None: 
            end_year = datetime.now().year
        if start_year < 1992 or end_year<start_year or end_year>datetime.now().year: 
            return print("Uncorrect years")
        if start_year>=2017:
            return print("Both years belong to the latest version")
        self.trade_off(position=position, start_year=start_year, end_year=end_year)
        print("*"*75)
        print(f"The positions you have to use to maintain homogeneous series between {start_year} and {end_year} is: \n\n", self.find_homogeneous_serie(position=position, start_year=start_year, end_year=end_year)) 

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
import plotly.graph_objects as go
import chart_studio.plotly as py
import plotly
import git
import platform
from bs4 import BeautifulSoup
import itertools
import re


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
        self.__url_base = "https://unstats.un.org/unsd/trade/classifications/"
        self.__url_suffix = "correspondence-tables.asp" 

    def available_methods(self):
        print("Use `get_df()` to get dataframe with the correlations between all HS versions\n")
        print("Use `get_codes()` to get the codes by: version (default HS17, str or list) or chapter")
        print("Use `check_position()` to check if position exists")
        print("Use `year_to_HS()` to get the available HS version from years")
        #uncomplete
    
    def get_conversion_link(self, from_year=None, to_year=None): 
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}
        r = requests.get(self.__url_base+self.__url_suffix, headers= headers)
        soup = BeautifulSoup(r.content, "html.parser")
        all_links = [str(x)[9: str(x).index('">')] for x in list(soup.find_all('a', href=True)) if "tables/HS" in str(x)]
        link = [x for x in all_links if str(from_year) in x and str(to_year) in x][0]
        return self.__url_base+link.replace(" ", "%20")

    def get_conversion_table(self, from_year=None, to_year=None): 
        url = self.get_conversion_link(from_year=from_year, to_year=to_year)
        xl = pd.ExcelFile(url)
        sheet_num = [idx for idx, s in enumerate(xl.sheet_names) if 'Conversion' in s][0]
        df = xl.parse(sheet_num, header=None)
        df = df.dropna(how="all", axis=0)
        df = df.dropna(how='all', axis=1).reset_index(drop=True)
        ncols = len(df.columns)
        tups = [(idx,s) for idx, s in enumerate(list(itertools.chain(*df.values))) if "HS" in str(s) and "Conversion" not in str(s)]
        id1, s1 = tups[0][0],tups[0][1]
        id2, s2 = tups[1][0], tups[1][1]
        a = list(range(0,ncols))*10
        col1id, col2id = a[id1], a[id2]
        df = df.iloc[:,np.array([col1id,col2id])]
        df.columns = [s1, s2]
        ind = df[df[s1]==s1].index[0]
        data = df.iloc[ind+1:,:].dropna().reset_index(drop=True)
        return data

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
            if len(versions)>0:
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
                return None
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
    

    def genSankey2(self, position=None, start_year=None, end_year=None, output_title='Sankey Diagram'):
        if self.check_position(position): 
            hom_series = self.find_homogeneous_serie(position, start_year, end_year)
            if hom_series: 
                related = list(set([x[5:] for x in hom_series]))
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

                import plotly.graph_objects as go

                fig = go.Figure(data = [go.Sankey(
                    node = dict(
                      pad = 15,
                      thickness = 20,
                      line = dict(
                        color = "black",
                        width = 0.5),
                      label = labelList,
                      color = colorList
                    ),
                    link = dict(
                      source = sourceTargetDf['sourceID'],
                      target = sourceTargetDf['targetID'],
                      value = sourceTargetDf['count']
                    )

                    )]
                )

                fig.update_layout(title_text = output_title, 
                    font_size = 10,
                    margin=dict(l=20, r=20, t=20, b=20))
                
                return fig
            else: 
                print(f"Position {position} not correspond to that period")
        else: 
           print("Please define a correct position")



    def recursive_trade_off(self, df, position, k): 
    
        if k>=0:
            currcols = df.columns.tolist()[k:]
            print(currcols, "(up currcols)")
            print(f"Evaluating graph object with {', '.join(currcols)} versions\n")
            data = df[currcols].drop_duplicates()
            connections = []
            for i in range(len(currcols)-1): 
                temp_tup_list = list(data[[currcols[i], currcols[i+1]]].drop_duplicates().itertuples(index=False, name=None))
                connections = connections + temp_tup_list
            G = nx.Graph()
            G.add_edges_from(connections)
            try:
                positions = sorted(nx.node_connected_component(G, currcols[-1]+"-"+position))
                print(positions, "connected positions\n", k, "k")
                if len(positions)==len(currcols): 
                    return self.recursive_trade_off(df, position, k-1)
                else: 
                    print("Evaluation finished\n")
                    print(currcols[1:], "(down currcols)")
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


    def trade_off2(self, position=None, start_year=None, end_year=None): #FALTA MODIFICAR
        
        """ La idea es resolver el bugg que se genera cuando hay una relación n:1 
        entre la última versión y la anterior, el programa no sigue evaluando si es posible
        encontrar una serie temporal para la misma position que no tenga pérdida de precision. 
        Ejemplo: ['HS92-030379','HS96-030379','HS02-030379','HS07-030361','HS07-030362','HS07-030379']
        La posicion 030379 no tiene perdida de precision para las versiones HS92, HS96 y HS02, sin embargo
        el programa recursive_trade_off() evalúa  """
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
                dist = 0
                for comb in itertools.combinations(versions, 2):
                    a,b = comb[0],comb[1]
                    ind_a, ind_b = versions.index(a), versions.index(b)
                    dist_temp = ind_b - ind_a
                    length = len(data.loc[data[a]==position, a:b].drop_duplicates())
                    if length == 1 and dist_temp>dist:
                        dist = dist_temp
                        selected_start = a
                        selected_end = b
                print(f"Your position has no precision loss {self.HS_to_years([selected_start,selected_end])}")
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
                description = df.loc[df.id==position,'text']
                if len(description)>0: 
                   return description.values[0]
                else: 
                    print("No matches found")
            else:
                print("Please specify HS version")
        else:
            print("Please define a correct position")
    

    def HS_from_year(self, year=None):
        if year==None: 
            print("Please define year")
        elif year < 1992 or year >datetime.now().year: 
            print("Uncorrect year")
        else:
            years = [1992, 1996, 2002, 2007, 2012, 2017]
            version_dict = {k:v for k,v in zip(years, self.__HS.keys())}
            year_v = functools.reduce(lambda a,b: a if a<=year else b, list(reversed(years)))
            return version_dict[year_v]
                


    def  search_position_by_name(self):
        """Hacer una función que vaya recorriendo las versiones (de más vieja a más nueva)
        busque un nombre entre las descripciones y determine cuáles son las posiciones que se pueden buscar"""
        print("This program begins with a text search.\n Please type the product name: \n")
        position_name = input()
        print("\nDefine a period.\nType start year:\n")
        start_year= int(input())
        print("\nType end year:\n")
        end_year = int(input())

        data = pd.DataFrame()
        query_versions = reversed(self.year_to_HS(start_year=start_year, end_year=end_year))
        for v in query_versions: 
            url = "https://comtrade.un.org/data/cache/classification{}.json".format(self.__HS[v])
            json = requests.get(url).json()
            df = pd.DataFrame(json['results'])
            df['version'] = v
            df = df[(df.id.str.contains("\\b\\d{6}\\b", regex=True))&
                (df.text.str.contains("\\b(?i)"+position_name+"s?|\\b(?i)"+position_name+"es?", flags=re.IGNORECASE, regex=True))].reset_index(drop=True)
            data = data.append(df, ignore_index=True)
        if len(data)==0:
            print(f"No matches found in {v} version")
        else: 
            grouped = data.groupby('id').agg({'text': lambda gr: str(gr.head(1).values[0]),'version':lambda gr: "|".join(gr)}).reset_index()
            text = grouped.text+" - "+grouped.version
            print()
            return "\n".join(text.values), start_year, end_year

    def query(self, position=None, start_year=None, end_year=None, sankey=False):
        if start_year==None: 
            start_year = 1992
        if end_year==None: 
            end_year = datetime.now().year
        if start_year < 1992 or end_year<start_year or end_year>datetime.now().year: 
            return print("Uncorrect years")
        if start_year>=2017:
            return print("Both years belong to the latest version")
        self.trade_off2(position=position, start_year=start_year, end_year=end_year)
        print("*"*75)
        print(f"The positions you have to use to maintain homogeneous series between {start_year} and {end_year} is: \n\n", self.find_homogeneous_serie(position=position, start_year=start_year, end_year=end_year)) 
        if sankey: 
            
            repo = git.Repo('.', search_parent_directories=True)
            repo = repo.working_tree_dir
            if platform.system()=='Windows':
                img_folder = repo+"\\img\\"
            else: 
                img_folder = repo+"/img/"
            Path(img_folder).mkdir(parents=True, exist_ok=True)
            fig = self.genSankey(position, start_year = start_year, end_year = end_year, output_title=f"Sankey Diagram - {position}")
            if fig is not None:
                return plotly.offline.plot(fig, validate=False, filename = f"{img_folder}{position}.html")
    

    def query2(self): 
        q, start_year, end_year = self.search_position_by_name()
        print(q,"\n")
        print("Please select your position code:\n")
        position=input()
        print("\n Do you want to get all the correlations in a Sankey plot? [Y/N]\n")
        sankey=""
        while sankey!=False and sankey!=True:
            answer = input()
            if answer.lstrip().rstrip().lower()=="y": 
                sankey=True
            elif answer.lstrip().rstrip().lower()=="n":
                sankey=False
            else:
                print("\n Uncorrect answer, try again! [Y/N]\n")
        
        if start_year==None: 
            start_year = 1992
        if end_year==None: 
            end_year = datetime.now().year
        if start_year < 1992 or end_year<start_year or end_year>datetime.now().year: 
            return print("Uncorrect years")
        if start_year>=2017:
            return print("Both years belong to the latest version")
        
        #print(f"\nThis program allows user to get three different output related with your code {position}.\n")
        #print(f"If you want to get")


        #self.trade_off(position=position, start_year=start_year, end_year=end_year)
        #print("*"*75)
        #print(f"The positions you have to use to maintain homogeneous series between {start_year} and {end_year} is: \n\n", self.find_homogeneous_serie(position=position, start_year=start_year, end_year=end_year)) 
        if sankey: 
            return self.genSankey2(position=position, start_year=start_year, end_year=end_year, output_title= f"Sankey Diagram - HS Code: {position}" )
            #repo = git.Repo('.', search_parent_directories=True)
            #repo = repo.working_tree_dir
            #if platform.system()=='Windows':
            #    img_folder = repo+"\\img\\"
            #else: 
            #    img_folder = repo+"/img/"
            #Path(img_folder).mkdir(parents=True, exist_ok=True)
            #fig = self.genSankey(position, start_year = start_year, end_year = end_year, output_title=f"Sankey Diagram - {position}")
            #if fig is not None:
            #    return plotly.offline.plot(fig, validate=False, filename = f"{img_folder}{position}.html")


    
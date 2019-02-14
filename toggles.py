__author__ = 'arsen52096_/'

import pyodbc,re
import pandas as pd
import numpy as np
import sys
import datetime

from constants import *

import os 

OPER = os.path.abspath('../Data/OperAM.mdb')
ANN = os.path.abspath('../Data/BasGodF.mdb')

# Функция я приведения всех ПХ к одному виду, насколько это возможно
def phToFormat(ph):
    try:
        ph = re.sub(r'[^\w\s]',' ',ph)    
        return ' '.join(ph.lower().split())
    except:
        return '!нет названия!'

# Функция получения суммарного передвижения за период
def returnTraffic(table):
    table = table.fillna(0)
    return (table.ix[0:9,:].sum() \
            + table.ix[11:19,:].sum() \
            - table.ix[20:29,:].sum() \
            + table.ix[30:42,:].sum() \
            - table.ix[43:51,:].sum() \
            + table.ix[52:61,:].sum() \
            - table.ix[68:71,:].sum() \
            + table.ix[72:80,:].sum() \
            - table.ix[81:86,:].sum() \
            + table.ix[87:97,:].sum() \
            - table.ix[98:,:].sum()            
           )

def getShortOrgName(code):
    # подключение к базе
    db = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+OPER)
    dbc = db.cursor()
    dbc.execute('SELECT NAME_SHORT from SprORG WHERE KOD_ORG=\''+str(code)+'\'')
    
    sh_name = dbc.fetchall()[0][0]
    
    db.close()
    
    return sh_name


def fetchOperative(code):
    # подключение к базе
    db = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+OPER)
    dbc = db.cursor()

    # запрос к форме 1.6 по коду организации
    def get_1_6_fromOrgCode(code):
        dbc.execute('SELECT \
                RAO.PH_Name,RAO.OpCod,RAO.OpDate,RAO.Kbm,RAO.Tonne,RAO.Sht,\
                RAO.ActA,RAO.ActBG,RAO.RAOCod,RAO.BCod \
                FROM SprORG INNER JOIN (FORMP INNER JOIN RAO ON FORMP.ID = RAO.IDF) ON SprORG.ID = FORMP.IDP \
                WHERE SprORG.KOD_ORG=\''+str(code)+'\''
               )
    
    
        return pd.DataFrame(np.array([row for row in dbc.fetchall()]),columns=COLS_1_6).fillna(0)

    # запрос к форме 1.5 по коду организации
    def get_1_5_fromOrgCode(code):
        dbc.execute('SELECT \
                ROZ.PH_Name,ROZ.OpCod,ROZ.OpDate,ROZ.Sht,ROZ.BCod \
                FROM SprORG INNER JOIN (FORMP INNER JOIN ROZ ON FORMP.ID = ROZ.IDF) ON SprORG.ID = FORMP.IDP \
                WHERE SprORG.KOD_ORG=\''+str(code)+'\''
               )
    
        return pd.DataFrame(np.array([row for row in dbc.fetchall()]),columns=COLS_1_5).fillna(0)

    # 1.6
    try:
        data_op = get_1_6_fromOrgCode(code).fillna(0)
        #print([type(i)for i in list(data_op['Операция, дата'].value_counts().index)])
        data_op['Год'] = (data_op['Операция, дата']).apply(lambda x: 
            x.year if isinstance(x, datetime.datetime ) else (2013 if isinstance(x, int) else x.to_datetime().year))
    except:
        print( "Unexpected error:", sys.exc_info()[0],sys.exc_info()[1])
        data_op = get_1_6_fromOrgCode(77057).fillna(0)
        data_op['Год'] = (data_op['Операция, дата']).apply(lambda x: x.year)
        data_op = data_op[data_op['Год']==1000]

    data_op['Код РАО'] = pd.to_numeric(data_op['Код РАО'], downcast='integer',errors='coerce')
    data_op['Код РАО'] = data_op['Код РАО'].fillna(0).apply(int)
    data_op['Статус РАО'] = data_op['Статус РАО'].apply(str)
    data_op['ПХ, наименование'] = data_op['ПХ, наименование'].apply(phToFormat) 

    grouped_op = data_op[[
        'ПХ, наименование','Операция, код',
        'Количество, куб.м','Количество, т','Суммарная активность, Бк, альфа-излучающих нуклидов',
        'Суммарная активность, Бк, бета-, гамма- излучающих нуклидов',
        'Год','Статус РАО','Код РАО','Количество, шт.'
        ]
       ].fillna(0).groupby(['Год','ПХ, наименование','Код РАО','Статус РАО','Операция, код'],as_index=False).sum()

    # 1.5
    try:
        data_op_1_5 = get_1_5_fromOrgCode(code).fillna(0)
        data_op_1_5['Год'] = (data_op_1_5['Операция, дата']).apply(lambda x: x.year)
    except:
        data_op_1_5 = get_1_5_fromOrgCode(77057).fillna(0)
        data_op_1_5['Год'] = (data_op_1_5['Операция, дата']).apply(lambda x: x.year)
        data_op_1_5 = data_op_1_5[data_op_1_5['Год']==1000]

    data_op_1_5['Статус РАО'] = data_op_1_5['Статус РАО'].apply(str)
    data_op_1_5['ПХ, наименование'] = data_op_1_5['ПХ, наименование'].apply(phToFormat)
    
    grouped_op_1_5 = data_op_1_5[[
        'ПХ, наименование','Операция, код',
        'Год','Статус РАО','ОЗРИ, количество, шт.'
        ]
       ].fillna(0).groupby(['Год','ПХ, наименование','Статус РАО','Операция, код'],as_index=False).sum()

    grouped_op_1_5['Количество, куб.м'] = 0
    grouped_op_1_5['Количество, т'] = 0
    grouped_op_1_5['Суммарная активность, Бк, альфа-излучающих нуклидов'] = 0
    grouped_op_1_5['Суммарная активность, Бк, бета-, гамма- излучающих нуклидов'] = 0
    grouped_op_1_5 = grouped_op_1_5.rename(str, columns={"ОЗРИ, количество, шт.": "Количество, шт."})
    
    
    db.close()

    return grouped_op,grouped_op_1_5

def fetchAnnual(code):
    # подключение к базе
    db = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ='+ANN)
    dbc = db.cursor()

    def get_2_2_fromOrgCode(code,alias='F2'):
        dbc.execute('SELECT FORMS.fYEAR,'+str(alias)+'.g2,'+str(alias)+'.g4,'+str(alias)+'.g5, \
                                        '+str(alias)+'.g6,'+str(alias)+'.g8,'+str(alias)+'.g10, \
                                        '+str(alias)+'.g14,'+str(alias)+'.g15 \
                        FROM SprORG INNER JOIN (FORMS INNER JOIN '+str(alias)+' ON FORMS.ID = '+str(alias)+'.IDF) ON SprORG.ID = FORMS.IDP \
                        WHERE SprORG.KOD_ORG=\''+str(code)+'\''
                   )
        return pd.DataFrame(np.array([row for row in dbc.fetchall()]),columns=COLS_2_2).fillna(0)
    
    # 2.2 both 19 and 24
    data_ann = pd.concat([get_2_2_fromOrgCode(code),get_2_2_fromOrgCode(code,'F2_24')]).fillna(0)
    data_ann['ПХ Наименование, №'] = data_ann['ПХ Наименование, №'].apply(phToFormat)
    

    def codeToInt(x):
        if isinstance(x,int):
            return x
        elif isinstance(x,str):
            if x.isdigit():
                return int(x)
            else:
                return 0
        else:
            return 0
    
    try:
        data_ann['Код РАО'] = data_ann['Код РАО'].apply(codeToInt)
    except:
        pass    
    data_ann['Статус РАО'] = data_ann['Статус РАО'].apply(str)

    grouped_ann = data_ann[[
        'ПХ Наименование, №',
        'Объем, м3','Масса нетто, т',
        'Сумм акт альфа-изл, Бк','Сумм акт бета, гамма-изл, Бк',
        'Количество ЗРИ, шт',
        'Год','Статус РАО','Код РАО'
        ]].fillna(0).groupby(['Год','ПХ Наименование, №','Код РАО','Статус РАО'],as_index=False).sum()

    return grouped_ann

def translate(name):
 
    #Заменяем пробелы и преобразуем строку к нижнему регистру
    name = name.replace('\"','')
    name = name.replace(' ','_').lower()
    
    #
    transtable = (
        ## Большие буквы
        (u"Щ", u"Sch"),
        (u"Щ", u"SCH"),
        # two-symbol
        (u"Ё", u"Yo"),
        (u"Ё", u"YO"),
        (u"Ж", u"Zh"),
        (u"Ж", u"ZH"),
        (u"Ц", u"Ts"),
        (u"Ц", u"TS"),
        (u"Ч", u"Ch"),
        (u"Ч", u"CH"),
        (u"Ш", u"Sh"),
        (u"Ш", u"SH"),
        (u"Ы", u"Yi"),
        (u"Ы", u"YI"),
        (u"Ю", u"Yu"),
        (u"Ю", u"YU"),
        (u"Я", u"Ya"),
        (u"Я", u"YA"),
        # one-symbol
        (u"А", u"A"),
        (u"Б", u"B"),
        (u"В", u"V"),
        (u"Г", u"G"),
        (u"Д", u"D"),
        (u"Е", u"E"),
        (u"З", u"Z"),
        (u"И", u"I"),
        (u"Й", u"J"),
        (u"К", u"K"),
        (u"Л", u"L"),
        (u"М", u"M"),
        (u"Н", u"N"),
        (u"О", u"O"),
        (u"П", u"P"),
        (u"Р", u"R"),
        (u"С", u"S"),
        (u"Т", u"T"),
        (u"У", u"U"),
        (u"Ф", u"F"),
        (u"Х", u"H"),
        (u"Э", u"E"),
        (u"Ъ", u"`"),
        (u"Ь", u"'"),
        ## Маленькие буквы
        # three-symbols
        (u"щ", u"sch"),
        # two-symbols
        (u"ё", u"yo"),
        (u"ж", u"zh"),
        (u"ц", u"ts"),
        (u"ч", u"ch"),
        (u"ш", u"sh"),
        (u"ы", u"yi"),
        (u"ю", u"yu"),
        (u"я", u"ya"),
        # one-symbol
        (u"а", u"a"),
        (u"б", u"b"),
        (u"в", u"v"),
        (u"г", u"g"),
        (u"д", u"d"),
        (u"е", u"e"),
        (u"з", u"z"),
        (u"и", u"i"),
        (u"й", u"j"),
        (u"к", u"k"),
        (u"л", u"l"),
        (u"м", u"m"),
        (u"н", u"n"),
        (u"о", u"o"),
        (u"п", u"p"),
        (u"р", u"r"),
        (u"с", u"s"),
        (u"т", u"t"),
        (u"у", u"u"),
        (u"ф", u"f"),
        (u"х", u"h"),
        (u"э", u"e"),
    )
    #перебираем символы в таблице и заменяем
    for symb_in, symb_out in transtable:
        name = name.replace(symb_in, symb_out)
    #возвращаем переменную
    return name



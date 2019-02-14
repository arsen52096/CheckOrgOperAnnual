__author__ = 'arsen52096_/'

from toggles import *
import seaborn as sns
import os,subprocess

import warnings
warnings.filterwarnings("ignore")

PATH = os.getcwd()
os.chdir(PATH)

class AnnualVSOperative:
    def __init__(self,code):
        self.code = code

        self.grouped_op, self.grouped_op_1_5 = fetchOperative(code)
        self.grouped_ann = fetchAnnual(code)

        self.ph_s = list(set(list(self.grouped_op['ПХ, наименование'].unique()) +
                        list(self.grouped_op_1_5['ПХ, наименование'].unique()) +
                        list(self.grouped_ann['ПХ Наименование, №'].unique())))
        
        self.ph_s_dict = {}
        for ph in self.ph_s:
            self.ph_s_dict[ph] = {
                    'status' : (list(set(list(self.grouped_op[self.grouped_op['ПХ, наименование']==ph]['Статус РАО'].unique()) +
                                list(self.grouped_op_1_5[self.grouped_op_1_5['ПХ, наименование']==ph]['Статус РАО'].unique()) +
                                list(self.grouped_ann[self.grouped_ann['ПХ Наименование, №']==ph]['Статус РАО'].unique())))),
                    'code' : list(set(list(self.grouped_op[self.grouped_op['ПХ, наименование']==ph]['Код РАО'].unique())+
                                list(self.grouped_ann[self.grouped_ann['ПХ Наименование, №']==ph]['Код РАО'].unique())))
                                }
    
        self.status_s = list(set(list(self.grouped_op['Статус РАО'].unique()) +
                    list(self.grouped_op_1_5['Статус РАО'].unique()) +
                    list(self.grouped_ann['Статус РАО'].unique())))

        self.year_s = (list(set(list(self.grouped_op['Год'].unique())+list(self.grouped_ann['Год'].unique()))))
        self.year_s.sort()

        self.code_s = self.grouped_op['Код РАО'].unique()
        #print( self.ph_s_dict)
        self.short_name = getShortOrgName(code)
        
        self.grouped_op['Код РАО'] = self.grouped_op['Код РАО'].apply(lambda x: int(str(x)[:10]))
        self.grouped_ann['Код РАО'] = self.grouped_ann['Код РАО'].apply(lambda x: int(str(x)[:10]))
                        

    
    def report(self):
        cm = sns.diverging_palette(150, 10, l=80, n=3,as_cmap=True)       
        num_index = 1
        page = 1
        #print(self.ph_s_dict)
        body = '<p align="right">Для служебного пользования</p>'
        body +=  '<h2><center>'+self.short_name+'</center><h2>'
        for p,ph in enumerate(self.ph_s): # self.ph_s
            print('%s из %s пунктов хранения' % (p+1,len(self.ph_s)))
            #for status in self.status_s:
            for status in self.ph_s_dict[ph]['status']:
                
                ozri_count = 0
                #for code in self.code_s:
                for code in self.ph_s_dict[ph]['code']:
                    
                    code_orig = code.copy()
                    #code = int(str(code)[:4]+'1'+str(code)[5:])
                    
                    if code//10e10>0:
                        code = code//10
                    
                
                    traffic_sum = pd.Series([0.,0.,0.,0.,0.],
                          index=[['Количество, куб.м', 'Количество, т',
                                  'Суммарная активность, Бк, альфа-излучающих нуклидов',
                                  'Суммарная активность, Бк, бета-, гамма- излучающих нуклидов','Количество, шт.']])
    
                    prev_table = pd.DataFrame(index = ['Оперативная отчетность','Годовая отчетность'],
                                                  columns = ['Количество, куб.м', 'Количество, т',
                                                              'Сумм акт альфа-изл, Бк',
                                                              'Сумм акт бета, гамма-изл, Бк',
                                                              'Количество ЗРИ, шт'])
        
                    prev_year = pd.Series()
                    for year in self.year_s:
                        if year==2018:
                            break
                        if year>2015:
                            code = code_orig
                        if year>2014:
                            code = int(str(code)[:4]+'1'+str(code)[5:])
                            
                        grouped_op = self.grouped_op
                        grouped_ann = self.grouped_ann
                                                    
                        table_op = grouped_op[grouped_op['ПХ, наименование']==ph]\
                            [grouped_op['Код РАО']==code]\
                            [grouped_op['Статус РАО']==status]\
                            [grouped_op['Год']==year]\
                            [['Операция, код','Количество, куб.м','Количество, т',\
                              'Суммарная активность, Бк, альфа-излучающих нуклидов',\
                              'Суммарная активность, Бк, бета-, гамма- излучающих нуклидов',
                              'Количество, шт.']].fillna(0).groupby(['Операция, код']).sum()

                        table_ann = grouped_ann[grouped_ann['ПХ Наименование, №']==ph]\
                                    [grouped_ann['Код РАО']==code]\
                                    [grouped_ann['Статус РАО']==status]\
                                    [grouped_ann['Год']==year]\
                                    [['Объем, м3','Масса нетто, т',                
                                      'Сумм акт альфа-изл, Бк',
                                      'Сумм акт бета, гамма-изл, Бк',
                                      'Количество ЗРИ, шт'
                                      ]].fillna(0).sum() # 'Количество ЗРИ, шт',
                        
                            #print(table_op)
                            #print(table_ann)
# or (np.any(prev_table.values!=table_ann.values) and table_op.empty)
                        if (not table_op.empty and table_ann.sum()!=0) or not table_op.empty:
#                            if table_ann.sum()!=0:
#                                prev_ann_table = table_ann
                            
                            if str(code)[-2:] in OZRI_CODES:
                                grouped_op_1_5 = self.grouped_op_1_5

                                ozri_count = grouped_op_1_5[grouped_op_1_5['ПХ, наименование']==ph]\
                                        [grouped_op_1_5['Статус РАО']==status]\
                                        [grouped_op_1_5['Год']==year]\
                                        [['Операция, код','Количество, куб.м','Количество, т',\
                                  'Суммарная активность, Бк, альфа-излучающих нуклидов',\
                                  'Суммарная активность, Бк, бета-, гамма- излучающих нуклидов',
                                  'Количество, шт.']].fillna(0).groupby(['Операция, код']).sum()
                            
                                if not ozri_count.empty:
                                    try:
                                        table_op = table_op.append(ozri_count)
                                    except:
                                        table_op = table_op.add(ozri_count)
                                    
                            table_op = table_op.sort_index()
                            traffic_table = returnTraffic(table_op).fillna(0)

                            traffic_sum += traffic_table
                            
                            traffic_sum = traffic_sum.apply(lambda x: round(x,3) if type(x)==float else x)
                            traffic_sum = traffic_sum.apply(lambda x: int((x-x%10**(int(np.log10(x))-2))) if (x>10**4) else x)
                            table_ann = table_ann.apply(lambda x: round(x,3) if type(x)==float else x)
                            table_ann = table_ann.apply(lambda x: int((x-x%10**(int(np.log10(x))-2))) if (x>10**4) else x)
                          
                            
                            if np.all(prev_year.values==table_ann.values) and traffic_table.sum()==0.:
                                    prev_year = table_ann
                                    continue
                            
                            if not all(traffic_sum.values==table_ann.values):
#                                print(traffic_sum.values)
#                                print(table_ann.values)
#                                print(prev_year.values)
                                
                                
                                
                                df = pd.DataFrame([traffic_sum.values,
                                                   table_ann.values],
                                                  index = ['Оперативная отчетность','Годовая отчетность'],
                                                  columns = ['Количество, куб.м', 'Количество, т',
                                                              'Сумм акт альфа-изл, Бк',
                                                              'Сумм акт бета, гамма-изл, Бк',
                                                              'Количество ЗРИ, шт'])
                                
                                
                               
#                                print(df)
                                
                                
                                
                                print('%d) На конец %d года\tСтатус РАО:%s\tКод РАО:%s\tПХ: %s'%(num_index,year,status,code,ph))
                                body += '<h3>'+str(num_index)+') На конец '+str(year)+' года\tКод РАО: '+str(code_orig)+ \
                                        '\tСтатус РАО: '+status+'\tПХ: '+ph+'</h3>'
                            
#                                print(prev_year)
#                                print(table_ann)
#                                print(traffic_sum.ix[:4].sum())
                                
                                # пока убрал ОЗРИ
                                body += df.style.background_gradient(cmap=cm).render()
                                if (num_index%5!=0):
                                    body += '<br>'
                                else:
                                    page +=1 # -- протокол проверки, '+str(page)+' cтр. --
                                    body += '<h2><center> </center><h2>'
                                num_index += 1
                        
#                            print(table_ann['Количество ЗРИ, шт'])
#                            print(traffic_sum)
                        prev_year = table_ann    
        
        
        top = open('src/snippets/top.txt','r')
        top = top.readlines()

        bottom = open('src/snippets/bottom.txt','r')
        bottom = bottom.readlines()
        
        transl_short_name = translate(self.short_name)
        htm_file_name = 'src/html/'+transl_short_name+'.htm'
        file  = open(htm_file_name,'w')
        file.write(''.join(top)+body+''.join(bottom))
        file.close()
        
        pdf_file_name = "src/pdf/"+transl_short_name+".pdf"
        
        try:
            os.remove(pdf_file_name)
        except OSError:
            pass
        
        subprocess.call(["src/wkhtmltopdf64.exe", os.path.abspath(htm_file_name),pdf_file_name])



if __name__ == "__main__":
    print('Приветствую! Введите код организации:')
    
    ORG = (input())
    
    aVSo = AnnualVSOperative(ORG)
    
    print('Запустить сверку для %s?' % (aVSo.short_name))
    os.system("PAUSE")
    
    aVSo.report()
    
    print('Спасибо за ожидание! Файл готов. До скорой встречи!')
    os.system("PAUSE")
file_menu = 'outputTSV.tsv'
file_sample = 'config/triggerDatasetMapTail.py'
file_output = 'Menu_online_v3p1_V2.py'
triggerName = 'tttt'
column_stream = 0
column_dataset = 1
column_trigger = 2
column_type = -1
column_group = 3
column_ps = 5

triggerDataset = {}
triggerStream = {}
triggerGroup = {}
triggerType = {}
prescaleMap = {}

current_stream = ''
current_dataset = ''

def check_group(group):
    group_list =['EXO', 'JME', 'SUS', 'BPH', 'SMP', 'BTV', 'TAU', 'HIG', 'EGM', 'B2G', 'MUO', 'PPD', 'AlCa', 'TOP', 'HIN', 'TRK', 'FSQ', 'ECAL', 'HCAL', 'null', 'All_HLT', 'All_PSed', 'type_signal', 'type_control','Higgs','Analysis','tau-pog','Egamma','ttH']
    if group in group_list:
        return True
    isGroup = True
    if (len(group)<3 or len(group)>10)and isGroup:
        isGroup = False
    if isGroup:
        if not group[0].isupper():
            isGroup = False
#        if not group[1].isupper():
#            isGroup = False
    return isGroup


for Line in open(file_menu,'r'):
    line = Line.split('\t')
    trigger = ''
    if column_stream >=0:
        if 'stream' in line[column_stream]:
            current_stream = line[column_stream].replace('stream','')
            current_stream = current_stream.replace('\n','')
            current_stream = current_stream.replace(' ','')
            continue
    if column_dataset >=0:
        if 'dataset' in line[column_dataset]:
            current_dataset = line[column_dataset].replace('dataset','')
            current_dataset = current_dataset.replace('\n','')
            current_dataset = current_dataset.replace(' ','')
            continue
    if column_trigger >=0:
        if '_v' in line[column_trigger]:
            trigger = line[column_trigger]
            print trigger
        else:continue
# make stream map
    if column_stream >=0:
        if not (trigger in triggerStream):
            tmp_list = []
            tmp_list.append(current_stream)
            triggerStream[trigger] = tmp_list
        else:
            if not (current_stream in triggerStream[trigger]):
                triggerStream[trigger].append(current_stream)

# make dataset map
    if column_dataset >=0:
        if not (trigger in triggerDataset):
            tmp_list = []
            tmp_list.append(current_dataset)
            triggerDataset[trigger] = tmp_list
        else:
            if not (current_dataset in triggerDataset[trigger]):
                triggerDataset[trigger].append(current_dataset)
# make group map
    if column_group >=0:
        tmp_group = line[column_group]
        tmp_group = tmp_group.replace('/',',')
        tmp_group = tmp_group.replace('(',',')
        tmp_group = tmp_group.replace(')',',')
        tmp_group = tmp_group.replace('-',',')
        tmp_group = tmp_group.replace('.',',')
        tmp_group = tmp_group.replace('SUSY','SUS')
        tmp_group = tmp_group.replace('Higgs','HIG')
        tmp_group = tmp_group.replace('Egamma','EGM')
        tmp_group = tmp_group.replace('EXO PAG','EXO,PAG')
        tmp_group = tmp_group.replace('B2G PAG','B2G,PAG')
        tmp_group = tmp_group.replace('Muon','MUO')
        tmp_group = tmp_group.replace('muon','MUO')
        tmp_group = tmp_group.replace('tau pog','tau-pog')
        tmp_group_list = tmp_group.split(',')
        tmp_group_list2 = []
        if not (trigger in triggerGroup):
            for group in tmp_group_list:
                group=group.strip(' ')
                if check_group(group):
                    tmp_group_list2.append(group)
            if tmp_group_list2 == []:
                tmp_group_list2 = [' ']
            triggerGroup[trigger] = tmp_group_list2 
# make PS map
    if column_ps >=0:
        if not (trigger in prescaleMap):
            tmp_list = []
            prescale = line[column_ps]
	    prescale = prescale.replace('\n','')
            prescale = prescale.replace('\r','')
            prescale = prescale.replace('\d','')
            prescale = prescale.replace(' ','')
            prescale = prescale.replace(',','.')
            tmp_ps = float(prescale)
            if tmp_ps !=0 and tmp_ps <1:
                tmp_ps = 1
            tmp_list.append(str(int(tmp_ps)))
            prescaleMap[trigger] = tmp_list

# make type map
    if column_type >=0:
        if not (trigger in triggerType):
            tmp_list = []
            tmp_list.append(line[column_type])
            triggerType[trigger] = tmp_list
        else:
            if not (line[column_type] in triggerType[trigger]):
                triggerType[trigger].append(line[column_type])


# write to output triggerMap.py
file_out = open(file_output,'w')

file_out.write('# -*- coding: iso-8859-15 -*-\n')
file_out.write('triggerList = []\n')
file_out.write('triggerName = "%s"\n'%(triggerName))

# write dataset
file_out.write('triggersDatasetMap = {\n')
for trigger in triggerDataset:
    file_out.write('    \'%s\' : %s,\n'%(trigger,triggerDataset[trigger]))
file_out.write('}\n\n')
# write group
file_out.write('triggersGroupMap = {\n')
for trigger in triggerGroup:
    file_out.write('    \'%s\' : %s,\n'%(trigger,triggerGroup[trigger]))
file_out.write('}\n\n')
# write stream
file_out.write('DatasetStreamMap = {\n')
for trigger in triggerStream:
    file_out.write('    \'%s\' : %s,\n'%(trigger,triggerStream[trigger]))
file_out.write('}\n\n')
# write ps information
file_out.write('prescaleMap = {\n')
for trigger in prescaleMap:
    file_out.write('    \'%s\' : %s,\n'%(trigger,prescaleMap[trigger]))
file_out.write('}\n\n')
# write type information
file_out.write('triggersTypeMap = {\n')
for trigger in triggerType:
    file_out.write('    \'%s\' : %s,\n'%(trigger,triggerType[trigger]))
file_out.write('}\n\n')

# write the rest part (from sample)
for line in open(file_sample,'r'):
    file_out.write(line)

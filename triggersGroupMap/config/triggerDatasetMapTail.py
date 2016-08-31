
triggersToRemove = [
    'DST_*',
    'AlCa_*',
    'HLT_EcalCalibration_v',
    'HLT_HcalCalibration_v',
    'HLT_HT410to430_v',
    'HLT_HT430to450_v',
    'HLT_HT450to470_v',
    'HLT_HT470to500_v',
    'HLT_HT500to550_v',
    'HLT_HT550to650_v',
    'HLT_HT650_v',
    'HLT_Physics_v',
    'HLT_L1FatEvents_part0_v',
    'HLT_L1FatEvents_part1_v',
    'HLT_L1FatEvents_part2_v',
    'HLT_L1FatEvents_part3_v',
    'HLT_L1FatEvents_v',
    'HLT_ZeroBias_part0_v',
    'HLT_ZeroBias_part1_v',
    'HLT_ZeroBias_part2_v',
    'HLT_ZeroBias_part3_v',
    'HLT_ZeroBias_part4_v',
    'HLT_Physics_part0_v',
    'HLT_Physics_part1_v',
    'HLT_Physics_part2_v',
    'HLT_Physics_part3_v',
    'HLT_ZeroBias_v',
    'HLT_Random_v',
    'HLT_RsqMR240_Rsq0p09_MR200_4jet_v',
    'HLT_PFHT250_DiPFJetAve90_PFAlphaT0p55_v',
    'HLT_PFHT300_DiPFJetAve90_PFAlphaT0p53_v',
    'HLT_PFHT350_DiPFJetAve90_PFAlphaT0p52_v',
    'HLT_PFHT400_DiPFJetAve90_PFAlphaT0p51_v',
    'HLT_Photon90_CaloIdL_PFHT500_v',
    'HLT_Mu3er_PFHT140_PFMET125_v',
    'HLT_Mu6_PFHT200_PFMET80_BTagCSV_p067_v',
    'HLT_PFMET120_BTagCSV_p067_v',
    
]

def check_trigger(trigger_in):
    if trigger_in in triggersToRemove:
        return True

    for trigger in triggersToRemove:
        if '*' in trigger:
            if trigger[:-1] in trigger_in:
                return True

        elif '_v' in trigger:
            if trigger.split('_v')[0] == trigger_in.split('_v')[0]:
                return True

        else:
            if trigger == trigger_in.split('_v')[0]:
                return True
    return False


#triggersGroupMap = dict(triggersGroupMap.items())

triggerList = []
L1List = []
HLTList = []
#twoHLTsList = []
primaryDatasetList = []
groupList = []
twoDatasetsList = []
getTriggerString = {}

## Fill triggerList and groupList and primaryDatasetList
for trigger in triggersDatasetMap.keys():
    #if trigger[:-1] in triggersToRemove: continue
    if not (trigger in triggerList) : triggerList.append(trigger)
    for dataset in triggersDatasetMap[trigger]:
        if not dataset in primaryDatasetList: primaryDatasetList.append(dataset)
    if check_trigger(trigger):continue
    for group in triggersGroupMap[trigger]:
        if not group in groupList: groupList.append(group)

## Fill HLTList and L1List
for trigger in triggerList:
    if "HLT_" in trigger: HLTList.append(trigger)
#    elif "L1_" in trigger: L1List.append(trigger)

## Fill getTriggerString get a map from trigger and group names to strings
for trigger in triggerList:
    getTriggerString[trigger]=trigger
    for dataset in triggersDatasetMap[trigger]:
        if dataset in getTriggerString.keys(): getTriggerString[dataset]+='||'+trigger
        else: getTriggerString[dataset]=trigger
    if check_trigger(trigger):
        print trigger
        continue
    for group in triggersGroupMap[trigger]:
        if group in getTriggerString.keys(): getTriggerString[group]+='||'+trigger
        else: getTriggerString[group]=trigger

## Fill string for All group
groupList.append('All_HLT')
for trigger in HLTList:
    if check_trigger(trigger):continue
    if 'All_HLT' in getTriggerString.keys(): getTriggerString['All_HLT']+='||'+trigger
    else: getTriggerString['All_HLT']=trigger

## Fill string for prescaled paths
groupList.append('All_PSed')
for trigger in HLTList:
    if check_trigger(trigger):continue
    if int(prescaleMap[trigger][0]) <=1 : continue
    if 'All_PSed' in getTriggerString.keys(): getTriggerString['All_PSed']+='||'+trigger
    else: getTriggerString['All_PSed']=trigger

## Fill string for type
if triggersTypeMap:
    groupList.append('type_signal')
    for trigger in triggersTypeMap:
        if check_trigger(trigger):continue
        if (not ('signal' in triggersTypeMap[trigger])) and (not ('backup' in triggersTypeMap[trigger])):continue
        if 'type_signal' in getTriggerString.keys(): getTriggerString['type_signal']+='||'+trigger
        else: getTriggerString['type_signal']=trigger
    
    groupList.append('type_control')
    for trigger in triggersTypeMap:
        if check_trigger(trigger):continue
        if not ('control' in triggersTypeMap[trigger]):continue
        if 'type_control' in getTriggerString.keys(): getTriggerString['type_control']+='||'+trigger
        else: getTriggerString['type_control']=trigger

#groupList.append('type_backup')
#for trigger in triggersTypeMap:
#    if not ('backup' in triggersTypeMap[trigger]):continue
#    if 'type_backup' in getTriggerString.keys(): getTriggerString['type_backup']+='||'+trigger
#    else: getTriggerString['type_backup']=trigger

                                           
print groupList

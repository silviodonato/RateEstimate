#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

########## Configuration #####################################################################
#from triggersGroupMap.triggersGroupMap__frozen_2015_25ns14e33_v4p4_HLT_V1 import *
#from triggersGroupMap.triggersMap_GRun_V72 import *
from triggersGroupMap.Menu_online_v3p1_V2 import *
#from triggersGroupMap.prescaleMap_GRun_V72 import *
#from triggersGroupMap.triggersMap_L1HandMade import *
#from datasetCrossSections.datasetCrossSectionsPhys14 import *
from datasetCrossSections.datasetCrossSectionsHLTPhysics import *
#from datasetCrossSections.datasetLumiSectionsData import *

batchSplit = False
batchSplit = True
looping = False
looping = True

##### Adding an option to the code #####

if batchSplit:
    from optparse import OptionParser
    parser=OptionParser()

    parser.add_option("-n","--number",dest="fileNumber",default="0",type="int") # python file.py -n N => options.fileNumber is N
    parser.add_option("-d","--dataset",dest="datasetName",default="",type="str")

    (options,args)=parser.parse_args()

##### Other configurations #####

folder = '/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/Run2016G/HLTPhysics_2016G_menu3p1p6_279694/HLTPhysics_ntuples'
localdir = '/afs/cern.ch/user/x/xgao/eos/cms'
lumi = 1              # luminosity [s-1cm-2]
if (batchSplit): multiprocess = 1           # number of processes
else: multiprocess = 1 # 8 multiprocessing disbaled for now because of incompatibilities with the way the files are accessed. Need some development.
pileupMAX = 100
pileupMIN = 0
pileupFilter = False        # use pile-up filter?
pileupFilterGen = False    # use pile-up filter gen or L1?
useEMEnriched = False       # use plain QCD mu-enriched samples (Pt30to170)?
useMuEnriched = False       # use plain QCD EM-enriched samples (Pt30to170)?
evalL1 = False              # evaluate L1 triggers rates?
evalHLTpaths = True        # evaluate HLT triggers rates?
evalHLTgroups = True       # evaluate HLT triggers groups rates and global HLT and L1 rates
evalHLTprimaryDatasets = False # evaluate HLT triggers primary datasets rates and global HLT and L1 rates
#evalHLTtwopaths = True    # evaluate the correlation among the HLT trigger paths rates?
evalHLTtwogroups = False   # evaluate the correlation among the HLT trigger groups rates?
label = "test"         # name of the output files
runNo = "279654"           #if runNo='0', means code will run for all Run.
LS_min = '43'
LS_max = '246'            #default is 9999

isData = True
## L1Rate studies as a function of PU and number of bunches:
evalL1scaling = False

nLS = 623 ## number of Lumi Sections run over data
lenLS = 23.31 ## length of Lumi Section
psNorm = 720. / 4. #*(5./4.64) #232./4. # Prescale Normalization factor if running on HLTPhysics
###############################################################################################

## log level
log = 2                     # use log=2

## filter to be used for QCD EM/Mu enriched
EM_cut = "(!HLT_BCToEFilter_v1 && HLT_EmFilter_v1)"# && HLT_EmGlobalFilter_v1)"
Mu_cut = "(MCmu3)"# && HLT_MuFilter_v1)"

## filter to be used for pile-up filter
PUFilterGen = 'HLT_RemovePileUpDominatedEventsGenV2_v1'
PUFilterL1 = 'HLT_RemovePileUpDominatedEvents_v1'

##### Load lib #####

import ROOT
import time
import sys
from math import *
from os import walk
from os import mkdir
from scipy.stats import binom
import math
import datetime
import os
import shlex
import subprocess
import json

ROOT.TFormula.SetMaxima(10000,10000,10000) # Allows to extend the number of operators in a root TFormula. Needed to evaluate the .Draw( ,OR string) in the GetEvents function

##### Function definition #####

executable_eos = '/afs/cern.ch/project/eos/installation/cms/bin/eos.select'

def runCommand(commandLine):
    #sys.stdout.write("%s\n" % commandLine)
    args = shlex.split(commandLine)
    retVal = subprocess.Popen(args, stdout = subprocess.PIPE)
    return retVal

def lsl(file_or_path,my_filelist):
    '''
    List EOS file/directory content, returning the information found in 'eos ls -l'.
    The output is a list of dictionaries with the following entries:
        permissions
        file
        modified
        size (in bytes)
    An exception of type IOError will be raised in case file/directory does not exist.
    '''

    directory = os.path.dirname(file_or_path)
    ls_command = runCommand('%s ls -l %s' % (executable_eos, file_or_path))

    stdout, stderr = ls_command.communicate()
    #print "stdout = ", stdout
    status = ls_command.returncode
    #print "status = ", status
    if status != 0:
        raise IOError("File/path = %s does not exist !!" % file_or_path)
    
    retVal = []
    for line in stdout.splitlines():
        fields = line.split()
        if len(fields) < 8:
            continue
        file_info = {
            'permissions' : fields[0],
            'size' : int(fields[4]),
            'file' : fields[8]
        }
        time_stamp = " ".join(fields[5:8])
        # CV: value of field[7] may be in format "hour:minute" or "year".
        #     if number contains ":" it means that value specifies hour and minute when file/directory was created
        #      and file/directory was created this year.
        if time_stamp.find(':') != -1:
            file_info['time'] = time.strptime(
                time_stamp + " " + str(datetime.datetime.now().year),
                "%b %d %H:%M %Y")
        else:
            file_info['time'] = time.strptime(time_stamp, "%b %d %Y")
        file_info['path'] = file_or_path
        #print "file_info = " % file_info
        retVal.append(file_info)
        my_filelist.append(file_info)
        tmp_path=file_info['path']+'/'+file_info['file']
        if not '.' in tmp_path[-5:]:
            isdir=True
        else:
            isdir=False
        #print "is dir: ", isdir
        #print "file_info =", file_info
        if isdir and not 'log' in tmp_path:
            lsl(file_info['path']+'/'+file_info['file'],my_filelist)
    return

## modified square root to avoid error
def sqrtMod(x):
    if x>0: return sqrt(x)
    else: return 0

## not used (under development)
def CL(p,n):
    precision1 = 1E-3
    precision2 = 1E-6
    epsilon = 1.*p/n
    epsilon_down = epsilon
    epsilon_up = epsilon
    prob = 0.5
    while prob<0.95:
        epsilon_down/=1+precision1
        prob = binom.cdf(p, n, epsilon_down)
    
    while prob>0.95:
        epsilon_down*=1+precision2
        prob = binom.cdf(p, n, epsilon_down)
    
    while prob>0.05:
        epsilon_up*=1+precision1
        prob = binom.cdf(p-1, n, epsilon_up) 
    
    while prob<0.05:
        epsilon_up/=1+precision2
        prob = binom.cdf(p-1, n, epsilon_up) 
    
    return epsilon_down,epsilon_up

## not used (under development)
def test_CL(p,n):
    print  1-CL(p,n)[0]-CL(n-p,n)[1]
    print  1-CL(p,n)[1]-CL(n-p,n)[0]

## get the trigger list from the ntuples
def getTriggersListFromNtuple(chain,triggerListInNtuples):
            for leaf in chain.GetListOfLeaves():
               name = leaf.GetName()
               if (("HLT_" in name) or (evalL1 and ("L1_" in name))) and not ("Prescl" in name):
                triggerListInNtuples.append(name)

## get the prescale associated with a trigger from the ntuples
def getPrescaleListInNtuples():                                                                               
    prescales={}                                                                                                                   
  # take the first "hltbit" file                                                                                                   
    dirpath = ''                                                                                                                   
    filenames = []                                                                                                                 
    for dataset in datasetList:
        datasetName = dataset
        noRootFile = True
        onlyFail = False
        walking_folder = folder+"/"+datasetName
        eosDirContent = []
        lsl(walking_folder,eosDirContent)
        for key in eosDirContent:
            if (("failed" in str(key['path'])) or ("log" in str(key['path']))):
                onlyFail = True
                continue
            elif ("root" in str(key['file'])):
                filenames.append("root://eoscms//eos/cms"+str(key['path'])+'/'+str(key['file']))
                dirpath = "root://eoscms//eos/cms/"+walking_folder
                noRootFile = False
                onlyFail = False
                break
        if len(filenames)>0: break
 
    if len(filenames)==0:                                                                                                          
        raise ValueError('No good file found in '+folder)                                                                          
                                                                                                                                   
    for filename in filenames:                                                                                                     
        if 'hltbit' in filename: break                                                                                             
                                                                                                                                   
    _file0 = ROOT.TFile.Open(filename)                                                                                 
    chain = ROOT.gDirectory.Get("HltTree")                                                                                         
                                                                                                                                   
    for leaf in chain.GetListOfLeaves():                                                                                           
        name = leaf.GetName()                                                                                                      
        if (("HLT_" in name) or (evalL1 and ("L1_" in name))) and not ("Prescl" in name):                                          
            trigger=name                                                                                                           
            i=0                                                                                                                    
            pname=name+'_Prescl'                                                                                                   
            for event in chain:                                                                                                    
                value=getattr(event,pname)                                                                                         
                if (i==2): break                                                                                                   
                i+=1                                                                                                               
            prescales[trigger]=value                                                                                               

    return prescales       

## set and fill totalEventsMatrix, passedEventsMatrix, rateTriggerTotal, squaredErrorRateTriggerTotal with zero
def setToZero(totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix,triggerAndGroupList,rateTriggerTotal,squaredErrorRateTriggerTotal) :
    for dataset in xsectionDatasets:
        totalEventsMatrix[dataset]=0
        for trigger in triggerAndGroupList:
            passedEventsMatrix[(dataset,trigger)]=0
            WeightedErrorMatrix[(dataset,trigger)]=0
    
    for trigger in triggerAndGroupList:
        rateTriggerTotal[trigger]=0
        squaredErrorRateTriggerTotal[trigger]=0

## read totalEventsMatrix and passedEventsMatrix and write a .tsv file containing the number of events that passed the trigger
def writeMatrixEvents(fileName,datasetList,triggerList,totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix,writeGroup=False,writeDataset=False):
    f = open(fileName, 'w')
    text = 'Path\t' 
    if writeGroup: text += 'Group\t'
    if writeDataset: text += 'Primary dataset\t'
    for dataset in datasetList:
        datasetName = dataset[:-21]
        datasetName = datasetName.replace("-", "")
        datasetName = datasetName.replace("_", "")
        text +=  datasetName + '\t\t\t'

    text += '\n'
    text +=  'TotalEvents\t'
    if writeGroup: text += '\t'
    if writeDataset: text += '\t'
    for dataset in datasetList:
        text += str(totalEventsMatrix[dataset]) + '\t'

    for trigger in triggerList: 
        text += '\n'
        text +=  trigger+'\t'
        if writeGroup:
            for group in triggersGroupMap[trigger]:
                if not group.isdigit(): text += group+','        
            text=text[:-1] ##remove the last comma
            text += '\t'
        if writeDataset and trigger not in L1List:
            for dataset in triggersDatasetMap[trigger]: text += dataset+','
            text=text[:-1] ##remove the last comma
            text += '\t'       
 
        for dataset in datasetList:
            if batchSplit:
                if options.datasetName=="all": text += str(passedEventsMatrix[(dataset,trigger)]) + '\t'
                elif dataset==options.datasetName: text += str(passedEventsMatrix[(dataset,trigger)]) + '\t±\t' + str(sqrtMod(WeightedErrorMatrix[(dataset,trigger)])) + '\t'
                else: text += str(0) + '\t±\t' + str(0) + '\t'
            else: text += str(passedEventsMatrix[(dataset,trigger)]) + '\t'

    f.write(text)
    f.close()

## read rateTriggerTotal and rateTriggerDataset and write a .tsv file containing the trigger rates
def writeMatrixRates(fileName,prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,triggerList,writeGroup=False,writeDataset=False):
    f = open(fileName, 'w')
    text = 'Prescale\t'
    text += 'Path\t'
    if writeGroup: text += 'Group\t'
    if writeDataset: text += 'Primary dataset\t'
    text += 'Total\t\t\t'
    for dataset in datasetList:
        datasetName = dataset
        #datasetName = dataset[:-21]
        #datasetName = datasetName.replace("-", "")
        #datasetName = datasetName.replace("_", "")
        text +=  datasetName + '\t\t\t'

    for trigger in triggerList:
        text += '\n'
        if (trigger not in groupList) and (trigger not in primaryDatasetList):# and (trigger not in twoGroupsList):
            text += str(prescaleList[trigger])+'\t'
        else: text += ''+'\t'    
        text +=  trigger+'\t'
        if writeGroup:
            for group in triggersGroupMap[trigger]:
                if not group.isdigit(): text += group+','        
            text=text[:-1] ##remove the last comma
            text += '\t'
        if writeDataset and trigger not in L1List:
            for dataset in triggersDatasetMap[trigger]: text += dataset+','
            text=text[:-1] ##remove the last comma
            text += '\t'
        
        text += str(rateTriggerTotal[trigger])+'\t±\t'+str(sqrtMod(squaredErrorRateTriggerTotal[trigger]))+'\t'
        for dataset in datasetList:
            if batchSplit:
                if options.datasetName=="all": text += str(rateTriggerDataset[(dataset,trigger)]) + '\t±\t' + str(sqrtMod(squaredErrorRateTriggerDataset[(dataset,trigger)])) + '\t'
                elif dataset==options.datasetName: text += str(rateTriggerDataset[(dataset,trigger)]) + '\t±\t' + str(sqrtMod(squaredErrorRateTriggerDataset[(dataset,trigger)])) + '\t'
                else: text += str(0) + '\t±\t' +str(0) + '\t'
            else: text += str(rateTriggerDataset[(dataset,trigger)]) + '\t±\t' + str(sqrtMod(squaredErrorRateTriggerDataset[(dataset,trigger)])) + '\t'

    f.write(text)
    f.close()

## Use this for L1Rate studies (L1Rates scaling with luminosity and NofBunches); only if you use the new format of L1TriggersMap.
def writeL1RateStudies(fileName,prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,triggerList,writeGroup=False):
    f = open(fileName, 'w')
    text = 'L1 path\t'
    if writeGroup: text += 'Group\t'
    text += 'Prescale\t'
    text += 'Total Rate (Hz)\t\t\t'
    
## For each L1 configuration , prepare Rates scaled by the target luminosity:
    text += '1e34\t\t\t'; text += '7e33\t\t\t'; text += '5e33\t\t\t'
    text += '3.5e33\t\t\t'; text += '2e33\t\t\t'; text += '1e33\t\t\t' 
    
    for trigger in triggersL1GroupMap.keys():
        text += '\n'
        text +=  trigger+'\t'

        if writeGroup:
            text += str(triggersL1GroupMap[trigger][0])
            text += '\t'
        text += str(prescaleList[trigger])+'\t'
        text += str(rateTriggerTotal[trigger])+'\t±\t'+str(sqrtMod(squaredErrorRateTriggerTotal[trigger]))+'\t'

     ## For each L1 trigger that is not Masked, compute the ratio between the target and the original prescale:
        for idx in range(2, 8):
            ratio = int(triggersL1GroupMap[trigger][idx])/prescaleList[trigger]
            text += str(ratio*rateTriggerTotal[trigger])+'\t±\t'+str(sqrtMod(squaredErrorRateTriggerTotal[trigger]))+'\t'

    f.write(text)
    f.close()
    
## compare the trigger list from the ntuple and from triggersGroupMap*.py and print the difference
def CompareGRunVsGoogleDoc(datasetList,triggerList,folder):
    # take the first "hltbit" file
    dirpath = ''
    filenames = []
 
    for dataset in datasetList:
        datasetName = dataset
        noRootFile = True
        onlyFail = False
        walking_folder = folder+"/"+datasetName
        eosDirContent = []
        lsl(walking_folder,eosDirContent)
        for key in eosDirContent:
            if (("failed" in str(key['path'])) or ("log" in str(key['path']))):
                onlyFail = True
                continue
            elif ("root" in str(key['file'])):
                filenames.append("root://eoscms//eos/cms"+str(key['path'])+'/'+str(key['file']))
                dirpath = "root://eoscms//eos/cms/"+walking_folder
                noRootFile = False
                onlyFail = False
                break
        if len(filenames)>0: break 
    if len(filenames)==0:
        raise ValueError('No good file found in '+folder)
    
    for filename in filenames:
        if 'hltbit' in filename: break
    
    _file0 = ROOT.TFile.Open(filename)
    chain = ROOT.gDirectory.Get("HltTree")
    
    # get trigger bits and make a comparison with google DOC
    triggerListInNtuples = []
    getTriggersListFromNtuple(chain,triggerListInNtuples)
    intersection = set(triggerListInNtuples).intersection(triggerList)
    diffTriggersGRun = triggerListInNtuples [:]
    diffTriggersGoogle = triggerList [:]

    for i in intersection:
        diffTriggersGRun.remove(i)
        diffTriggersGoogle.remove(i)

    diffTriggersGRun.sort()
    diffTriggersGoogle.sort()
    print 
    print '#'*30,"Triggers only in GRun:",'#'*30
    for t in diffTriggersGRun:
        print t
    print 
    print '#'*30,"Triggers only in Google doc:",'#'*30
    for t in diffTriggersGoogle:
        print t

    for trigger in triggerList:
        if trigger in diffTriggersGoogle: triggerList.remove(trigger)
    
    triggerList = intersection
    return list(triggerList)

## given filepath, the filter string to use at the numerator and denominator, get the number of events that pass the triggers
def getEvents(input_):
    (filepath,filterString,denominatorString,withNegativeWeights) = input_
    print "Entered getEvents()",filepath
    passedEventsMatrix_={}
    WeightedErrorMatrix_={}
    #try to open the file and get the TTree
    tree = None
    _file0 = ROOT.TFile.Open(filepath)
    tree=ROOT.gDirectory.Get("HltTree")
    if not looping:
    ##### "Draw" method
        if (tree!=None): 
        # Creating aliases for HLT paths branches in the tree in order to reduce the length of the global OR string
            i = 0
            root_alias_dic = {}
            for leaf in tree.GetListOfLeaves():
                triggerName = leaf.GetName()
                if (triggerName in triggerList):
                    tree.SetAlias("T_"+str(i),triggerName)
                    if not triggerName in root_alias_dic:
                        root_alias_dic[triggerName] = "T_"+str(i)
                    i += 1
    
            getTriggerString1={}
            for t in getTriggerString:
                getTriggerString1[t]=getTriggerString[t]
            for group in groupList:
                groupPathList = getTriggerString1[group].split('||')
                print getTriggerString1[group]
                print "*"*50
                getTriggerString1[group] = '0'
                for triggerPath in groupPathList:
                    if triggerPath in triggerList:
                        triggerAlias = root_alias_dic[triggerPath] 
                        if getTriggerString1[group]!='0': getTriggerString1[group] += '||'+triggerAlias
                        else: getTriggerString1[group] = triggerAlias
                print getTriggerString1[group]
                print "*"*50
    
    
            for dataset in primaryDatasetList:
                datasetPathList = getTriggerString1[dataset].split('||')
                print getTriggerString1[dataset]
                print "*"*50
                getTriggerString1[dataset] = '0'
                for triggerPath in datasetPathList:
                    if triggerPath in triggerList:
                        triggerAlias = root_alias_dic[triggerPath]
                        if getTriggerString1[dataset]!='0': getTriggerString1[dataset] += '||'+triggerAlias
                        else: getTriggerString1[dataset] = triggerAlias
                print getTriggerString1[dataset]
                print "*"*50

        #if tree is defined, get totalEvents and passedEvents
        if (tree!=None): 
            if isData:
                totalEventsMatrix_ = tree.Draw("",denominatorString) 
                if withNegativeWeights: totalEventsMatrix_= totalEventsMatrix_ - 2*tree.Draw("",'(MCWeightSign<0)&&('+denominatorString+')')
                for trigger in triggerAndGroupList:
                    passedEventsMatrix_[trigger] = tree.Draw("",'('+getTriggerString1[trigger]+')&&('+filterString+')')
                    if withNegativeWeights: passedEventsMatrix_[trigger] = passedEventsMatrix_[trigger] - 2*tree.Draw("",'(MCWeightSign<0)&&('+getTriggerString1[trigger]+')&&('+filterString+')')
            else:
                totalEventsMatrix_ = tree.Draw("",'('+denominatorString+')&&(NPUTrueBX0<='+str(pileupMAX)+')&&(NPUTrueBX0>='+str(pileupMIN)+')')
                if withNegativeWeights: totalEventsMatrix_= totalEventsMatrix_ - 2*tree.Draw("",'(MCWeightSign<0)&&('+denominatorString+')&&(NPUTrueBX0<='+str(pileupMAX)+')&&(NPUTrueBX0>='+str(pileupMIN)+')')
                for trigger in triggerAndGroupList:
                    passedEventsMatrix_[trigger] = tree.Draw("",'('+getTriggerString1[trigger]+')&&('+filterString+')&&(NPUTrueBX0<='+str(pileupMAX)+')&&(NPUTrueBX0>='+str(pileupMIN)+')')
                    if withNegativeWeights: passedEventsMatrix_[trigger] = passedEventsMatrix_[trigger] - 2*tree.Draw("",'(MCWeightSign<0)&&('+getTriggerString1[trigger]+')&&('+filterString+')&&(NPUTrueBX0<='+str(pileupMAX)+')&&(NPUTrueBX0>='+str(pileupMIN)+')')
            _file0.Close()
        else:  #if tree is not undefined/empty set enties to zero
            totalEventsMatrix_ = 0
            for trigger in triggerAndGroupList:
                passedEventsMatrix_[trigger] = 0
    
    ##### Looping method
    else:
        #if tree is defined, get totalEvents and passedEvents
        if (tree!=None):
            if isData:
#                print denominatorString
                totalEventsMatrix_ = tree.Draw("",denominatorString)
                if withNegativeWeights: totalEventsMatrix_= totalEventsMatrix_ - 2*tree.Draw("","(MCWeightSign<0)&&("+denominatorString+")")
            else:
                totalEventsMatrix_ = tree.Draw("",'('+denominatorString+')&&(NPUTrueBX0<='+str(pileupMAX)+')&&(NPUTrueBX0>='+str(pileupMIN)+')')
                if withNegativeWeights: totalEventsMatrix_= totalEventsMatrix_ - 2*tree.Draw("","(MCWeightSign<0)&&("+denominatorString+")&&(NPUTrueBX0<="+str(pileupMAX)+")&&(NPUTrueBX0>="+str(pileupMIN)+")") 
            N = tree.GetEntries()
            if evalHLTpaths: passedEventsMatrix_['All_HLT'] = 0
            if evalL1: passedEventsMatrix_['L1'] = 0

            i = 0

            presclFromMap = False
            lumiColumn = 1
            # Filling the prescale dictionary using the map
            if (presclFromMap):
                for trigger in triggersL1GroupMap.keys():
                    L1PrescDict[trigger] = triggersL1GroupMap[trigger][lumiColumn]
        
            for trigger in triggerAndGroupList:
                passedEventsMatrix_[trigger] = 0
                WeightedErrorMatrix_[trigger] = 0
            # Looping over the events to compute the rates
            u = 0
            #N = 100.
            print "Nevents =",N
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#            for leaf in tree.GetListOfLeaves():
#                triggerName = leaf.GetName()
#                if (tree.Draw("",triggerName)) != 0:
#                    for event in tree:                        
#                        #print '%s : %d , value : %d'%(triggerName,tree.Draw("",triggerName),getattr(event,triggerName))
#                        break
            global Total_count
#            print '%s : %d , total : %d'%("HLT_Mu20_v3",tree.Draw("","HLT_Mu20_v3"),Total_count)
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            for event in tree:
                if (int(runNo) != 0 and int(getattr(event,'Run')) != int(runNo)):continue
                if int(getattr(event,'LumiBlock')) < int(LS_min) or int(getattr(event,'LumiBlock')) > int(LS_max):continue
                #if u==N: break
                if u%(N/50)==0: print "\r{0:.1f} %".format(100*float(u)/float(N))
                u += 1 
                Total_count += 1 
                if isData: PUevent = 0
                else: PUevent = getattr(event,"NPUTrueBX0")
                if (PUevent>pileupMAX or PUevent<pileupMIN): continue
                HLTCount = 0
                L1Count = 0
                L1Presc = 0
                filterFloat = 1
                stringMemory = ""
                psMultiple = False
                for trigger in triggerAndGroupList:
                    if getTriggerString[trigger] == '0':continue
                    if trigger in groupList: 
                        triggerInGroupList = getTriggerString[trigger].split('||')
                        psMultiple = False
                        tempCount = 1e+10 
                        for path in triggerInGroupList:     
                            if not (path in triggerAndGroupList):continue
                            if (path not in prescaleMap.keys()) or int(prescaleMap[path][0])==0 or prescaleMap[path][0]=='' or 'DST_' in path or 'AlCa_' in path: continue 
                            HLTCount = getattr(event,path) 
                            if HLTCount and filterFloat and (int(prescaleMap[path][0])<tempCount): tempCount = int(prescaleMap[path][0])
                        if tempCount==1e+10: continue
                        passedEventsMatrix_[trigger] += 1/float(tempCount)
                        WeightedErrorMatrix_[trigger] += (1/float(tempCount))*(1/float(tempCount))
                    elif trigger in primaryDatasetList:
                        triggerInDatasetList = getTriggerString[trigger].split('||')
                        psMultiple = False
                        tempCount = 1e+10
                        for path in triggerInDatasetList:
                            if not (path in triggerAndGroupList):continue
                            if (path not in prescaleMap.keys()) or int(prescaleMap[path][0])==0 or prescaleMap[path][0]=='': continue
                            HLTCount = getattr(event,path)
                            if HLTCount and filterFloat and (int(prescaleMap[path][0])<tempCount): tempCount = int(prescaleMap[path][0])
                        if tempCount==1e+10: continue
                        passedEventsMatrix_[trigger] += 1/float(tempCount)
                        WeightedErrorMatrix_[trigger] += (1/float(tempCount))*(1/float(tempCount))
                    else:
                        if (trigger not in prescaleMap.keys()) or int(prescaleMap[trigger][0])==0 or prescaleMap[trigger][0]=='': continue 
                        else: 
                            HLTCount = getattr(event,trigger)
                            if (HLTCount==1 and filterFloat==1):
                                #passedEventsMatrix_[trigger] += 1
                                passedEventsMatrix_[trigger] += 1/float(prescaleMap[trigger][0])
                                WeightedErrorMatrix_[trigger] += (1/float(prescaleMap[trigger][0]))*(1/float(prescaleMap[trigger][0]))
                        #print "Event:",u,"passedEventsMatrix_=",passedEventsMatrix_[trigger]

        else:  #if chain is not undefined/empty set entries to zero
            totalEventsMatrix_ = 0
            for trigger in triggerAndGroupList:
                passedEventsMatrix_[trigger] = 0

    return passedEventsMatrix_,totalEventsMatrix_,WeightedErrorMatrix_

## fill the matrixes of the number of events and the rates for each dataset and trigger
Total_count = 0
def fillMatrixAndRates(dataset,totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix,rateTriggerDataset,squaredErrorRateTriggerDataset):
    print "Entered fillMatrixAndRates()"
    start = time.time()
    skip = False

    ## find the subdirectory containing the ROOT files
    dirpath=''
    filenames=[]
    noRootFile = True
    walking_folder = folder+"/"+dataset
    eosDirContent=[]
    lsl(walking_folder,eosDirContent)
    for key in eosDirContent:
        if (("failed" in str(key['path'])) or ("log" in str(key['file'])) or ("160508_132840" in str(key['path']))): continue
        if (".root" in str(key['file'])):
            if batchSplit:
                filenames.append("root://eoscms//eos/cms"+str(key['path'])+'/'+str(key['file']))
                dirpath = "root://eoscms//eos/cms"+walking_folder
            else:
                filenames.append(localdir+str(key['path'])+'/'+str(key['file']))
                dirpath = localdir+walking_folder
            noRootFile = False

    ## print an error if a dataset is missing
    if batchSplit:
        if (dirpath=='' or (len(filenames)<options.fileNumber)):
            print
            print '#'*80
            print '#'*10,"dataset=",dataset," not found!"
            print '#'*80
            skip = True
    else:
        if dirpath=='':
            print
            print '#'*80
            print '#'*10,"dataset=",dataset," not found!"
            print '#'*80
            skip = True
    
    ## get the cross section and the global rate of the dataset
    xsection = xsectionDatasets[dataset] #pb
    if isData:
        rateDataset[dataset] = (1./psNorm)*lenLS*nLS*lumi*xsection
    else:
        print "lumi = ",lumi," xsection = ",xsection
        rateDataset [dataset] = lumi*xsection*1E-24/1E12 # [1b = 1E-24 cm^2, 1b = 1E12pb ]
    
    ## check if the dataset belong to the (anti) QCD EM/Mu enriched dataset lists or it contains negative weights
    isEMEnriched = False
    isMuEnriched = False
    isAntiEM = False
    isAntiMu = False
    withNegativeWeights = False
    
    if dataset in datasetEMEnrichedList:        isEMEnriched = True
    if dataset in datasetMuEnrichedList:        isMuEnriched = True
    if dataset in datasetAntiMuList:            isAntiMu = True
    if dataset in datasetAntiEMList:            isAntiEM = True
    if dataset in datasetNegWeightList:         withNegativeWeights = True
    
    filterString = '1'
    if isData and runNo!='0':
        filterString+="&&(Run=="+runNo+")"   
        if LS_min !='0':
            filterString+="&&(LumiBlock>="+LS_min+")&&(LumiBlock<="+LS_max+")"
 
    ## skip file if you have to
    if (not useMuEnriched) and isMuEnriched: skip = True
    if (not useEMEnriched) and isEMEnriched: skip = True
    
    ## apply PU filter
    if pileupFilter and ('QCD'in dirpath):
        if pileupFilterGen: filterString += '&&'+PUFilterGen
        else: filterString += '&&'+PUFilterL1
    
    ## if useEMEnriched, apply AntiEM cut 
    if useEMEnriched and isAntiEM: filterString += '&& !'+EM_cut
    
    ## if useMuEnriched, apply AntiMu cut
    if useMuEnriched and isAntiMu: filterString += '&& !'+Mu_cut
    
    denominatorString = '1'
    if isData and runNo!='0':
        denominatorString+="&&(Run=="+runNo+")"   
        if LS_min !='0':
            denominatorString+="&&(LumiBlock>="+LS_min+")&&(LumiBlock<="+LS_max+")"
    ## if useEMEnriched and is EMEnriched, apply EM cut 
    if useEMEnriched and isEMEnriched:
        filterString += '&& '+EM_cut
        denominatorString += '&& '+EM_cut
    
    ## if useMuEnriched and is MuEnriched, apply Mu cut 
    if useMuEnriched and isMuEnriched:
        filterString += '&& '+Mu_cut
        denominatorString += '&& '+Mu_cut
    
    ## print a log, only for one file per dataset
    if log>1:
        if not skip:
            print
            print '#'*10,"Dataset:",dataset,'#'*30
            print "Loading folder:",walking_folder
            print "First file:",filenames[0]
            print "nfiles =",len(filenames)
            print "total rate of dataset =",rateDataset [dataset]
            print "using numerator filter:",filterString
            print "using denominator filter:",denominatorString
            print "using negative weight? ",withNegativeWeights
        else:
            print
            print '#'*10,"Skipping ",dataset,'#'*30
    
    if not skip:
        ## prepare the input for getEvents((filepath,filterString,denominatorString))
        inputs = []
        i = 1
        for filename in filenames:
            fileTest = ROOT.TFile.Open(filename)
            if fileTest:
                if(batchSplit):
                    if(i==options.fileNumber):
                        print "file ",i," (",filename,") added to inputs"
                        inputs.append((filename,filterString,denominatorString,withNegativeWeights))
                        break
                    elif(options.fileNumber==-1):
                        print "file ",i," (",filename,") added to inputs"
                        inputs.append((filename,filterString,denominatorString,withNegativeWeights))
                else: inputs.append((filename,filterString,denominatorString,withNegativeWeights))
            i += 1
            #if i==16:break
 
        ## evaluate the number of events that pass the trigger with getEvents()
        if multiprocess>1:
            p = Pool(multiprocess)
            output = p.map(getEvents, inputs)
    
        ## get the output
        for input_ in inputs:
            if multiprocess>1: (passedEventsMatrix_,totalEventsMatrix_,WeightedErrorMatrix_) = output[inputs.index(input_)]
            else: (passedEventsMatrix_,totalEventsMatrix_,WeightedErrorMatrix_) = getEvents(input_)
        
            ##fill passedEventsMatrix[] and totalEventsMatrix[]
            totalEventsMatrix[dataset] += totalEventsMatrix_
            for trigger in triggerAndGroupList:
                passedEventsMatrix[(dataset,trigger)] += passedEventsMatrix_[trigger]
                WeightedErrorMatrix[(dataset,trigger)] += WeightedErrorMatrix_[trigger]
        
        ##fill rateTriggerDataset[(dataset,trigger)] and squaredErrorRateTriggerDataset[(dataset,trigger)]
        if evalHLTtwogroups:
            f = ROOT.TFile("twoGroupsCorrelations.root","recreate")
            ROOT.gStyle.SetOptStat(0)
            GroupCorrelHisto = ROOT.TH2F('GroupCorrelHisto','Overlapping rates for group pairs', 21, 0, 21, 21, 0, 21)
            i = 0
            j = 0
            L2g = len(twoGroupsList)
            N2g = (-1+math.pow(1+(8*L2g),0.5))/2
        for trigger in triggerAndGroupList:
            if isData:
                #print passedEventsMatrix[(dataset,trigger)], rateDataset[dataset]
                rateTriggerDataset[(dataset,trigger)] = passedEventsMatrix[(dataset,trigger)]/rateDataset[dataset]
                squaredErrorRateTriggerDataset[(dataset,trigger)] = passedEventsMatrix[(dataset,trigger)]/(rateDataset[dataset]*rateDataset[dataset])
                if evalHLTtwogroups:
                    if trigger in twoGroupsList:
                        if(i<N2g and j<N2g):
                            GroupCorrelHisto.SetBinContent(i,j,rateTriggerDataset[(dataset,trigger)])
                            i += 1
                        elif(i==N2g and j<(N2g-1)):
                            i = j+1
                            j += 1
                            GroupCorrelHisto.SetBinContent(i,j,rateTriggerDataset[(dataset,trigger)])
                            i += 1
            else:
                rateTriggerDataset [(dataset,trigger)] = rateDataset[dataset]/totalEventsMatrix[dataset]*passedEventsMatrix[(dataset,trigger)]
                squaredErrorRateTriggerDataset [(dataset,trigger)] = rateDataset[dataset]*rateDataset[dataset]*passedEventsMatrix[(dataset,trigger)]/totalEventsMatrix[dataset]/totalEventsMatrix[dataset] # (rateDataset*sqrt(1.*passedEvents/nevents/nevents)) **2               
        if evalHLTtwogroups:
            i = 1
            for group in groupList:
                if group != "Masked":
                    GroupCorrelHisto.GetXaxis().SetBinLabel(i,group)
                    GroupCorrelHisto.GetXaxis().LabelsOption("v")
                    GroupCorrelHisto.GetYaxis().SetBinLabel(i,group)
                    GroupCorrelHisto.GetYaxis().LabelsOption("v")
                    i += 1
            f.Write()
    ## do not crash if a dataset is missing!
    else:
        totalEventsMatrix[dataset]=1
        for trigger in triggerAndGroupList:
                passedEventsMatrix[(dataset,trigger)] = 0

        rateTriggerDataset [(dataset,trigger)] = 0
        squaredErrorRateTriggerDataset [(dataset,trigger)] = 0

    end = time.time()
    if log>1:
        if not skip: print "time(s) =",round((end - start),2)," total events=",totalEventsMatrix[dataset]," time per 10k events(s)=", round((end - start)*10000/totalEventsMatrix[dataset],2)

########## Main #####################################################################

## start the script
startGlobal = time.time() ## timinig stuff

## fill datasetList properly
datasetList+=datasetEMEnrichedList
datasetList+=datasetMuEnrichedList

## print a log
print
print "Using up to ", multiprocess ," processes."
print "Folder: ", folder
print "Luminosity: ", lumi
print "Use QCDEMEnriched? ", useEMEnriched
print "Use QCDMuEnriched? ", useMuEnriched
print "Evaluate L1 triggers rates? ", evalL1
print "Evaluate HLT triggers rates? ", evalHLTpaths
#print "Evaluate HLT triggers shared rates? ", evalHLTtwopaths
print "Evaluate HLT groups rates? ", evalHLTgroups
print "Evaluate HLT groups shared rates? ", evalHLTtwogroups
print "Pile-up filter: ",pileupFilter
if pileupFilter:
    print "Pile-up filter version: ",
    if pileupFilterGen:
        print "pt-hat MC truth (new)"
    else:
        print "leading L1 object (old)"

print

# load library for multiprocessing
if multiprocess>1: 
    from multiprocessing import Pool

### initialization ###
# fill triggerAndGroupList with the objects that you want to measure the rate (HLT+L1+HLTgroup+HLTtwogroup)
triggerAndGroupList=[]
#if not evalL1: groupList.remove('L1')
#if not evalHLTpaths : groupList.remove('All_HLT')
if evalHLTpaths:
    HLTList = CompareGRunVsGoogleDoc(datasetList,HLTList,folder)
    triggerAndGroupList=triggerAndGroupList+HLTList
if evalL1:              
    L1List = CompareGRunVsGoogleDoc(datasetList,L1List,folder)
    triggerAndGroupList=triggerAndGroupList+L1List

if evalHLTprimaryDatasets: triggerAndGroupList=triggerAndGroupList+primaryDatasetList
if evalHLTgroups:       triggerAndGroupList=triggerAndGroupList+groupList
#if evalHLTtwopaths:     triggerAndGroupList=triggerAndGroupList+twoHLTsList
if evalHLTtwogroups:    triggerAndGroupList=triggerAndGroupList+twoGroupsList
#if evalL1:              triggerAndGroupList=triggerAndGroupList+L1List


# fill triggerList with the trigger HLT+L1
#triggerList=[]
#if evalHLTpaths:        triggerList=triggerList+HLTList
#if evalL1:              triggerList=triggerList+L1List
## check trigger list in triggersGroupMap (ie. ~ Google doc), with trigger bits in ntuples (ie. GRun)
if evalHLTpaths or evalL1: triggerList = CompareGRunVsGoogleDoc(datasetList,triggerList,folder)


# define dictionaries
passedEventsMatrix = {}                 #passedEventsMatrix[(dataset,trigger)] = events passed by a trigger in a dataset
WeightedErrorMatrix = {}
totalEventsMatrix = {}                  #totalEventsMatrix[(dataset,trigger)] = total events of a dataset
rateDataset = {}                        #rateDataset[dataset] = rate of a dataset (xsect*lumi)
rateTriggerDataset = {}                 #rateTriggerDataset[(dataset,trigger)] = rate of a trigger in a dataset
squaredErrorRateTriggerDataset = {}     #squaredErrorRateTriggerDataset[(dataset,trigger)] = squared error on the rate
rateTriggerTotal = {}                   #rateTriggerTotal[(dataset,trigger)] = total rate of a trigger
squaredErrorRateTriggerTotal = {}       #squaredErrorRateTriggerTotal[trigger] = squared error on the rate
setToZero(totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix,triggerAndGroupList,rateTriggerTotal,squaredErrorRateTriggerTotal)  #fill all dictionaries with zero

## create a list with prescales associated to each HLT/L1 trigger path
prescaleList = {}               # prescaleTriggerTotal[trigger] = prescale from Ntuple                                             
prescaleList = getPrescaleListInNtuples()                                                                                             
#print prescaleList       

## loop on dataset and fill matrix with event counts, rates, and squared errors
for dataset in datasetList:
    if batchSplit:
        if options.datasetName=="all": fillMatrixAndRates(dataset,totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix,rateTriggerDataset,squaredErrorRateTriggerDataset)
        elif dataset==options.datasetName:
            fillMatrixAndRates(dataset,totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix,rateTriggerDataset,squaredErrorRateTriggerDataset)
            break
    else: fillMatrixAndRates(dataset,totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix,rateTriggerDataset,squaredErrorRateTriggerDataset)

## evaluate the total rate with uncertainty for triggers and groups
for dataset in datasetList:
    if batchSplit:
        if options.datasetName=="all":
            for trigger in triggerAndGroupList:
                    rateTriggerTotal[trigger] += rateTriggerDataset[(dataset,trigger)]
                    squaredErrorRateTriggerTotal[trigger] += squaredErrorRateTriggerDataset[(dataset,trigger)]
        elif dataset==options.datasetName:
            for trigger in triggerAndGroupList:
                    rateTriggerTotal[trigger] += rateTriggerDataset[(dataset,trigger)]
                    squaredErrorRateTriggerTotal[trigger] += squaredErrorRateTriggerDataset[(dataset,trigger)]
            break
    else:
        for trigger in triggerAndGroupList:
                    rateTriggerTotal[trigger] += rateTriggerDataset[(dataset,trigger)]
                    squaredErrorRateTriggerTotal[trigger] += squaredErrorRateTriggerDataset[(dataset,trigger)]

if batchSplit: directoryname = 'ResultsBatch/'
else: directoryname = 'Results/'
filename = ''
filename += label
filename += "_"+triggerName
filename += "_"+str(lumi).replace("+","")
if pileupFilter:
    if pileupFilterGen:filename += '_PUfilterGen'
    else:filename += '_PUfilterL1'

if useEMEnriched: filename += '_EMEn'
if useMuEnriched: filename += '_MuEn'


if batchSplit:

    try:
        #mkdir("ResultsBatch_Parking2_Parking3")
        if not os.path.exists(directoryname+"ResultsBatch_Events"): os.makedirs(directoryname+"ResultsBatch_Events")
        if not os.path.exists(directoryname+"ResultsBatch_groupEvents"): os.makedirs(directoryname+"ResultsBatch_groupEvents")
        if not os.path.exists(directoryname+"ResultsBatch_primaryDatasetEvents"): os.makedirs(directoryname+"ResultsBatch_primaryDatasetEvents")
    except:
        pass

    ### write files with events count
    if evalL1: writeMatrixEvents(filename+'_L1_matrixEvents_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',datasetList,L1List,totalEventsMatrix,passedEventsMatrix,True,False)
    if evalHLTpaths: writeMatrixEvents(directoryname+'ResultsBatch_Events/'+filename+'_matrixEvents_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',datasetList,HLTList,totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix,True,True)
    if evalHLTprimaryDatasets: writeMatrixEvents(directoryname+'ResultsBatch_primaryDatasetEvents/'+filename+'_matrixEvents_primaryDataset_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',datasetList,primaryDatasetList,totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix)
    if evalHLTgroups: writeMatrixEvents(directoryname+'ResultsBatch_groupEvents/'+filename+'_matrixEvents_groups_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',datasetList,groupList,totalEventsMatrix,passedEventsMatrix,WeightedErrorMatrix)
    if evalHLTtwogroups: writeMatrixEvents(filename+'_matrixEvents.twogroups_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',datasetList,twoGroupsList,totalEventsMatrix,passedEventsMatrix)


    ### write files with  trigger rates
    if evalL1:writeMatrixRates(filename+'_L1_matrixRates_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,L1List,True,False)
    if evalHLTpaths: writeMatrixRates(directoryname+filename+'_matrixRates_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,HLTList,True,True)
    if evalHLTprimaryDatasets: writeMatrixRates(directoryname+filename+'_matrixRates.primaryDataset_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,primaryDatasetList)
    if evalHLTgroups: writeMatrixRates(directoryname+filename+'_matrixRates.groups_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,groupList)
    if evalHLTtwogroups: writeMatrixRates(filename+'_matrixRates.twogroups_'+str(options.datasetName)+'_'+str(options.fileNumber)+'.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,twoGroupsList)

else:
    try:
        mkdir("Results")
    except:
        pass

    ## write files with events count
    if evalL1: writeMatrixEvents(filename+'_L1_matrixEvents.tsv',datasetList,L1List,totalEventsMatrix,passedEventsMatrix,True,False)
    if evalHLTpaths: writeMatrixEvents(directoryname+filename+'_matrixEvents.tsv',datasetList,HLTList,totalEventsMatrix,passedEventsMatrix,True,True)
    if evalHLTprimaryDatasets: writeMatrixEvents(directoryname+filename+'_matrixEvents.primaryDataset.tsv',datasetList,primaryDatasetList,totalEventsMatrix,passedEventsMatrix)
    if evalHLTgroups: writeMatrixEvents(directoryname+filename+'_matrixEvents.groups.tsv',datasetList,groupList,totalEventsMatrix,passedEventsMatrix)
    if evalHLTtwogroups: writeMatrixEvents(filename+'_matrixEvents.twogroups.tsv',datasetList,twoGroupsList,totalEventsMatrix,passedEventsMatrix)

    ## write files with  trigger rates
    if evalL1: writeMatrixRates(filename+'_L1_matrixRates.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,L1List,True,False)
    ##if evalL1scaling: writeL1RateStudies(filename+'_L1RateStudies_matrixRates.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,L1List,True)
    if evalHLTpaths: writeMatrixRates(directoryname+filename+'_matrixRates.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,HLTList,True,True)
    if evalHLTprimaryDatasets: writeMatrixRates(directoryname+filename+'_matrixRates.primaryDataset.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,primaryDatasetList)
    if evalHLTgroups: writeMatrixRates(directoryname+filename+'_matrixRates.groups.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,groupList)
    if evalHLTtwogroups: writeMatrixRates(filename+'_matrixRates.twogroups.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,twoGroupsList)


## print timing
endGlobal = time.time()
totalEvents = 0
for dataset in datasetList: totalEvents+=totalEventsMatrix[dataset]
print
print "Total Time=",round((endGlobal - startGlobal),2)," Events=",totalEvents," TimePer10kEvent=", round((endGlobal - startGlobal)*10000/totalEvents,2)




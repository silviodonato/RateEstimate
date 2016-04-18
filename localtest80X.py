#! /usr/bin/env python
# -*- coding: iso-8859-15 -*-

########## Configuration #####################################################################
#from triggersGroupMap.triggersGroupMap__frozen_2015_25ns14e33_v4p4_HLT_V1 import *
#from datasetCrossSections.datasetCrossSectionsPhys14 import *
#from datasetCrossSections.datasetCrossSectionsSpring15 import *
from datasetCrossSections.datasetLumiSectionsData import *

batchSplit = False
looping = True
folder = '/afs/cern.ch/user/x/xgao/CMSSW_8_0_3_patch1/src/RateEstimate/259721'
#folder = '/afs/cern.ch/user/x/xgao/CMSSW_8_0_3_patch1/src/MyTests/localtest'
lumi =  1#2E33              # luminosity [s-1cm-2]
if (batchSplit): multiprocess = 1           # number of processes
else: multiprocess = 8
pileupFilter = False        # use pile-up filter?
pileupFilterGen = False    # use pile-up filter gen or L1?
useEMEnriched = False       # use plain QCD mu-enriched samples (Pt30to170)?
useMuEnriched = False       # use plain QCD EM-enriched samples (Pt30to170)?
evalL1 = False              # evaluate L1 triggers rates?
evalHLTpaths = True        # evaluate HLT triggers rates?
evalHLTgroups = False       # evaluate HLT triggers groups rates and global HLT and L1 rates
#evalHLTtwopaths = True    # evaluate the correlation among the HLT trigger paths rates?
evalHLTtwogroups = False   # evaluate the correlation among the HLT trigger groups rates?
label = "rates_v4p4_V3_100K"         # name of the output files
runNo = "259721"


isData = True
## L1Rate studies as a function of PU and number of bunches:
evalL1scaling = False

nLS = 334 ## number of Lumi Sections run over data
lenLS = 23.31 ## length of Lumi Section
psNorm = 445./1. # Prescale Normalization factor if running on HLTPhysics
###############################################################################################

##### Adding an option to the code #####

if batchSplit:
    from optparse import OptionParser
    parser=OptionParser()

    parser.add_option("-n","--number",dest="fileNumber",default="0",type="int") # python file.py -n N => options.fileNumber is N
    (options,args)=parser.parse_args()

##### Other configurations #####

## log level
log = 2                     # use log=2

## filter to be used for QCD EM/Mu enriched
EM_cut = "(!HLT_BCToEFilter_v1 && HLT_EmFilter_v1)"
Mu_cut = "MCmu3"

## filter to be used for pile-up filter
PUFilterGen = 'HLT_RemovePileUpDominatedEventsGen_v1'
PUFilterL1 = 'HLT_RemovePileUpDominatedEvents_v1'

##### Load lib #####

import ROOT
import time
import sys
from math import *
from os import walk
from os import mkdir
from scipy.stats import binom

ROOT.TFormula.SetMaxima(10000,10000,10000) # Allows to extend the number of operators in a root TFormula. Needed to evaluate the .Draw( ,OR string) in the GetEvents function

##### Function definition #####

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
        for (dirpath_, dirnames, filenames_) in walk(folder+'/'+dataset):                                                          
            if len(filenames_)>0 and 'root' in filenames_[0]:                                                                      
                filenames = filenames_                                                                                             
                dirpath = dirpath_                                                                                                 
                break                                                                                                              
                                                                                                                                   
    if len(filenames)==0:                                                                                                          
        raise ValueError('No good file found in '+folder)                                                                          
                                                                                                                                   
    for filename in filenames:                                                                                                     
        if 'hltbit' in filename: break                                                                                             
                                                                                                                                   
    _file0 = ROOT.TFile.Open(dirpath+'/'+filename)                                                                                 
    chain = ROOT.gDirectory.Get("HltTree")                                                                                         
            
    triggerlist=[]                                                                                                                       
    for leaf in chain.GetListOfLeaves():                                                                                           
        name = leaf.GetName()                                                                                                      
        if (("HLT_" in name) or (evalL1 and ("L1_" in name))) and not ("Prescl" in name):                                          
            trigger=name                                                                                                           
            i=0                                                                                                                    
            pname=name+'_Prescl'
            if pname not in chain.GetListOfLeaves():continue                                                                                                   
            for event in chain:                                                                                                    
                value=getattr(event,pname)                                                                                         
                if (i==2): break                                                                                                   
                i+=1                                                                                                               
            prescales[trigger]=value
            triggerlist.append(trigger)     
            getTriggerString[trigger]=trigger                                                                                          
            triggersGroupMap[trigger]=['none']

    return prescales,triggerlist       

## set and fill totalEventsMatrix, passedEventsMatrix, rateTriggerTotal, squaredErrorRateTriggerTotal with zero
def setToZero(totalEventsMatrix,passedEventsMatrix,triggerAndGroupList,rateTriggerTotal,squaredErrorRateTriggerTotal) :
    for dataset in xsectionDatasets:
        totalEventsMatrix[dataset]=0
        for trigger in triggerAndGroupList:
            passedEventsMatrix[(dataset,trigger)]=0
    
    for trigger in triggerAndGroupList:
        rateTriggerTotal[trigger]=0
        squaredErrorRateTriggerTotal[trigger]=0

## read totalEventsMatrix and passedEventsMatrix and write a .tsv file containing the number of events that passed the trigger
def writeMatrixEvents(fileName,datasetList,triggerList,totalEventsMatrix,passedEventsMatrix,writeGroup=False):
    f = open(fileName, 'w')
    text = 'Path\t' 
    if writeGroup: text += 'Group\t'
    for dataset in datasetList:
        datasetName = dataset[:-21]
        datasetName = datasetName.replace("-", "")
        datasetName = datasetName.replace("_", "")
        text +=  datasetName + '\t'

    text += '\n'
    text +=  'TotalEvents\t'
    if writeGroup: text += '\t'
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
        
        for dataset in datasetList:
            text += str(passedEventsMatrix[(dataset,trigger)]) + '\t'

    f.write(text)
    f.close()

## read rateTriggerTotal and rateTriggerDataset and write a .tsv file containing the trigger rates
def writeMatrixRates(fileName,prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,triggerList,writeGroup=False):
    f = open(fileName, 'w')
    text = 'Prescale\t'
    text += 'Path\t'
    if writeGroup: text += 'Group\t'
    text += 'Total\t\t\t'
    for dataset in datasetList:
        datasetName = dataset[:-21]
        datasetName = datasetName.replace("-", "")
        datasetName = datasetName.replace("_", "")
        text +=  datasetName + '\t\t\t'

    for trigger in triggerList:
        text += '\n'
        if (trigger not in groupList ):
            text += str(prescaleList[trigger])+'\t'
        else: text += ''+'\t'    
        text +=  trigger+'\t'
        if writeGroup:
            for group in triggersGroupMap[trigger]:
                if not group.isdigit(): text += group+','
        
            #text=text[:-1] ##remove the last comma
            text += '\t'
        
        text += str(rateTriggerTotal[trigger])+'\t±\t'+str(sqrtMod(squaredErrorRateTriggerTotal[trigger]))+'\t'
        for dataset in datasetList:
            text += str(rateTriggerDataset[(dataset,trigger)]) + '\t±\t' + str(sqrtMod(squaredErrorRateTriggerDataset[(dataset,trigger)])) + '\t'

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
        text += str(rateTriggerTotal[trigger])+'\t�\t'+str(sqrtMod(squaredErrorRateTriggerTotal[trigger]))+'\t'

     ## For each L1 trigger that is not Masked, compute the ratio between the target and the original prescale:
        for idx in range(2, 8):
            ratio = int(triggersL1GroupMap[trigger][idx])/prescaleList[trigger]
            text += str(ratio*rateTriggerTotal[trigger])+'\t�\t'+str(sqrtMod(squaredErrorRateTriggerTotal[trigger]))+'\t'

    f.write(text)
    f.close()
    
## compare the trigger list from the ntuple and from triggersGroupMap*.py and print the difference
def CompareGRunVsGoogleDoc(datasetList,triggerList,folder):
    # take the first "hltbit" file
    dirpath = ''
    filenames = []
    for dataset in datasetList:
        for (dirpath_, dirnames, filenames_) in walk(folder+'/'+dataset):
            if len(filenames_)>0 and 'root' in filenames_[0]:
                filenames = filenames_
                dirpath = dirpath_
                break
    
    if len(filenames)==0:
        raise ValueError('No good file found in '+folder)
    
    for filename in filenames:
        if 'hltbit' in filename: break
    
    _file0 = ROOT.TFile.Open(dirpath+'/'+filename)
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
    return triggerList

## given filepath, the filter string to use at the numerator and denominator, get the number of events that pass the triggers
def getEvents(input_):
    (filepath,filterString,denominatorString,withNegativeWeights) = input_
    passedEventsMatrix_={}
    #try to open the file and get the TTree
    tree = None
    try:
       _file0 = ROOT.TFile.Open(filepath)
       tree=ROOT.gDirectory.Get("HltTree")
    except:
        pass

    ##### "Draw" method
    if not looping:
   
        # Creating aliases for HLT paths branches in the tree in order to reduce the length of the global OR string
        i = 0
        for leaf in tree.GetListOfLeaves():
            triggerName = leaf.GetName()
            if ("HLT_" in triggerName) and not ("Prescl" in triggerName):
                tree.SetAlias("HLT_"+str(i),triggerName)
                i += 1
        # Creating aliases for L1 paths branches in the tree in order to reduce the length of the global OR string
        i = 0
        for leaf in tree.GetListOfLeaves():
            triggerName = leaf.GetName()
            if ("L1_" in triggerName) and not ("Prescl" in triggerName) and not ("HLT_" in triggerName):
                tree.SetAlias("L1_"+str(i),triggerName)
                i += 1
 
        #if tree is defined, get totalEvents and passedEvents
        if (tree!=None): 
            totalEventsMatrix_ = tree.Draw("",denominatorString)
            if (totalEventsMatrix_ != 0):
                if withNegativeWeights: totalEventsMatrix_= totalEventsMatrix_ - 2*tree.Draw("","(MCWeightSign<0)&&("+denominatorString+")")
                for trigger in triggerAndGroupList:
                    #print '*** getEvents ***',trigger
                    passedEventsMatrix_[trigger] = tree.Draw("",'('+getTriggerString[trigger]+')&&('+filterString+')')
                    if withNegativeWeights: passedEventsMatrix_[trigger] = passedEventsMatrix_[trigger] - 2*tree.Draw("",'(MCWeightSign<0)&&('+getTriggerString[trigger]+')&&('+filterString+')')
            else:
                totalEventsMatrix_ = 0
                for trigger in triggerAndGroupList:
                    passedEventsMatrix_[trigger] = 0 
            _file0.Close()
        else:  #if tree is not undefined/empty set enties to zero
            totalEventsMatrix_ = 0
            for trigger in triggerAndGroupList:
                passedEventsMatrix_[trigger] = 0
    
    ##### Looping method
    else:
        #if tree is defined, get totalEvents and passedEvents
        if (tree!=None):
            totalEventsMatrix_ = tree.Draw("",denominatorString)
            if (totalEventsMatrix_ != 0):
                if withNegativeWeights: totalEventsMatrix_= totalEventsMatrix_ - 2*tree.Draw("","(MCWeightSign<0)&&("+denominatorString+")")
    
                N = tree.GetEntries()
                if evalHLTpaths: passedEventsMatrix_['All_HLT'] = 0
                if evalL1: passedEventsMatrix_['L1'] = 0
    
                HLTNames = []
                L1Names = []
                L1PrescDict = {}
                i = 0
                for leaf in tree.GetListOfLeaves():
                    triggerName = leaf.GetName()
                    if (evalHLTpaths) and ("HLT_" in triggerName) and not ("Prescl" in triggerName):
                        HLTNames.append(triggerName)
                    elif (evalL1) and ("L1_" in triggerName) and not ("HLT_" in triggerName) and not ("Prescl" in triggerName):
                        L1Names.append(triggerName)
    
                HLTNames.remove("HLT_Physics_v2")
                presclFromMap = False
                lumiColumn = 1
                # Filling the prescale dictionary using the map
                if (presclFromMap):
                    for trigger in triggersL1GroupMap.keys():
                        L1PrescDict[trigger] = triggersL1GroupMap[trigger][lumiColumn]
                # Filling the prescale dictionary using the tree
                else:
                    for event in tree:
                        for trigger in L1Names: L1PrescDict[trigger] = getattr(event,trigger+'_Prescl')
                        break
             
                # Looping over the events to compute the global rate
                nprocessed=0
                for event in tree:
                    nprocessed+=1
                    HLTrun = getattr(event,"Run")
                    if(HLTrun!=int(runNo)):
                        continue
                    HLTCount = 0
                    L1Count = 0
                    L1Presc = 0
                    if HLTNames:
                        for trigger in HLTNames:
                            HLTCount = getattr(event,trigger)
                            if (HLTCount==1):# and filterString==1):
                                passedEventsMatrix_['All_HLT'] += 1
                                #print trigger,'in event : ', nprocessed
                                break
                    if L1Names:
                        for trigger in L1Names:
                            L1Count = getattr(event,trigger)
                            if (L1Count==1) and ((float(i)%L1PrescDict[trigger])==0):# and filterString==1):
                                passedEventsMatrix_['L1'] += 1
                                break
    
                # Using the "Draw" method for the HLT and L1 individual paths part because it is more efficient and there will be no problem with the string length
                if evalHLTpaths:
                    for trigger in HLTList:
                        passedEventsMatrix_[trigger] = tree.Draw("",'('+getTriggerString[trigger]+')&&('+filterString+')')
                if evalL1:
                    for trigger in L1List:
                        passedEventsMatrix_[trigger] = tree.Draw("",'('+getTriggerString[trigger]+')&&('+filterString+')')
                # Using the "Draw" method for the group part because it is more efficient and there will be no problem with the string length
                #for group in groupList:
                   # if (group != 'All_HLT') and (group != 'L1'):
                       # passedEventsMatrix_[group] = tree.Draw("",'('+getTriggerString[group]+')&&('+filterString+')')
            else:  #if chain is not undefined/empty set entries to zero
                totalEventsMatrix_ = 0
                for trigger in triggerAndGroupList:
                    passedEventsMatrix_[trigger] = 0

        else:  #if chain is not undefined/empty set entries to zero
            totalEventsMatrix_ = 0
            for trigger in triggerAndGroupList:
                passedEventsMatrix_[trigger] = 0


    return passedEventsMatrix_,totalEventsMatrix_

## fill the matrixes of the number of events and the rates for each dataset and trigger
def fillMatrixAndRates(dataset,totalEventsMatrix,passedEventsMatrix,rateTriggerDataset,squaredErrorRateTriggerDataset):
    start = time.time()
    skip = False
    dirpath=''
    filenames=[]
    ## find the subdirectory containing the ROOT files
    for (dirpath_, dirnames, filenames_) in walk(folder+'/'+dataset):
        if len(filenames_)>0 and 'root' in filenames_[0]:
            filenames = filenames_
            dirpath = dirpath_
            break
    
    ## print an error if a dataset is missing
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
    if isData:
        filterString+="&&(Run=="+runNo+")"
    
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
    if isData:
        denominatorString+="&&(Run=="+runNo+")"
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
            print "Loading folder:",dirpath
            print "First file:",dirpath+'/'+filenames[0]
            print "nfiles =",len(filenames)
            print "total rate of dataset =",rateDataset [dataset]
            print "using numerator filter:",filterString
            print "using denominator filter:",denominatorString
            print "using negative weight? ",withNegativeWeights
        else:
            print
            print '#'*10,"Skipping ",dataset,'#'*30
    
    ## prepare the input for getEvents((filepath,filterString,denominatorString))
    inputs = []
    i = 0
    if not skip:
        for filename in filenames:
            if(batchSplit):
                if(i==options.fileNumber): inputs.append((dirpath+'/'+filename,filterString,denominatorString,withNegativeWeights))
            else: inputs.append((dirpath+'/'+filename,filterString,denominatorString,withNegativeWeights))
            i += 1
    
    ## evaluate the number of events that pass the trigger with getEvents()
    if multiprocess>1:
        p = Pool(multiprocess)
        output = p.map(getEvents, inputs)
    
    ## get the output
    for input_ in inputs:
        if multiprocess>1: (passedEventsMatrix_,totalEventsMatrix_) = output[inputs.index(input_)]
        else: (passedEventsMatrix_,totalEventsMatrix_) = getEvents(input_)
        
        ##fill passedEventsMatrix[] and totalEventsMatrix[]
        totalEventsMatrix[dataset] += totalEventsMatrix_
        
        for trigger in triggerAndGroupList:
            #print '********************',trigger
            passedEventsMatrix[(dataset,trigger)] += passedEventsMatrix_[trigger]
    
    ## do not crash if a dataset is missing!
    if totalEventsMatrix[dataset]==0:   totalEventsMatrix[dataset]=1
    
    ##fill passedEventsMatrix[] and totalEventsMatrix[]
    for trigger in triggerAndGroupList:
        if isData:
            #print passedEventsMatrix
            rateTriggerDataset[(dataset,trigger)] = passedEventsMatrix[(dataset,trigger)]/rateDataset[dataset]
            squaredErrorRateTriggerDataset[(dataset,trigger)] = passedEventsMatrix[(dataset,trigger)]/(rateDataset[dataset]*rateDataset[dataset])
        else:    
            rateTriggerDataset [(dataset,trigger)] = rateDataset[dataset]/totalEventsMatrix[dataset]*passedEventsMatrix[(dataset,trigger)]
            squaredErrorRateTriggerDataset [(dataset,trigger)] = rateDataset[dataset]*rateDataset[dataset]*passedEventsMatrix[(dataset,trigger)]/totalEventsMatrix[dataset]/totalEventsMatrix[dataset] # (rateDataset*sqrt(1.*passedEvents/nevents/nevents)) **2
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
#if evalHLTpaths:        triggerAndGroupList=triggerAndGroupList+HLTList
#if evalHLTgroups:       triggerAndGroupList=triggerAndGroupList+groupList
#if evalHLTtwopaths:     triggerAndGroupList=triggerAndGroupList+twoHLTsList
#if evalHLTtwogroups:    triggerAndGroupList=triggerAndGroupList+twoGroupsList
#if evalL1:              triggerAndGroupList=triggerAndGroupList+L1List

# fill triggerList with the trigger HLT+L1
#triggerList=[]
#if evalHLTpaths:        triggerList=triggerList+HLTList
#if evalL1:              triggerList=triggerList+L1List

getTriggerString={}
triggersGroupMap={}
triggerName='menutest'
groupList=['none']
# define dictionaries
passedEventsMatrix = {}                 #passedEventsMatrix[(dataset,trigger)] = events passed by a trigger in a dataset
totalEventsMatrix = {}                  #totalEventsMatrix[(dataset,trigger)] = total events of a dataset
rateDataset = {}                        #rateDataset[dataset] = rate of a dataset (xsect*lumi)
rateTriggerDataset = {}                 #rateTriggerDataset[(dataset,trigger)] = rate of a trigger in a dataset
squaredErrorRateTriggerDataset = {}     #squaredErrorRateTriggerDataset[(dataset,trigger)] = squared error on the rate
rateTriggerTotal = {}                   #rateTriggerTotal[(dataset,trigger)] = total rate of a trigger
squaredErrorRateTriggerTotal = {}       #squaredErrorRateTriggerTotal[trigger] = squared error on the rate


## create a list with prescales associated to each HLT/L1 trigger path
prescaleList = {}               # prescaleTriggerTotal[trigger] = prescale from Ntuple                                            
HLTList = [] 
prescaleList,HLTList = getPrescaleListInNtuples()                                                                                             
triggerList=[]
#HLTList.remove("HLT_Physics_v2")
if evalHLTpaths:        triggerList=triggerList+HLTList
triggerAndGroupList+=HLTList
triggerAndGroupList.append('All_HLT')
triggersGroupMap['All_HLT']=['none']
prescaleList['All_HLT']=['0']
## check trigger list in triggersGroupMap (ie. ~ Google doc), with trigger bits in ntuples (ie. GRun)
#triggerList = CompareGRunVsGoogleDoc(datasetList,triggerList,folder)
#print triggerList
## loop on dataset and fill matrix with event counts, rates, and squared errors
setToZero(totalEventsMatrix,passedEventsMatrix,triggerAndGroupList,rateTriggerTotal,squaredErrorRateTriggerTotal)  #fill all dictionaries with zero
for dataset in datasetList:
    fillMatrixAndRates(dataset,totalEventsMatrix,passedEventsMatrix,rateTriggerDataset,squaredErrorRateTriggerDataset)

## evaluate the total rate with uncertainty for triggers and groups
for dataset in datasetList:
    for trigger in triggerAndGroupList:
            rateTriggerTotal[trigger] += rateTriggerDataset[(dataset,trigger)]
            squaredErrorRateTriggerTotal[trigger] += squaredErrorRateTriggerDataset[(dataset,trigger)]

if batchSplit: filename = 'ResultsBatch/'
else: filename = 'Results/'
filename = filename+runNo+"_"
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
        mkdir("ResultsBatch")
    except:
        pass

    ### write files with events count
    if evalL1: writeMatrixEvents(filename+'_L1.matrixEvents'+str(options.fileNumber)+'.tsv',datasetList,L1List,totalEventsMatrix,passedEventsMatrix,True)
    if evalHLTpaths: writeMatrixEvents(filename+'_matrixEvents'+str(options.fileNumber)+'.tsv',datasetList,HLTList,totalEventsMatrix,passedEventsMatrix,True)
    if evalHLTgroups: writeMatrixEvents(filename+'_matrixEvents.groups'+str(options.fileNumber)+'.tsv',datasetList,groupList,totalEventsMatrix,passedEventsMatrix)
    if evalHLTtwogroups: writeMatrixEvents(filename+'_matrixEvents.twogroups'+str(options.fileNumber)+'.tsv',datasetList,twoGroupsList,totalEventsMatrix,passedEventsMatrix)

    ### write files with  trigger rates
    if evalL1:writeMatrixRates(filename+'_L1_matrixRates'+str(options.fileNumber)+'.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,L1List,True)
    if evalHLTpaths: writeMatrixRates(filename+'_matrixRates'+str(options.fileNumber)+'.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,HLTList,True)
    if evalHLTgroups: writeMatrixRates(filename+'_matrixRates.groups'+str(options.fileNumber)+'.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,groupList)
    if evalHLTtwogroups: writeMatrixRates(filename+'_matrixRates.twogroups'+str(options.fileNumber)+'.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,twoGroupsList)

else:
    try:
        mkdir("Results")
    except:
        pass

    ## write files with events count
    if evalL1: writeMatrixEvents(filename+'_L1.matrixEvents.tsv',datasetList,L1List,totalEventsMatrix,passedEventsMatrix,True)
    if evalHLTpaths: writeMatrixEvents(filename+'_matrixEvents.tsv',datasetList,triggerAndGroupList,totalEventsMatrix,passedEventsMatrix,True)#HLTList
    if evalHLTgroups: writeMatrixEvents(filename+'_matrixEvents.groups.tsv',datasetList,groupList,totalEventsMatrix,passedEventsMatrix)
    if evalHLTtwogroups: writeMatrixEvents(filename+'_matrixEvents.twogroups.tsv',datasetList,twoGroupsList,totalEventsMatrix,passedEventsMatrix)

    ## write files with  trigger rates
    if evalL1: writeMatrixRates(filename+'_L1_matrixRates.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,L1List,True)
    ##if evalL1scaling: writeL1RateStudies(filename+'_L1RateStudies_matrixRates.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,L1List,True)
    if evalHLTpaths: writeMatrixRates(filename+'_matrixRates.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,triggerAndGroupList,True)
    if evalHLTgroups: writeMatrixRates(filename+'_matrixRates.groups.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,groupList)
    if evalHLTtwogroups: writeMatrixRates(filename+'_matrixRates.twogroups.tsv',prescaleList,datasetList,rateTriggerDataset,rateTriggerTotal,twoGroupsList)


## print timing
endGlobal = time.time()
totalEvents = 0
for dataset in datasetList: totalEvents+=totalEventsMatrix[dataset]
print
print "Total Time=",round((endGlobal - startGlobal),2)," Events=",totalEvents," TimePer10kEvent=", round((endGlobal - startGlobal)*10000/totalEvents,2)



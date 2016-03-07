# -*- coding: utf-8 -*-
from triggersGroupMap.triggersGroupMap__frozen_2015_25ns14e33_v4p4_HLT_V1 import *
from datasetCrossSections.datasetCrossSectionsSpring15_updatedFilterEff import *
#import ROOT
import time
import sys
#from math import *
#from scipy.stats import binom
import os  
import csv
import math


datasetList+=datasetEMEnrichedList
datasetList+=datasetMuEnrichedList

def my_print(datasetList):
    for dataset in datasetList:
        print dataset
    print len(datasetList)

def mergeRates(input_dir,output_name,L1write):
    wdir = input_dir
    
    ########## Merging the individual path rates
    h = open(output_name, "w")
    if L1write:
        h1 = open(output_name[:-4]+'_L1.tsv', "w")
    rateList = []
    for i in range(len(datasetList)+5):
        rateList.append([]) #0 Prescale
    
    #text_rate = 'Prescale\tPath\tGroup\tTotal\t\t\t\tHLTPhysics1\t\t\t\tHLTPhysics2\t\t\t\tHLTPhysics3\t\t\t\tHLTPhysics4\t\t\t\t'
    #text_rate = 'Prescale\tPath\tGroup\tTotal\t\t\t\tQCDPt15to30\t\t\tQCDPt30to50\t\t\tQCDPt50to80\t\t\tQCDPt80to120\t\t\tQCDPt120to170\t\t\tQCDPt170to300\t\t\tQCDPt300to470\t\t\tQCDPt470to600\t\t\tDYToLLM1\t\t\tWJetsToLNu\t\t\tQCDPt15to20EMEnriched\t\t\tQCDPt20to30EMEnriched\t\t\tQCDPt30to50EMEnriched\t\t\tQCDPt50to80EMEnriched\t\t\tQCDPt80to120EMEnriched\t\t\tQCDPt120to170EMEnriched\t\t\tQCDPt15to20MuEnrichedPt5\t\t\tQCDPt20to30MuEnrichedPt5\t\t\tQCDPt30to50MuEnrichedPt5\t\t\tQCDPt50to80MuEnrichedPt5\t\t\tQCDPt80to120MuEnrichedPt5\t\t\tQCDPt120to170MuEnrichedPt5\t\t\t'
    text_rate = 'Prescale\tPath\tGroup\tTotal\t\t\t'
    for i in range(len(datasetList)):
        text_rate+=datasetList[i].split('_TuneCUETP8M1_13TeV_pythia8')[0]+'\t\t\t'
    text_rate += '\n'
    
    if L1write:
        text_rate1 = 'Prescale\tPath\tGroup\tL1 seed\tL1 prescale\t\ttotal\t\t\t'
        for i in range(len(datasetList)):
            text_rate1+=datasetList[i].split('_TuneCUETP8M1_13TeV_pythia8')[0]+'\t\t\t'
        text_rate1 += '\n'
    
    lumi = 1E34
    rateDataset = {}
    TotalEventsPerDataset = {}
    datasetListFromFile = []
    ## fill datasetList properly
    for dataset in datasetList:
        rateDataset [dataset] = lumi*xsectionDatasets[dataset]*1E-24/1E12 # [1b = 1E-24 cm^2, 1b = 1E12pb ]
        datasetListFromFile.append(dataset)
        TotalEventsPerDataset[dataset] = 0

    
    Nlines = 0
    Nfiles = 0
    
    ### Looping over the individual .tsv files
    for rate_file in os.listdir(wdir):
        #print rate_file
        if ("matrixEvents" in rate_file) and not ("group" in rate_file):
            with open(wdir+rate_file) as tsvfile:
                tsvreader = csv.reader(tsvfile, delimiter="\t")
                Nfiles += 1
                i = 0
                ### For each .tsv file, looping over the lines of the text file and filling the python list with the summed rates
                for line in tsvreader: 
    		    if "TotalEvents" in line[0]:
       			for k in xrange(0,len(datasetList)): TotalEventsPerDataset[datasetListFromFile[k]] += float(line[k+2])
                        print line
                        print "*"*30
                        print len(line)
                        print "*"*30
                    groupCheck = False
                    #print "line[0]: ",line[0],", ","line[1]: ",line[1],", ","line[2]: ",line[2],", ","line[3]: ",line[3],", ","line[4]: ",line[4],"line[5]: ",line[5],", ","line[6]: ",line[6],"line[7]: ",line[7],", ","line[8]: ",line[8]#,", ","line[9]: ",line[9],", ","line[10]: ",line[10],", ","line[11]: ",line[11],"line[12]: ",line[12],", ","line[13]: ",line[13],"line[14]: ",line[14],", ","line[15]: ",line[15],", ","line[16]: ",line[16],", ","line[17]: ",line[17],", ","line[18]: ",line[18],"line[19]: ",line[19],", ","line[20]: ",line[20],"line[21]: ",line[21],", ","line[22]: ",line[22],", ","line[23]: ",line[23],", ","line[24]: ",line[24],", ","line[25]: ",line[25],"line[26]: ",line[26],", ","line[27]: ",line[27],"line[28]: ",line[28],"line[29]: ",line[29],", ","line[30]: ",line[30]
                    if (line[0]!='Path') and (line[0] not in rateList[1]):
                        for group in groupList:
                            if group in line[1]: groupCheck = True
                        if (groupCheck or ("TotalEvents" in line[0])): 
                            rateList[0].append(1) # Need to be changed to prescales
                            rateList[1].append(line[0])
                            rateList[2].append(line[1])
                            for ii in range(4,len(datasetList)+4):
                                rateList[ii].append(rateDataset[datasetListFromFile[ii-4]]*float(line[ii-2]))
                            tmp_rate=0.0
                            for ii in range(4,len(datasetList)+4):
                                tmp_rate+=rateDataset[datasetListFromFile[ii-4]]*float(line[ii-2])
                            rateList[3].append(tmp_rate)
                            #for j in xrange (4,26):
                                #print "i = ",i,", j = ",j
                            #    rateList[3][0] += rateList[j][0]
                            #print rate_file," ",rateList[3][0]
                    elif (line[0]!='Path'):
                        for group in groupList:
                            if group in line[1]: groupCheck = True
                        if (groupCheck or ("TotalEvents" in line[0])):
                            #print rate_file
                            for ii in range(4,len(datasetList)+4):
                                rateList[ii][i] += rateDataset[datasetListFromFile[ii-4]]*float(line[ii-2])
                            for j in xrange (4,len(datasetList)+4):
                                #print "i = ",i,", j = ",j
                                rateList[3][i] += rateList[j][i]
                            #print i," ",rate_file," ",rateList[3][i]
                            i += 1
                if (Nlines==0): Nlines = i
    
    print "Nfiles = ",Nfiles
    
    def is_number(s):
        try:
            float(s)
            return True
        except ValueError:
            pass
     
        try:
            import unicodedata
            unicodedata.numeric(s)
            return True
        except (TypeError, ValueError):
            pass
     
        return False
    
    TotalRateList = []
    TotalErrorList = []
    
    #for j in xrange (0,Nlines):
    #    TotalRateList.append(0)
    #    TotalErrorList.append(0)
    
    for j in xrange (0,Nlines):
        TotalRateList.append(0)
        TotalErrorList.append(0)
        for i in xrange(4,len(datasetList)+4):
     	    #if j<2: print TotalEventsPerDataset[datasetListFromFile[i-4]]
                denominator = TotalEventsPerDataset[datasetListFromFile[i-4]] 
                if denominator==0: denominator = 1
                TotalRateList[j] += rateList[i][j]/denominator
                #TotalErrorList[j] += (rateDataset[datasetListFromFile[i-4]]*TotalRateList[j])/denominator
                TotalErrorList[j] += ((rateDataset[datasetListFromFile[i-4]]*rateList[i][j])/denominator/denominator)
#        print "*"*30
#        print TotalErrorList[j]
        TotalErrorList[j] = math.sqrt(math.fabs(float(TotalErrorList[j])))
#        print TotalErrorList[j]
#        print "*"*30
    
    ### Filling up the new .tsv file with the content of the python list

#    print TotalEventsPerDataset
#    return
    for j in xrange (0,Nlines):
        for i in xrange(0,len(datasetList)+4):
            #print i," ",rateList[i][0]
            if i<3:
                text_rate += str(rateList[i][j])
                text_rate += "\t"
            elif i==3:
                #rate = rateList[i][j]/TotalEvents
                #print rate," ",rateList[i][j]," ",rateList[i][0]
                #error = (rateDataset[datasetListFromFile[i-4]]*rate)/rateList[i][0]
                text_rate += str(TotalRateList[j])
                text_rate += "\t+/-\t"
                text_rate += str(TotalErrorList[j])
                text_rate += "\t"
            elif i==len(datasetList)+3:
                if rateList[i][0]==0:
                    rate = 0
                    error = 0
                else:
                    rate = rateList[i][j]/TotalEventsPerDataset[datasetListFromFile[i-4]]
                    error = math.sqrt(math.fabs((rateDataset[datasetListFromFile[i-4]]*rate)/TotalEventsPerDataset[datasetListFromFile[i-4]]))
                text_rate += str(rate)
                text_rate += "\t+/-\t"
                text_rate += str(error)
                text_rate += "\n"
            else:
                if rateList[i][0]==0:
                    rate = 0
                    error = 0
                else:
                    rate = rateList[i][j]/TotalEventsPerDataset[datasetListFromFile[i-4]]
                    error = math.sqrt(math.fabs((rateDataset[datasetListFromFile[i-4]]*rate)/TotalEventsPerDataset[datasetListFromFile[i-4]]))
                text_rate += str(rate)
                text_rate += "\t+/-\t"
                text_rate += str(error)
                text_rate += "\t"
    
    h.write(text_rate)
    h.close()

    if not L1write:
        return
    HLTdic=getHLTmenuSteam('HLTmenu.csv')
    for j in xrange (0,Nlines):
        for i in xrange(0,len(datasetList)+4):
            #print i," ",rateList[i][0]
            if i<3:
                text_rate1 += str(rateList[i][j])
                text_rate1 += "\t"
            elif i==3:
                try:
                    text_rate1 += HLTdic[rateList[1][j].split('_v')[0]][0]
                    text_rate1 += "\t"
                    text_rate1 += HLTdic[rateList[1][j].split('_v')[0]][1]
                    text_rate1 += "\t"
                except:
                    text_rate1 += "\t"
                    text_rate1 += "\t"




                #rate = rateList[i][j]/TotalEvents
                #print rate," ",rateList[i][j]," ",rateList[i][0]
                #error = (rateDataset[datasetListFromFile[i-4]]*rate)/rateList[i][0]
                text_rate1 += str(TotalRateList[j])
                text_rate1 += "\t+/-\t"
                text_rate1 += str(TotalErrorList[j])
                text_rate1 += "\t"
            elif i==len(datasetList)+3:
                if rateList[i][0]==0:
                    rate = 0
                    error = 0
                else:
                    rate = rateList[i][j]/TotalEventsPerDataset[datasetListFromFile[i-4]]
                    error = math.sqrt(math.fabs((rateDataset[datasetListFromFile[i-4]]*rate)/TotalEventsPerDataset[datasetListFromFile[i-4]]))
                text_rate1 += str(rate)
                text_rate1 += "\t+/-\t"
                text_rate1 += str(error)
                text_rate1 += "\n"
            else:
                if rateList[i][0]==0:
                    rate = 0
                    error = 0
                else:
                    rate = rateList[i][j]/TotalEventsPerDataset[datasetListFromFile[i-4]]
                    error = math.sqrt(math.fabs((rateDataset[datasetListFromFile[i-4]]*rate)/TotalEventsPerDataset[datasetListFromFile[i-4]]))
                text_rate1 += str(rate)
                text_rate1 += "\t+/-\t"
                text_rate1 += str(error)
                text_rate1 += "\t"
    
    h1.write(text_rate1)
    h1.close()




def getL1pre(steamFile):
    predic={}
    l1predic={}
    if '.csv' in steamFile:
        import csv
     
        with open(steamFile) as csvfile:
            steamReader=csv.reader(csvfile)
            for line in steamReader:
                path = line[file4_l1path].split("_v")[0]
                path = path.strip()
    
                if path.find("L1_")!=-1:
                    l1pre = int(line[file4_l1prescale])
                    l1predic[path]=l1pre
    if '.tsv' in steamFile:
        tmp_file=open(steamFile,'r')
        for Line in tmp_file:
            line = Line.split('\t') 
            path = line[file4_l1path].split("_v")[0]
            path = path.strip()
    
            if path.find("L1_")!=-1:
                l1pre = int(line[file4_l1prescale])
                l1predic[path]=l1pre
    return l1predic 


def getHLTmenuSteam(steamFile):
    hltmenu={}
    import csv
 
    #HLTl1predic=getL1pre('L1menu.csv')
    HLTl1predic=getL1pre('ResultsBatch_0to0/rates_MC_v4p4_V1__frozen_2015_25ns14e33_v4p4_HLT_V1_7e33_PUfilterGen_EMEn_MuEn_L1_matrixRates_DYToLL_M_1_TuneCUETP8M1_13TeV_pythia8_1.tsv')
    if '.csv' in steamFile:
        with open(steamFile) as csvfile:
            steamReader=csv.reader(csvfile)
            for line in steamReader:
                path = line[file3_hltpath].split("_v")[0]
                path = path.strip()
    
                if path.find("HLT_")!=-1:
                    if (file3_l1path > 0):
                        L1path = line[file3_l1path].split(' OR ')
                        L1pre = ''
                        L1pretotal = 1
                        hltpre = int(line[file3_hltprescale])
                        for i in range(len(L1path)):
                            if L1path[i] in HLTl1predic:
                                if i == 0:
                                    L1pre = str(HLTl1predic[L1path[i]])
                                else:
                                    L1pre = L1pre + '|' +str(HLTl1predic[L1path[i]]) 
                                #L1pretotal*=int(HLTl1predic[L1path[i]])
                                L1pretotal=int(line[file3_l1prescale])
                                if L1pretotal == 0:
                                    L1pretotal =1
    
                            else:
                                L1pre = L1pre + '-1|'
                    else:
                        L1path="null"
                        L1pre='-1'
                    hltmenu[path]=(line[file3_l1path],L1pre,float(L1pretotal),hltpre)
    if '.tsv' in steamFile:
        file_hlt=open(steamFile,'r')
        for Line in file_hlt:
            line=Line.split('\t')
            path = line[file3_hltpath].split("_v")[0]
            path = path.strip()

            if path.find("HLT_")!=-1:
                if (file3_l1path > 0):
                    L1path = line[file3_l1path].split(' OR ')
                    L1pre = ''
                    L1pretotal = 1
                    hltpre = int(line[file3_hltprescale])
                    for i in range(len(L1path)):
                        if L1path[i] in HLTl1predic:
                            if i == 0:
                                L1pre = str(HLTl1predic[L1path[i]])
                            else:
                                L1pre = L1pre + '|' +str(HLTl1predic[L1path[i]])
                            #L1pretotal*=int(HLTl1predic[L1path[i]])
                            L1pretotal=int(line[file3_l1prescale])
                            if L1pretotal == 0:
                                L1pretotal =1

                        else:
                            L1pre = L1pre + '-1|'
                else:
                    L1path="null"
                    L1pre='-1'
                hltmenu[path]=(line[file3_l1path],L1pre,float(L1pretotal),hltpre)

    return hltmenu#,HLTl1predic

menu_lumibiasdic={
'1e33':3,
'2e33':2,
'5e33':0,
'7e33':-1,
'1e34':-2
}

index_lumi='1e34'
file3_hltpath = 2           #HLT_
file3_hltprescale = 22+int(menu_lumibiasdic[index_lumi])      #l1 prescale
file3_l1path = 6           #L1_
file3_l1prescale = 10+int(menu_lumibiasdic[index_lumi])      #l1 prescale

file4_l1path = 1           #L1_
#file4_l1prescale = 5+int(menu_lumibiasdic[index_lumi])      #l1 prescale
file4_l1prescale = 0     #l1 prescale






#mergeRates("/afs/cern.ch/user/x/xgao/work/RateEstimate_mc_22_02_16/1e34/ResultsBatch_23to27/","Results/mergedRates_MC_23to27.tsv",True)
mergeRates("/afs/cern.ch/user/x/xgao/work/RateEstimate_mc_22_02_16/1e34/ResultsBatch_28to32/","Results/mergedRates_MC_28to32.tsv",True)

#my_print(datasetList)

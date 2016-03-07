import ROOT
import time
import datetime
import os
import shlex
import subprocess
from datasetCrossSections.datasetCrossSectionsSpring15_updatedFilterEff import *


MYDIR='/afs/cern.ch/work/x/xgao/RateEstimate_mc_22_02_16/1e34'
CMSSWDir='/afs/cern.ch/user/x/xgao/CMSSW_7_6_3/src/'
#FILES=root://eoscms//eos/cms/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/Spring15/Hui_HLTRates_2e33_25ns_V4p4_V1/*
folder = '/store/group/dpg_trigger/comm_trigger/TriggerStudiesGroup/STEAM/Spring15/Hui_HLTRates_2e33_25ns_V4p4_V1_last_round_perhaps'


def runCommand(commandLine):
    #sys.stdout.write("%s\n" % commandLine)
    args = shlex.split(commandLine)
    retVal = subprocess.Popen(args, stdout = subprocess.PIPE)
    return retVal

def lsl(file_or_path):
    executable_eos = '/afs/cern.ch/project/eos/installation/cms/bin/eos.select'
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
        file_info['path'] = os.path.join(directory, file_info['file'])
        #print "file_info = " % file_info
        retVal.append(file_info)
    return retVal



def getdatasetfilenum(dataset):
    dirpath=''
    filenames=[]
    noRootFile = True
    walking_folder = folder+"/"+dataset
    while noRootFile:
        eosDirContent = lsl(walking_folder)
        for key in eosDirContent:
            if (("failed" in str(key['file'])) or ("log" in str(key['file']))): continue
            if ("root" in str(key['file'])):
                filenames.append(str(key['file']))
                dirpath = "root://eoscms//eos/cms"+walking_folder
                noRootFile = False
            else:
                walking_folder += "/"+key['file']
                break
#    print filenames
    return len(filenames)



def getsubdic(datasetList):
    sum1=0
    dic={}
    for dataset in datasetList:
        dic[dataset]=getdatasetfilenum(dataset)
        sum1+=getdatasetfilenum(dataset)
        print dataset+'  ,  ',getdatasetfilenum(dataset)
    return dic,sum1

def subpu(minPU,maxPU,datasetList,numdic,my_sum):
    try:
        tmp_dir='sub_%sto%s'%(str(minPU),str(maxPU))
        os.mkdir(tmp_dir)
    except:
        pass
    j=1
    for dataset in datasetList:
        for i in range(1,numdic[dataset]+1):
            print 'PU~[%s,%s]: %s : %d/%d '%(str(minPU),str(maxPU),dataset,i,numdic[dataset])
            print 'total: %d/%d  ;  %.1f %% processed '%(j,my_sum,(100*float(j)/float(my_sum)))
        
            try:
                tmp_jobname="submit_%s_%s.jobb"%(dataset,str(i))
                tmp_job=open(MYDIR+'/'+tmp_dir+'/'+tmp_jobname,'w')
                tmp_job.write("curr_dir=%s\n"%(MYDIR))
                tmp_job.write("cd %s\n"%(MYDIR))
                tmp_job.write("source env.sh\n")
                tmp_job.write("python RateEstimate.py -n %s -d %s\n"%(str(i),dataset))
                tmp_job.write("\n")
                tmp_job.close()
                os.system("chmod +x %s"%(MYDIR+'/'+tmp_dir+'/'+tmp_jobname))
                os.system("bsub -q 8nh -eo err.dat -oo out.dat %s"%(MYDIR+'/'+tmp_dir+'/'+tmp_jobname))
            except:
                pass
            j+=1


datasetList+=datasetEMEnrichedList
datasetList+=datasetMuEnrichedList



numdic,my_sum=getsubdic(datasetList)
#subpu(23,27,datasetList,numdic,my_sum)
subpu(28,32,datasetList,numdic,my_sum)

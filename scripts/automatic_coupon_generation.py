#command to run this script from python is 
# for lab pc:
# import os
# os.chdir(r"C:\MSC.Software\Digimat\working")
# exec(open('automatic_coupon_generation.py').read())

# for office pc:
# import os
# os.chdir(r"C:\MSC.Software\Digimat2018\Digimat\working")
# exec(open('automatic_coupon_generation.py').read())

import os
#run digimat to get digimat generated .inps
#modify .daf file
#os.getcwd()

# adjust this
# pc="lab"
pc="office"

batch_label='_batch003_' # adjust this

if pc=="office":
    working_directory=r"C:\\MSC.Software\\Digimat2018\\Digimat\\working"
    digi_short=r"C:\\MSC.Software\\Digimat2018\\Digimat\\2018.1\\DigimatFE\\exec\\DigimatFE.bat"
elif pc=="lab":
    working_directory=r"C:\MSC.Software\Digimat\working"
    digi_short=r"C:\MSC.Software\Digimat\shortcuts\DigimatFE20181.bat"
    
os.chdir(working_directory)
for i in range(5000,5000):
    state_number=str(i).zfill(3)
    with open('wovenplateletMorphology205A11'+'.daf','r') as in_file:
        buf=in_file.readlines()
    with open('SixByOne_inch_Sample' +str(state_number)+'.daf','w') as out_file:
        for line in buf:
            if line == 'name = cohesive_ppmc\n':
                line = 'name = '+ 'SixByOne_inch_Sample' +str(state_number)+'\n'
            if line == 'random_seed = 1\n':
                line = 'random_seed = '+str(i)+'\n'
            out_file.write(line)
    text= digi_short+' -runFEWorkflow input='+working_directory+ '\\'+'SixByOne_inch_Sample' +batch_label+str(state_number)+'.daf'
    os.system(text)
    

#make second part which turns this input into an abaqus model.
os.chdir("C:\ML Work\InputDecksForML")
for i in range(216,217):
    statenumber=i
    stringToAdd='plateletMorphology'+str(statenumber)
    
    
    #all that I should have to do is change the job name
    with open('MLAbaqusCommands.py','r') as in_file:
        buf=in_file.readlines()
    with open('MLAbaqusCommands'+str(statenumber)+'.py','w') as out_file:
        for line in buf:
            if line == 'mdb.ModelFromInputFile(name=JobName, inputFileName=\'C:/MSC.Software/Digimat/working/FE_Analysis1/test3.inp\')\n':
                line = 'mdb.ModelFromInputFile(name=JobName, inputFileName=\'C:/MSC.Software/Digimat/working/FE_Analysis1/'+stringToAdd+'.inp\')\n'
            if line == 'JobName=\'plateletModel\'\n':
                line = 'JobName=\'plateletModel'+str(statenumber)+'\'\n'
            out_file.write(line)
            
    os.system('abaqus cae noGUI=MLAbaqusCommands'+str(statenumber)+'.py')
    os.system(' ')


'''
#this portion of script does postprocessing
os.system('enable_lmod')
os.system('module load abaqus')
os.system('setenv LM_LICENSE_FILE 27040@abaqusresrch.license.odu.edu')
os.chdir("/home/rlars001/MLFolder/MLRuns3")
for i in range(160,381):
    statenumber=i
    stringToAdd='plateletMorphology'+str(statenumber)
    
    print(i)
    #all that I should have to do is change the job name
    with open('AijPost.py','r') as in_file:
        buf=in_file.readlines()
    with open('AijPost'+str(statenumber)+'.py','w') as out_file:
        for line in buf:
            if line == 'odbname=\'plateletModel\'\n':
                line = 'odbname=\'plateletModel'+str(statenumber)+'\'\n'
            out_file.write(line)
            
    os.system('abaqus viewer noGUI=AijPost'+str(statenumber)+'.py')
    os.system(' ')
'''
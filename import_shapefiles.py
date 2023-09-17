import os
import fnmatch
import subprocess

root=r'C:\Users\Humberto\Documents\GIS\PRACTICA\PORTFOLIO\OZE\data'
pattern = '*.shp'

def getSchema(filename):
    
    if filename == "OT_BUIT_P.shp":
        return "utility_poles"
    elif filename == "OT_BUWT_P.shp":
        return "utility_poles"
    elif filename == "OT_OIMK_A.shp":
        return "wet_areas"
    elif filename == "OT_OISZ_A.shp":
        return "rushes"
    elif filename == "OT_SKJZ_L.shp":
        return "roads"
    elif filename == "OT_SULN_L.shp":
        return "power_lines"
    elif filename == "OT_TCON_A.shp":
        return "protected_areas"
    elif filename == "OT_TCPK_A.shp":
        return "protected_areas"
    elif filename == "OT_TCRZ_A.shp":
        return "protected_areas"
    elif filename == "budynki.shp":
        return "buildings"
    elif filename == "dzialki.shp":
        return "parcels"
    else:
        return None

#walk loop to find the pattern files
for dirpath, dirnames, filenames in os.walk(root):
    for name in filenames:
        if fnmatch.fnmatch(name, pattern):
        #save the path name of the selected file to ff
            ff = os.path.join(dirpath, name)
        #create a name variable to be used for table name in DB
            tablename = name[:-4]
        #get the name of the schema according to the filename
            schema = getSchema(name)
            
            cmd = "shp2pgsql -I -s 2180 {0} {1}.{2} | psql -U postgres -d oze".format(ff, schema, tablename) 
            subprocess.run(cmd, shell=True)
            
          
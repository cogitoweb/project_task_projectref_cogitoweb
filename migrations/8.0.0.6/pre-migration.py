import logging
import subprocess, os.path
from openerp.tools.config import config

_logger = logging.getLogger('upgrade')

def migrate(cr, version):
    if not version:
        return
    

    ## info di db
    dbname = cr.dbname
    dbUser = config.get("db_user")
    dbPw = config.get("db_password")
    dbPort = config.get("db_port")
    dbHost = config.get("db_host")
    functionName = "triggers"

    _logger.info("____username: %s_____password: %s____porta: %s______host: %s____",dbUser, dbPw, str(dbPort), str(dbHost))   
    
    ## info di filesystem
    relativePath = os.path.dirname(os.path.realpath(__file__))                
    if(not os.path.isfile(relativePath + "/../../data/" + functionName + ".sql")):
        raise Exception('create function script ' + functionName + '.sql does not exist in data folder of this module')   
        
    subprocess.call(["psql", "postgresql://" + dbUser + ":" + dbPw + "@" + str(dbHost) + ":" + str(dbPort) + "/" + dbname, "-f", relativePath + "/../../data/" + functionName + ".sql"])
            



        

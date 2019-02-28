# coding:utf-8
from library import *
from library.base import Base
from library.virtwho import Virtwho

class Testcase(Virtwho):
    def test_run(self):
        case_name = os.path.basename(__file__)
        logger.info("Used to test UMB trigger")
        
if __name__ == "__main__":
    unittest.main()



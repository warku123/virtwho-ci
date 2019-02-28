from virtwho import *
from virtwho.base import Base
from virtwho.register import Register
from virtwho.provision import Provision

class RunProvision(Provision):
    def test_run(self):
        case_name = self.__class__.__name__
        self.provision_start()

if __name__ == "__main__":
    unittest.main()

from virt_who import *
from virt_who.base import Base
from virt_who.register import Register
from virt_who.provision import Provision


class RunProvision(Provision):
    def test_run(self):
        case_name = self.__class__.__name__
        self.provision_start()


if __name__ == "__main__":
    unittest.main()

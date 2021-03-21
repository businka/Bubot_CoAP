import unittest
from Bubot_CoAP.messages.message import Message
from Bubot_CoAP.messages.option import Option
from Bubot_CoAP.messages.options import Options
from Bubot_CoAP import defines


class Tests(unittest.TestCase):

    # def setUp(self):
    #     self.server_address = ("127.0.0.1", 5683)
    #     self.current_mid = random.randint(1, 1000)
    #     self.server_mid = random.randint(1000, 2000)
    #     self.server = CoAPServer("127.0.0.1", 5683)
    #     self.server_thread = threading.Thread(target=self.server.listen, args=(1,))
    #     self.server_thread.start()
    #     self.queue = Queue()
    #
    # def tearDown(self):
    #     self.server.close()
    #     self.server_thread.join(timeout=25)
    #     self.server = None

    def test_create_options(self):
        m = Message()
        o = Options()
        o.accept = 10000
        # setattr(o, 'accept', 10000)
        option = Option()
        option.number = defines.OptionRegistry.ACCEPT.number
        option.value = 10000

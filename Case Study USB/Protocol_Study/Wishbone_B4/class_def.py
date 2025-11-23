class Module_GPT_Response:
    def __init__(self, module_name):
        self.module_name = module_name
        self.verilog_code = []
        self.summary_text = []  # Sequential text summaries (just text)
        self.long_description = []
        self.control_flow_text = []
        self.data_flow_text = []
        self.input_output_list = []
        self.FSM = []
        self.cfg = []
        self.dfg = []
        self.CSR = []
        self.submodule_GPT_Response = {}

class Spec_GPT_Response:
    def __init__(self, spec_text, fsm_json, csr_json, others_json):
        # self.module_name = module_name
        self.spec_text = spec_text
        self.fsm_json = fsm_json
        self.csr_json = csr_json
        self.others_json = others_json

class Spec_Verification_Response:
    def __init__(self):
        self.FSM = []
        self.CSR = []
        self.OTHERS = []


class Protocol_Verification_Response:
    def __init__(self):
        self.FSM = []
        self.CSR = []
        self.OTHERS = []
        self.RESPONSE = []

class Protocol_GPT_Response:
    def __init__(self, protocol_name):
        self.protocol_name = protocol_name
        self.specs_json = []

class VariableStore:
    def __init__(self):
        self.data = {}  # main dictionary

    def store(self, key1, key2, value):
        """
        Store a value under (key1, key2).
        If key1 doesn't exist yet, create a sub-dictionary.
        """
        if key1 not in self.data:
            self.data[key1] = {}
        self.data[key1][key2] = value

    def get(self, key1, key2):
        """
        Retrieve the stored value for (key1, key2).
        Returns None if not found.
        """
        return self.data.get(key1, {}).get(key2)

    def __repr__(self):
        return str(self.data)

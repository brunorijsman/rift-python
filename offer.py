class RxOffer:

    def __init__(self, interface_name, system_id, level, not_a_ztp_offer, state):
        self.interface_name = interface_name
        self.system_id = system_id
        self.level = level
        self.not_a_ztp_offer = not_a_ztp_offer
        self.state = state
        self.best = False
        self.best_three_way = False
        self.removed = False
        self.removed_reason = ""

    @staticmethod
    def cli_headers():
        return [
            "Interface",
            "System ID",
            "Level",
            "Not A ZTP Offer",
            "State",
            "Best",
            "Best 3-Way",
            "Removed",
            "Removed Reason"]

    def cli_attributes(self):
        return [
            self.interface_name,
            self.system_id,
            self.level,
            self.not_a_ztp_offer,
            self.state.name,
            self.best,
            self.best_three_way,
            self.removed,
            self.removed_reason]

class TxOffer:

    def __init__(self, interface_name, system_id, level, not_a_ztp_offer, state):
        self.interface_name = interface_name
        self.system_id = system_id
        self.level = level
        self.not_a_ztp_offer = not_a_ztp_offer
        self.state = state

    @staticmethod
    def cli_headers():
        return [
            "Interface",
            "System ID",
            "Level",
            "Not A ZTP Offer",
            "State"]

    def cli_attributes(self):
        return [
            self.interface_name,
            self.system_id,
            self.level,
            self.not_a_ztp_offer,
            self.state.name]
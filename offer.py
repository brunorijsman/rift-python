class Offer:

    def __init__(self, level, not_a_ztp_offer, system_id):
        self.level = level
        self.not_a_ztp_offer = not_a_ztp_offer
        self.system_id = system_id
        self.removed = False
        self.removed_reason = ""

    @staticmethod
    def cli_headers():
        return [
            ["System ID"],
            ["Level"],
            ["Not A ZTP Offer"],
            ["Removed"],
            ["Removed Reason"]]

    def cli_attributes(self):
        return [
            self.system_id,
            self.level,
            self.not_a_ztp_offer,
            self.removed,
            self.removed_reason]



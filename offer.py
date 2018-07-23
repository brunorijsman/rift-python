class Offer:

    def __init__(self, level, not_a_ztp_offer, system_id, state):
        self.level = level
        self.not_a_ztp_offer = not_a_ztp_offer
        self.system_id = system_id
        self.state = state
        self.best = False
        self.best_three_way = False
        self.removed = False
        self.removed_reason = ""

    @staticmethod
    def cli_headers():
        return [
            ["System ID"],
            ["Level"],
            ["Not A ZTP Offer"],
            ["State"],
            ["Best"],
            ["Best 3-Way"],
            ["Removed"],
            ["Removed Reason"]]

    def cli_attributes(self):
        print("cli_attributes object", self) #! DEBUG
        return [
            self.system_id,
            self.level,
            self.not_a_ztp_offer,
            self.state.name,
            self.best,
            self.best_three_way,
            self.removed,
            self.removed_reason]



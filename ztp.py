
import common

class Ztp:
    @enum.unique
    class State(enum.Enum):
        UPDATING_CLIENTS = 1
        HOLDING_DOWN = 2
        COMPUTE_BEST_OFFER = 3

    @enum.unique
    class Event(enum.Enum):
        CHANGE_LOCAL_LEAF_INDICATIONS = 1
        CHANGE_LOCAL_CONFIGURED_LEVEL = 2
        NEIGHBOR_OFFER = 3
        WITH_DRAW_NEIGHBOROFFER = 4
        BETTER_HAL = 5
        BETTER_HAT = 6
        LOST_HAL = 7
        LOST_HAT = 8
        COMPUTATION_DONE = 9
        HOLDDOWN_EXPIRED = 10


    # on LostHAT in ComputeBestOffer finishes in ComputeBestOffer:
    #       LEVEL_COMPUTE
    def action_compute_level(self):
        # TODO:
        pass

    #
    def action_store_leaf_flag(self):
        # TODO:
        pass


    #
    def action_store_leaf_flag_and_compute_level(self):
        #
        self.action_store_leaf_flag()
        self.action_compute_level()

    #
    def action_update_offer_if_non_null(self):
        # TODO:
        #          if no level offered REMOVE_OFFER else
        #          if level > leaf then UPDATE_OFFER else REMOVE_OFFER
        pass

    #
    def action_store_level(self):
        # TODO:
        pass

    #

    def action_store_level_and_compute_level(self):
        #
        self.action_store_level()
        self.action_compute_level()

    #
    def action_purge_offers(self):
        # TODO:
        pass
    #

    def action_remove_offer(self):
        # TODO:
        pass
    #
    def action_check_hold_time_expired(self):
        # on LostHAL in ComputeBestOffer finishes in HoldingDown: if any
        # southbound adjacencies present update holddown timer to normal
        # duration else fire holddown timer immediately
        self.info(self._log, "_time_ticks_since_lie_received = {}")
        if self._time_ticks_since_lie_received == None:
            return False
        self._time_ticks_since_lie_received += 1
        if self._time_ticks_since_lie_received >= self.holdtime:
            self._fsm.push_event(self.Event.HOLD_DOWN_EXPIRED)




    transitions = {
        State.UPDATING_CLIENTS: state_one_way_transitions,
        State.HOLDING_DOWN: state_two_way_transitions,
        State.COMPUTE_BEST_OFFER: state_three_way_transitions
    }

    state_entry_actions = {
        State.COMPUTE_BEST_OFFER: []
    }


    def info(self, logger, msg):
        logger.info("[{}] {}".format(self._log_id, msg))

    def warning(self, logger, msg):
        logger.warning("[{}] {}".format(self._log_id, msg))


    def __init__(self, node, config):

        self._node = node
        self._name = 'ztp'
        # TODO: Make the default metric/bandwidth depend on the speed of the interface
        self._log = node._log.getChild("ztp")
        self.info(self._log, "Zero touch provisioning state machine")
        self._log_id = node._log_id + "-{}".format(self._name)
        self._fsm_log = self._log.getChild("fsm")
        self._holdtime = common.default_holdtime
        self._fsm = fsm.FiniteStateMachine(
            state_enum = self.State,
            event_enum = self.Event,
            transitions = self.transitions,
            state_entry_actions = self.state_entry_actions,
            initial_state = self.State.COMPUTE_BEST_OFFER,
            action_handler = self,
            log = self._fsm_log,
            log_id = self._log_id)
 #       self._one_second_timer = timer.Timer(1.0, lambda: self._fsm.push_event(self.Event.TIMER_TICK))



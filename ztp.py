

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

    # on  LOST_HAT in ComputeBestOffer finishes in ComputeBestOffer:  LEVEL_COMPUTE
    # on  LOST_HAT in HOLDING_DOWN   finishes in HOLDING_DOWN: NO_ACTION
    # on  LOST_HAL in HOLDING_DOWN    finishes in HOLDING_DOWN: NO_ACTION
    # on  CHANGE_LOCAL_LEAF_INDICATIONS in UpdatingClients    finishes in    ComputeBestOffer: STORE_LEAF_FLAGS
    # on  LOST_HAT in UpdatingClients    finishes in ComputeBestOffer: NO_ACTION
    # on    BETTER_HAT in HOLDING_DOWN    finishes in HoldingDown: NO_ACTION
    # on    NeighborOffer in ComputeBestOffer    finishes in ComputeBestOffer: NO_ACTION
    #     if no level offered
    #           then REMOVE_OFFER
    #           else  if level > leaf
    #                   then UPDATE_OFFER
    #                   else REMOVE_OFFER
    # on    BetterHAT in UpdatingClients    finishes in ComputeBestOffer: NO_ACTION
    # on    ChangeLocalConfiguredLevel in HOLDING_DOWN    finishes in    ComputeBestOffer: STORE_LEVEL
    # on    BetterHAL in ComputeBestOffer    finishes in ComputeBestOffer:    LEVEL_COMPUTE
    # on    HoldDownExpired in HOLDING_DOWN    finishes in ComputeBestOffer:    PURGE_OFFERS
    # on    ShortTic in HOLDING_DOWN    finishes in HOLDING_DOWN:
    #    if HOLDDOWN_TIMER_EXPIRED
    #           then PUSH_EVENT   HOLDDOWN_EXPIRED
    # on    ComputationDone in ComputeBestOffer    finishes in    UpdatingClients: NO_ACTION
    # on    LostHAL in UpdatingClients    finishes in HOLDING_DOWN:
    #     if any southbound adjacencies present
    #         then update holddown timer to normal duration
    #         else fire   holddown    timer    immediately
    # on     NeighborOffer in UpdatingClients    finishes in UpdatingClients:
    #     if no level offered REMOVE_OFFER else
    #     if level > leaf then UPDATE_OFFER else REMOVE_OFFER
    # on ChangeLocalConfiguredLevel in ComputeBestOffer finishes in ComputeBestOffer: store CONFIGURED level and LEVEL_COMPUTE
    # on NeighborOffer in HoldingDown finishes in HoldingDown:
    #     if no level offered REMOVE_OFFER else
    #     if level > leaf then UPDATE_OFFER else REMOVE_OFFER
    # on LostHAL in ComputeBestOffer finishes in HoldingDown:
    #     if any    southbound    adjacencies    present
    #         then     update    holddown    timer    to    normal duration
    #         else fire holddown timer immediately
    # on BetterHAT in ComputeBestOffer finishes in ComputeBestOffer: LEVEL_COMPUTE
    # on WithdrawNeighborOffer in ComputeBestOffer finishes in ComputeBestOffer: REMOVE_OFFER
    # on ChangeLocalLeafIndications in ComputeBestOffer finishes in       ComputeBestOffer: store leaf flags and LEVEL_COMPUTE
    # on BetterHAL in HoldingDown finishes in HoldingDown: no action
    # on WithdrawNeighborOffer in HoldingDown finishes in HoldingDown:      REMOVE_OFFER
    # on ChangeLocalLeafIndications in HoldingDown finishes in      ComputeBestOffer: store leaf flags
    # on ChangeLocalConfiguredLevel in UpdatingClients finishes in      ComputeBestOffer: store level
    # on ComputationDone in HoldingDown finishes in HoldingDown:
    # on BetterHAL in UpdatingClients finishes in ComputeBestOffer: no      action
    # on WithdrawNeighborOffer in UpdatingClients finishes in      UpdatingClients: REMOVE_OFFER
    # on Entry into UpdatingClients: update all LIE FSMs with      computation results
    # on Entry into ComputeBestOffer: LEVEL_COMPUTE

   #  Following words are used for well known procedures:
   # 1.  PUSH Event: pushes an event to be executed by the FSM upon exit  of this action
   # 2.  COMPARE_OFFERS: checks whether based on current offers and held    last results the events BetterHAL/LostHAL/BetterHAT/LostHAT are       necessary and returns them
   # 3.  UPDATE_OFFER: store current offer and COMPARE_OFFERS, PUSH   according events
   # 4.  LEVEL_COMPUTE: compute best offered or configured level and HAL/  HAT, if anything changed PUSH ComputationDone
   # 5.  REMOVE_OFFER: remove the according offer and COMPARE_OFFERS, PUSH       according events
   # 6.  PURGE_OFFERS: REMOVE_OFFER for all held offers, COMPARE OFFERS,       PUSH according events

# on LostHAT in ComputeBestOffer finishes in ComputeBestOffer:
    #       LEVEL_COMPUTE

    def action_no_action(self):
        pass

    def action_level_compute(self):
        # TODO:
        pass

    #on ChangeLocalLeafIndications in UpdatingClients finishes in ComputeBestOffer: store leaf flags
    def action_store_leaf_flag(self):
        # TODO:
        pass


    #
    def action_store_leaf_flag_and_level_compute(self):
        #
        self.action_store_leaf_flag()
        self.action_level_compute()

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
        #TODO what is first store level or compute level?

        self.action_store_level()
        self.action_level_compute()

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
        State.UPDATING_CLIENTS: state_updating_clients_transitions,
        State.HOLDING_DOWN: state_holding_down_transitions,
        State.COMPUTE_BEST_OFFER: state_compute_best_offer_transitions
    }

    state_entry_actions = {
 #       State.COMPUTE_BEST_OFFER: []
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
        #TODO take ztp hold time from init file
        self._holdtime = 1
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



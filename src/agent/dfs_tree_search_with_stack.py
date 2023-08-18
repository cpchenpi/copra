#!/usr/bin/env python3

import sys

root_dir = f"{__file__.split('src')[0]}"
if root_dir not in sys.path:
    sys.path.append(root_dir)
import typing
from collections import deque
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from src.rl.q_tree import QTreeStateInfo
from src.agent.gpt_guided_tree_search_policy import PromptSummary, ProofQTree, StateType, TreeSearchAction, TreeSearchActionType
from src.agent.gpt_guided_tree_search_policy import ProofQInfo, ProofQTree
from src.rl.simple_proof_env import ProofEnvInfo, ProgressState
from src.rl.proof_action import ProofAction
from src.rl.proof_state import ProofState, FailedProofState
from src.agent.gpt_guided_tree_search_policy import TreeSearchAlgorithm

@dataclass_json
@dataclass
class StateActionPair(object):
    state : ProofState
    action : ProofAction

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, StateActionPair) and self.state == __value.state and self.action == __value.action
    
    def __hash__(self) -> int:
        return hash((self.state, self.action))
    
    def __ge__(self, __o: object) -> bool:
        assert isinstance(__o, StateActionPair)
        assert isinstance(self.state, ProofState)
        assert isinstance(self.action, ProofAction)
        return (self.state, self.action) >= (__o.state, __o.action)
    
    def __le__(self, __o: object) -> bool:
        assert isinstance(__o, StateActionPair)
        assert isinstance(self.state, ProofState)
        assert isinstance(self.action, ProofAction)
        return (self.state, self.action) <= (__o.state, __o.action)
    
    def __lt__(self, __o: object) -> bool:
        assert isinstance(__o, StateActionPair)
        assert isinstance(self.state, ProofState)
        assert isinstance(self.action, ProofAction)
        return (self.state, self.action) < (__o.state, __o.action)
    
    def __gt__(self, __o: object) -> bool:
        assert isinstance(__o, StateActionPair)
        assert isinstance(self.state, ProofState)
        assert isinstance(self.action, ProofAction)
        return (self.state, self.action) > (__o.state, __o.action)


@dataclass_json
@dataclass
class DFSTreeNode(object):
    state_action_pair: StateActionPair
    next_state_action_pair: StateActionPair
    action : ProofAction
    info : ProofEnvInfo
    reward : float
    done : bool
    incorrect_actions: typing.List[ProofAction] = field(default_factory=list)
    actions_till_now: typing.List[ProofAction] = field(default_factory=list)

class DFSTreeSearch(TreeSearchAlgorithm):
    def __init__(self):
        self._action_queue : deque = deque()
        self._search_stack : typing.List[DFSTreeNode] = []
        pass

    def reset(self):
        self._action_queue.clear()
        self._search_stack.clear()

    def update_new_node(self, tree: ProofQTree, state: ProofState, action: ProofAction, next_state: ProofState, reward: float, done: bool, info: ProofEnvInfo):
        assert action.action_type in [ProofAction.ActionType.RUN_TACTIC, ProofAction.ActionType.GET_DFNS, ProofAction.ActionType.GET_THMS], "The action type should be either RUN_TACTIC, GET_DFNS or GET_THMS"
        if len(self._search_stack) > 0:
            last_node = self._search_stack[-1]
        else:
            last_node = None
        non_simplifying_action_message = "The proof-step does NOT simplify the goal. Try stepping back with different proof-step."
        subsequent_failed_action_message = "The proof-step ultimately leads to goals which eventually don't simplify. Try stepping back with a different proof-step."
        current_state_action_pair = StateActionPair(state, ProofAction(ProofAction.ActionType.NONE))
        next_state_action_pair = StateActionPair(next_state, action)
        new_node = DFSTreeNode(current_state_action_pair, next_state_action_pair, action, info, reward, done)
        current_node_is_correct = True
        if self._check_if_state_is_harder(current_state_action_pair, next_state_action_pair):
            if action.action_type == ProofAction.ActionType.RUN_TACTIC:
                # Backtrack to the previous state because we ran a tactic which did not simplify the goal
                self._action_queue.append(TreeSearchAction(TreeSearchActionType.BACKTRACK, state, summary=None))
            new_node.info.progress = ProgressState.FAILED
            new_node.info.error_message = non_simplifying_action_message
            new_node.next_state_action_pair.state = FailedProofState # This is to ensure that there are no cycles in the tree
            current_node_is_correct = False
        elif new_node.info.progress == ProgressState.STATE_CHANGED or new_node.info.progress == ProgressState.STATE_UNCHANGED:
            assert new_node.state_action_pair > new_node.next_state_action_pair, "The next state should not be harder than the current state"
            current_node_is_correct = True
        else:
            assert new_node.info.progress == ProgressState.FAILED, "The progress should be FAILED"
            new_node.next_state_action_pair.state = FailedProofState # This is to ensure that there are no cycles in the tree
            current_node_is_correct = False
        if last_node is None or last_node.next_state_action_pair.state != FailedProofState:
            self._search_stack.append(new_node)
        elif current_node_is_correct:
            assert last_node.next_state_action_pair.state == FailedProofState, "The last node's next state should be FailedProofState"
            assert last_node.next_state_action_pair.state == new_node.state_action_pair.state, "There cannot be a jump in the states"
            # Pop the failed node from the stack
            self._search_stack.pop()
            # Add the new node to the stack
            self._search_stack.append(new_node)
        else:
            assert last_node.state_action_pair.state == new_node.state_action_pair.state, "There cannot be a jump in the states"
            assert last_node.next_state_action_pair.state == FailedProofState, "The last node's next state should be FailedProofState"
            if action in last_node.incorrect_actions or new_node.action == last_node.action:
                # Pop from the stack, because we no longer want to use this action again
                self._search_stack.pop()
                # Update the last node as the older node is popped
                last_node = self._search_stack[-1] if len(self._search_stack) > 0 else None
                if last_node is None:
                    # There is nothing in the queue the search is over
                    self._action_queue.append(TreeSearchAction(TreeSearchActionType.STOP, state, summary=None))
                else:
                    assert last_node.next_state_action_pair.state != FailedProofState, "The last node's next state should not be FailedProofState"
                    if last_node.state_action_pair.action.action_type == ProofAction.ActionType.RUN_TACTIC:
                        # Add backtracking if the last action was a tactic
                        self._action_queue.append(TreeSearchAction(TreeSearchActionType.BACKTRACK, state, summary=None))
                    # Deem the last action as invalid
                    last_node.next_state_action_pair.state = FailedProofState
                    last_node.info.progress = ProgressState.FAILED
                    last_node.info.error_message = subsequent_failed_action_message
            else:
                last_node.incorrect_actions.append(last_node.action)
                last_node.action = new_node.action
                last_node.next_state_action_pair.action = new_node.next_state_action_pair.action
                last_node.next_state_action_pair.state = FailedProofState
                last_node.info = new_node.info
    
    def estimate_q_value(self, tree: ProofQTree, state: ProofState, action: ProofAction, next_state: ProofState, reward: float, done: bool, info: ProofEnvInfo) -> float:
        return super().estimate_q_value(tree, state, action, next_state, reward, done, info)
    
    def __call__(self, tree: ProofQTree, state: ProofState) -> TreeSearchAction:
        if len(self._action_queue) > 0:
            return self._action_queue.popleft()
        elif len(self._search_stack) == 0:
            qtree_state_info = QTreeStateInfo(state, 
                ProofQInfo(0.0, False, 0.0, has_loop=False, distance_from_root=0, proof_env_info=None, state_type=StateType.UNDISCOVERED))
            # There are no nodes in the tree, so we have to just give the summary from the proof state.
            return TreeSearchAction(TreeSearchActionType.NEXT_ACTION_SUMMARY_PROMPT, state, 
                summary=PromptSummary([], [], None, qtree_state_info))
        else:
            return self._dfs(tree, state)
    
    def _dfs(self, tree: ProofQTree, state: ProofState) -> TreeSearchAction:
        assert len(self._search_stack) > 0, "The search stack should not be empty"
        last_node = self._search_stack[-1]
        distance_from_root = len(self._search_stack)
        if last_node.next_state_action_pair.state == FailedProofState:
            assert last_node.state_action_pair.state == state, "The last node's current state should be the current state"
            assert last_node.info.progress == ProgressState.FAILED, "The last node's progress should be FAILED"
            assert last_node.info.error_message is not None, "The last node's error message should not be None"
            return TreeSearchAction(TreeSearchActionType.FAILED_ACTION_SUMMARY_PROMPT,
                    last_node.current_state_info, summary = PromptSummary(
                        last_node.incorrect_actions,
                        last_node.actions_till_now,
                        last_node.current_state_info.action,
                        QTreeStateInfo(last_node.current_state_info, 
                            ProofQInfo(
                                last_node.reward, 
                                last_node.done, 
                                qval = -1.0 * distance_from_root, 
                                distance_from_root = distance_from_root,
                                proof_env_info=last_node.info))))
        elif last_node.next_state_action_pair.state == state:
            assert len(last_node.incorrect_actions) == 0, "The last node's incorrect actions should be empty"
            assert last_node.info.progress != ProgressState.FAILED, "The last node's progress should not be FAILED"
            assert last_node.info.error_message is None, "The last node's error message should be None"
            return TreeSearchAction(TreeSearchActionType.NEXT_ACTION_SUMMARY_PROMPT,
                    last_node.next_state, summary = PromptSummary(
                        last_node.incorrect_actions,
                        last_node.actions_till_now,
                        last_node.current_state_info.action,
                        QTreeStateInfo(last_node.next_state, 
                            ProofQInfo(
                                last_node.reward, 
                                last_node.done, 
                                qval = -1.0 * distance_from_root, 
                                distance_from_root = distance_from_root,
                                proof_env_info=last_node.info))))
        else:
            raise Exception("The last node's next state should either be the current state or a failed state")

    def _check_if_state_is_harder(self, current_state_action_pair: StateActionPair, next_state_action_pair: StateActionPair) -> bool:
        if current_state_action_pair <= next_state_action_pair:
            return True
        else:
            for node in self._search_stack:
                if node.next_state_action_pair <= next_state_action_pair:
                    return True
            return False
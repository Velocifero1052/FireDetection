"""
Fire Decision Algorithm Simulator
Implements algorithms A, B, C according to SP 484.1311500.2020
Author: Based on Mutovin & Chubar formalization
GitHub: https://github.com/Velocifero1052/FireDetection
"""

import time
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
import random

class FireSignal(Enum):
    NO_FIRE = 0
    FIRE = 1

class DetectorType(Enum):
    AUTOMATIC = "automatic"
    MANUAL = "manual"

@dataclass
class FireDetector:
    id: str
    zone_id: str
    detector_type: DetectorType = DetectorType.AUTOMATIC
    is_triggered: bool = False

    def read_state(self) -> bool:
        """Simulate reading detector state"""
        return self.is_triggered

class ReQueryTimer:
    def __init__(self, timeout_sec: float = 60.0):
        self.timeout = timeout_sec
        self.start_time: Optional[float] = None
        self.running = False

    def start(self):
        self.start_time = time.time()
        self.running = True

    def is_expired(self) -> bool:
        if not self.running:
            return False
        return (time.time() - self.start_time) > self.timeout

    def stop(self):
        self.running = False

class FireAlgorithm:
    """Base class for fire decision algorithms"""
    def __init__(self, zone_id: str):
        self.zone_id = zone_id
        self.fire_signal = FireSignal.NO_FIRE

    def process(self, detectors: List[FireDetector]) -> FireSignal:
        raise NotImplementedError

class AlgorithmA(FireAlgorithm):
    """Algorithm A: Immediate confirmation without re-query"""
    def process(self, detectors: List[FireDetector]) -> FireSignal:
        for d in detectors:
            if d.detector_type == DetectorType.AUTOMATIC and d.read_state():
                self.fire_signal = FireSignal.FIRE
                return self.fire_signal
        self.fire_signal = FireSignal.NO_FIRE
        return self.fire_signal

class AlgorithmB(FireAlgorithm):
    """Algorithm B: Re-query with timeout (max 60 sec)"""
    def __init__(self, zone_id: str, timeout_sec: float = 60.0):
        super().__init__(zone_id)
        self.timer = ReQueryTimer(timeout_sec)
        self.pending_trigger = False

    def process(self, detectors: List[FireDetector]) -> FireSignal:
        # Check if any automatic detector is triggered
        any_triggered = any(d.detector_type == DetectorType.AUTOMATIC and d.read_state() for d in detectors)

        if any_triggered and not self.pending_trigger and self.fire_signal == FireSignal.NO_FIRE:
            # First trigger: start re-query timer
            self.pending_trigger = True
            self.timer.start()
            return FireSignal.NO_FIRE

        if self.pending_trigger:
            if self.timer.is_expired():
                # Timeout without confirmation
                self.pending_trigger = False
                self.timer.stop()
                return FireSignal.NO_FIRE

            # Check for confirmation (same or different detector still triggered)
            if any_triggered:
                self.fire_signal = FireSignal.FIRE
                self.pending_trigger = False
                self.timer.stop()
                return self.fire_signal

        return self.fire_signal

class AlgorithmC(FireAlgorithm):
    """Algorithm C: Two independent automatic detectors in same or different zones within same room"""
    def __init__(self, room_zones: List[str], timeout_sec: float = 60.0):
        super().__init__(room_zones[0] if room_zones else "room")
        self.room_zones = room_zones
        self.timer = ReQueryTimer(timeout_sec)
        self.first_trigger_zone: Optional[str] = None
        self.first_trigger_time: Optional[float] = None

    def process(self, all_detectors: List[FireDetector]) -> FireSignal:
        # Group detectors by zone
        zone_triggered = {}
        for d in all_detectors:
            if d.detector_type == DetectorType.AUTOMATIC and d.read_state():
                zone_triggered[d.zone_id] = True

        # Check if any zone in room is triggered
        current_triggered_zones = [z for z in self.room_zones if zone_triggered.get(z, False)]

        if not self.first_trigger_zone and current_triggered_zones:
            # First automatic detector triggered
            self.first_trigger_zone = current_triggered_zones[0]
            self.first_trigger_time = time.time()
            self.timer.start()
            return FireSignal.NO_FIRE

        if self.first_trigger_zone:
            if self.timer.is_expired():
                # Timeout
                self._reset()
                return FireSignal.NO_FIRE

            # Need a different zone triggered
            other_zones_triggered = [z for z in current_triggered_zones if z != self.first_trigger_zone]
            if other_zones_triggered:
                self.fire_signal = FireSignal.FIRE
                self._reset()
                return self.fire_signal

        return self.fire_signal

    def _reset(self):
        self.first_trigger_zone = None
        self.first_trigger_time = None
        self.timer.stop()

# ========== SIMULATION EXAMPLE ==========
def simulate_scenario(algorithm: FireAlgorithm, detector_states_sequence: List[List[bool]], detector_ids: List[str], zone_id: str):
    """Run a time-step simulation"""
    detectors = [FireDetector(id=did, zone_id=zone_id) for did in detector_ids]
    print(f"\n--- Running {algorithm.__class__.__name__} on zone {zone_id} ---")
    for step, states in enumerate(detector_states_sequence):
        for d, state in zip(detectors, states):
            d.is_triggered = state
        result = algorithm.process(detectors)
        print(f"Step {step+1}: Detector states {states} -> Fire Signal: {result.name}")
        if result == FireSignal.FIRE:
            break

if __name__ == "__main__":
    # Scenario 1: Algorithm A - immediate fire
    print("\n" + "="*50)
    print("SCENARIO 1: Algorithm A - immediate fire on first trigger")
    algo_a = AlgorithmA("zone1")
    # Step1: no fire, Step2: detector1 triggers
    simulate_scenario(algo_a, [[False, False], [True, False]], ["D1", "D2"], "zone1")

    # Scenario 2: Algorithm B - re-query with confirmation within timeout
    print("\n" + "="*50)
    print("SCENARIO 2: Algorithm B - first trigger, then confirmation")
    algo_b = AlgorithmB("zone1", timeout_sec=2.0)
    simulate_scenario(algo_b, [[True, False], [True, False]], ["D1", "D2"], "zone1")
    time.sleep(0.5)  # simulate real time

    # Scenario 3: Algorithm B - timeout without confirmation
    print("\n" + "="*50)
    print("SCENARIO 3: Algorithm B - first trigger, then timeout")
    algo_b2 = AlgorithmB("zone1", timeout_sec=1.0)
    simulate_scenario(algo_b2, [[True, False], [False, False]], ["D1", "D2"], "zone1")
    time.sleep(1.2)

    # Scenario 4: Algorithm C - two independent zones
    print("\n" + "="*50)
    print("SCENARIO 4: Algorithm C - first zone triggers, second zone confirms")
    detectors_c = [
        FireDetector("Z1_D1", "zone1"),
        FireDetector("Z2_D1", "zone2")
    ]
    algo_c = AlgorithmC(room_zones=["zone1", "zone2"], timeout_sec=2.0)
    # Step1: zone1 triggers, Step2: zone2 triggers
    states_seq = [
        [(True, "zone1"), (False, "zone2")],
        [(True, "zone1"), (True, "zone2")]
    ]
    for step, state_list in enumerate(states_seq):
        for det, (triggered, _) in zip(detectors_c, state_list):
            det.is_triggered = triggered
        res = algo_c.process(detectors_c)
        print(f"Step {step+1}: {[(d.id, d.is_triggered) for d in detectors_c]} -> Fire: {res.name}")
        if res == FireSignal.FIRE:
            break
# Fire Decision Algorithm Simulator

This project implements **Algorithms A, B, and C** for fire signal generation according to Russian regulation **SP 484.1311500.2020**, as formalized by Mutovin & Chubar.

## Features
- Algorithm A: Immediate fire on any automatic detector trigger.
- Algorithm B: Re-query with timeout (max 60 sec). Fire only if trigger persists or repeats within timeout.
- Algorithm C: Two independent automatic detectors in the same room (different zones). Fire only after second independent trigger.
- Simulation of detector state sequences.
- Easy to extend with new algorithms or hardware-in-the-loop.

## Installation
```bash
git clone https://github.com/maxmutovin/fire-algorithm-simulator.git
cd fire-algorithm-simulator
python fire_algorithm.py
"""
app/engine/allocation.py
Packet-based FEFO allocation engine.
All allocation operates on integer packet units only.
"""
import math
from typing import List, Literal
from dataclasses import dataclass


@dataclass
class AllocationResult:
    packets_used: int
    allocated_g: float
    deviation: float           # (allocated_g - required_g) / required_g
    strategy: Literal["strict", "approx"]
    batches_used: List[dict]   # [{batch_id, packets_taken, grams_taken}]
    feasible: bool


MAX_DEVIATION = 0.25           # 25% tolerance threshold


def allocate_fefo(
    batches: List,
    required_g: float,
    strategy: Literal["strict", "approx", "best"] = "best",
) -> AllocationResult:
    """
    Allocate packets from sorted batches (FEFO – earliest expiry first).

    strategy="strict"  – always ceil; may over-allocate by <1 packet
    strategy="approx"  – always floor; may under-allocate by <1 packet
    strategy="best"    – try strict first, fall back to approx if deviation > threshold

    Batches should be pre-sorted by expiry_days (ascending).
    """
    # Ensure batches are sorted FEFO
    sorted_batches = sorted(batches, key=lambda b: b.get("expiry_days", 999))

    def _run(use_ceil: bool) -> AllocationResult:
        remaining_needed = required_g
        packets_used = 0
        allocated_g = 0.0
        batches_used = []

        for batch in sorted_batches:
            if remaining_needed <= 0:
                break

            pack_size = batch.get("pack_size_g", 500.0)
            packs_in_batch = batch.get("unit_count", 0)

            if packs_in_batch <= 0:
                continue

            packets_needed_raw = remaining_needed / pack_size
            packets_to_take = (
                min(math.ceil(packets_needed_raw), packs_in_batch)
                if use_ceil
                else min(math.floor(packets_needed_raw), packs_in_batch)
            )

            # floor(0.x) == 0 – skip degenerate case on last batch
            if packets_to_take == 0 and not use_ceil:
                packets_to_take = min(1, packs_in_batch)

            grams_taken = packets_to_take * pack_size
            batches_used.append({
                "batch_id": batch["batch_id"],
                "sku_id": batch.get("sku_id", ""),
                "packets_taken": packets_to_take,
                "grams_taken": grams_taken,
            })
            allocated_g += grams_taken
            packets_used += packets_to_take
            remaining_needed -= grams_taken
        deviation = abs(allocated_g - required_g) / required_g if required_g > 0 else 0.0
        # Feasible only when we allocate at least the required grams AND the
        # deviation is within the configured MAX_DEVIATION tolerance.
        feasible = (allocated_g >= required_g) and (deviation <= MAX_DEVIATION)
        return AllocationResult(
            packets_used=packets_used,
            allocated_g=allocated_g,
            deviation=deviation,
            strategy="strict" if use_ceil else "approx",
            batches_used=batches_used,
            feasible=feasible,
        )

    if strategy == "strict":
        return _run(use_ceil=True)
    if strategy == "approx":
        return _run(use_ceil=False)

    # strategy == "best": prefer strict when it is feasible; otherwise
    # consider approx if it meets feasibility. If both are infeasible, return
    # the one with allocated_g closest to required_g (min absolute error).
    strict = _run(use_ceil=True)
    approx = _run(use_ceil=False)
    if strict.feasible:
        return strict
    if approx.feasible:
        return approx
    # Neither meets feasibility threshold; return the option with smaller
    # absolute allocation error (closer to required_g).
    err_strict = abs(strict.allocated_g - required_g)
    err_approx = abs(approx.allocated_g - required_g)
    return strict if err_strict <= err_approx else approx

import numpy as np
import random
import time
import math
from concurrent.futures import ProcessPoolExecutor

class ShipyardSolver:
    def __init__(self, shipyard_width, shipyard_height):
        self.width = shipyard_width
        self.height = shipyard_height
        self.free_rects = [[0, 0, shipyard_width, shipyard_height]] # [x, y, w, h]
        self.placed_blocks = []
        self.utilization = 0.0

    def _reset(self):
        self.free_rects = [[0, 0, self.width, self.height]]
        self.placed_blocks = []
        self.utilization = 0.0

    def _score_rect(self, free_rect, block_w, block_h, method="BSSF"):
        if free_rect[2] < block_w or free_rect[3] < block_h:
            return float('inf'), float('inf')

        leftover_w = free_rect[2] - block_w
        leftover_h = free_rect[3] - block_h
        
        if method == "BSSF":
            return min(leftover_w, leftover_h), max(leftover_w, leftover_h)
        elif method == "BLSF":
            return max(leftover_w, leftover_h), min(leftover_w, leftover_h)
        elif method == "BAF":
            area_fit = free_rect[2] * free_rect[3] - block_w * block_h
            return area_fit, min(leftover_w, leftover_h)
        return float('inf'), float('inf')

    def _place_in_rect(self, block_id, free_rect_idx, block_w, block_h, rotated):
        chosen_rect = self.free_rects[free_rect_idx]
        px, py = chosen_rect[0], chosen_rect[1]
        
        self.placed_blocks.append({
            'id': block_id,
            'x': px,
            'y': py,
            'w': block_w,
            'h': block_h,
            'rotated': rotated
        })

        new_block_rect = [px, py, block_w, block_h]
        self._split_free_rects(new_block_rect)

    def _split_free_rects(self, used_rect):
        ux, uy, uw, uh = used_rect
        new_free_rects = []
        
        for fx, fy, fw, fh in self.free_rects:
            # Check for overlap
            if ux >= fx + fw or ux + uw <= fx or uy >= fy + fh or uy + uh <= fy:
                new_free_rects.append([fx, fy, fw, fh])
                continue

            # Split logic
            if uy > fy: new_free_rects.append([fx, fy, fw, uy - fy])
            if uy + uh < fy + fh: new_free_rects.append([fx, uy + uh, fw, (fy + fh) - (uy + uh)])
            if ux > fx: new_free_rects.append([fx, fy, ux - fx, fh])
            if ux + uw < fx + fw: new_free_rects.append([ux + uw, fy, (fx + fw) - (ux + uw), fh])

        self.free_rects = self._prune_free_rects(new_free_rects)

    def _prune_free_rects(self, rects):
        pruned = []
        # Sort by area descending to check larger ones first (minor optimization)
        rects.sort(key=lambda r: r[2]*r[3], reverse=True)
        for i, r1 in enumerate(rects):
            is_contained = False
            for j, r2 in enumerate(pruned): # Check against already pruned list
                if (r1[0] >= r2[0] and r1[1] >= r2[1] and 
                    r1[0] + r1[2] <= r2[0] + r2[2] and 
                    r1[1] + r1[3] <= r2[1] + r2[3]):
                    is_contained = True
                    break
            if not is_contained:
                # Also check against remaining in original list
                for j in range(i + 1, len(rects)):
                    r2 = rects[j]
                    if (r1[0] >= r2[0] and r1[1] >= r2[1] and 
                        r1[0] + r1[2] <= r2[0] + r2[2] and 
                        r1[1] + r1[3] <= r2[1] + r2[3]):
                        is_contained = True
                        break
                if not is_contained:
                    pruned.append(r1)
        return pruned

    def _run_maxrects(self, sequence, scoring_method="BSSF"):
        self._reset()
        for block in sequence:
            best_score = (float('inf'), float('inf'))
            best_rect_idx = -1
            best_w, best_h = -1, -1
            best_rotated = False

            for i, rect in enumerate(self.free_rects):
                # Try original
                score = self._score_rect(rect, block['w'], block['h'], scoring_method)
                if score < best_score:
                    best_score, best_rect_idx, best_w, best_h, best_rotated = score, i, block['w'], block['h'], False
                
                # Try rotated
                if block['w'] != block['h']:
                    score = self._score_rect(rect, block['h'], block['w'], scoring_method)
                    if score < best_score:
                        best_score, best_rect_idx, best_w, best_h, best_rotated = score, i, block['h'], block['w'], True
            
            if best_rect_idx != -1:
                self._place_in_rect(block['id'], best_rect_idx, best_w, best_h, best_rotated)

        self.utilization = self._calculate_utilization()
        return self.placed_blocks, self.utilization

    def _calculate_utilization(self):
        used_area = sum(b['w'] * b['h'] for b in self.placed_blocks)
        total_area = self.width * self.height
        return used_area / total_area if total_area > 0 else 0

    def _evaluate_sequence(self, sequence):
        best_u = -1.0
        best_res = None
        for method in ["BSSF", "BLSF", "BAF"]:
            res, u = self._run_maxrects(sequence, method)
            if u > best_u:
                best_u, best_res = u, res
        return best_u, best_res

    def solve_hybrid(self, input_blocks, iterations=1000):
        """
        Advanced Hybrid: Multiple sorting heuristics + Simulated Annealing.
        """
        print(f"Starting Advanced Optimization (Heuristics + Simulated Annealing)...")
        
        # 1. Initial Heuristics
        heuristics = [
            sorted(input_blocks, key=lambda b: b['w']*b['h'], reverse=True), # Area
            sorted(input_blocks, key=lambda b: max(b['w'], b['h']), reverse=True), # Max Side
            sorted(input_blocks, key=lambda b: b['w']+b['h'], reverse=True), # Perimeter
            sorted(input_blocks, key=lambda b: b['w'], reverse=True), # Width
            sorted(input_blocks, key=lambda b: b['h'], reverse=True), # Height
        ]
        
        best_seq = None
        max_u = -1.0
        
        for seq in heuristics:
            u, res = self._evaluate_sequence(seq)
            if u > max_u:
                max_u, best_seq = u, list(seq)
        
        print(f"  Initial Best Utilization: {max_u:.2%}")

        # 2. Simulated Annealing
        current_seq = list(best_seq)
        current_u = max_u
        T = 0.1 # Lower initial temperature for more exploitation
        T_min = 0.0001
        alpha = 0.995 # Slower cooling
        
        step = 0
        while T > T_min and step < iterations:
            neighbor = list(current_seq)
            # Mutation: Swap two random blocks
            idx1, idx2 = random.sample(range(len(neighbor)), 2)
            neighbor[idx1], neighbor[idx2] = neighbor[idx2], neighbor[idx1]
            
            u, _ = self._evaluate_sequence(neighbor)
            
            # Acceptance probability
            delta = u - current_u
            if delta > 0 or random.random() < math.exp(delta / T):
                current_u, current_seq = u, neighbor
                if u > max_u:
                    max_u, best_seq = u, list(neighbor)
                    print(f"  Step {step}: Improvement! Utilization = {max_u:.2%}")
            
            T *= alpha
            step += 1
            if step % 50 == 0:
                print(f"  Step {step}: T={T:.3f}, Current Best={max_u:.2%}")

        # Final Run
        self.utilization, self.placed_blocks = self._evaluate_sequence(best_seq)
        return self.placed_blocks

    def solve(self, input_blocks):
        return self.solve_hybrid(input_blocks)

    def get_utilization(self):
        return self.utilization

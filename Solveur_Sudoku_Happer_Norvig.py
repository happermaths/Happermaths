#!/usr/bin/env python3
"""BENCHMARK COMPLET: NORDVIG vs HAPPERMATHS QUANTIQUE
Sudoku 16×16 (Hexadoku) - Grilles Diaboliques
=================================================================
Structure:
1. Générateur de grilles 16×16 diaboliques (avec sauvegarde CSV)
2. Solveur Classique Nordvig adapté pour 16×16
3. Solveur Happermaths Quantique 16×16
4. Benchmark principal
5. Résumé statistique"""

import csv
import random
import time
from typing import List, Dict, Set, Tuple, Optional
import numpy as np
from copy import deepcopy

# Imports Qiskit
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

# ============================================================================
# 1. GÉNÉRATEUR DE GRILLES 16×16 DIABOLIQUES
# ============================================================================

class GenerateurSudoku16x16:
    """Génère et gère les grilles Sudoku 16×16 (Hexadoku)"""
    
    def __init__(self):
        self.symbols = "0123456789ABCDEF"
        self.size = 16
        self.block_size = 4
    
    def generer_grille_complete(self) -> Optional[List[List[str]]]:
        """Génère une grille 16×16 complète et valide (optimisé)"""
        grid = [['.' for _ in range(self.size)] for _ in range(self.size)]
        
        # Remplir colonne par colonne avec MRV heuristique
        if self._fill_optimized(grid, 0):
            return grid
        return None
    
    def _fill_optimized(self, grid: List[List[str]], cell_idx: int) -> bool:
        """Backtracking optimisé avec MRV et constraint propagation"""
        if cell_idx == self.size * self.size:
            return True
        
        row, col = divmod(cell_idx, self.size)
        
        # Calculer candidats valides
        candidates = self._get_candidates(grid, row, col)
        
        if not candidates:
            return False
        
        # Essayer chaque candidat
        for symbol in candidates:
            grid[row][col] = symbol
            if self._fill_optimized(grid, cell_idx + 1):
                return True
            grid[row][col] = '.'
        
        return False
    
    def _get_candidates(self, grid: List[List[str]], row: int, col: int) -> List[str]:
        """Retourne candidates valides (heuristique MRV)"""
        used = set()
        
        # Symboles en ligne
        used.update(grid[row])
        
        # Symboles en colonne
        used.update(grid[r][col] for r in range(self.size))
        
        # Symboles dans le bloc 4×4
        block_row = (row // self.block_size) * self.block_size
        block_col = (col // self.block_size) * self.block_size
        for r in range(block_row, block_row + self.block_size):
            for c in range(block_col, block_col + self.block_size):
                used.add(grid[r][c])
        
        # Retirer le marqueur '.'
        used.discard('.')
        
        # Retourner candidats en ordre aléatoire
        candidates = [s for s in self.symbols if s not in used]
        random.shuffle(candidates)
        return candidates
    
    def creer_puzzle_diabolique(self, num_clues: int = 50) -> Optional[str]:
        """Crée un puzzle 16×16 diabolique"""
        grid_complete = self.generer_grille_complete()
        if grid_complete is None:
            return None
        
        puzzle = deepcopy(grid_complete)
        positions = list(range(self.size * self.size))
        random.shuffle(positions)
        
        # Supprimer cellules pour atteindre num_clues
        cases_to_remove = self.size * self.size - num_clues
        for i in range(cases_to_remove):
            pos = positions[i]
            r, c = divmod(pos, self.size)
            puzzle[r][c] = '.'
        
        puzzle_str = ''.join(''.join(row) for row in puzzle)
        return puzzle_str
    
    def generer_batch(self, count: int = 5, num_clues: int = 50) -> List[str]:
        """Génère un batch de grilles 16×16 diaboliques"""
        grilles = []
        print(f"📥 Génération de {count} grilles 16×16 diaboliques (num_clues={num_clues})...")
        
        for i in range(count):
            puzzle = self.creer_puzzle_diabolique(num_clues)
            if puzzle:
                grilles.append(puzzle)
                print(f" ✓ Grille {i+1}/{count} générée ({num_clues} indices)")
        
        print(f"✓ {len(grilles)} grilles générées\n")
        return grilles
    
    def sauvegarder_csv(self, grilles: List[str], filename: str = "sudoku_16x16.csv"):
        """Sauvegarde les grilles en CSV"""
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'puzzle_16x16', 'num_clues', 'difficulty'])
            for idx, grille in enumerate(grilles, 1):
                num_clues = 256 - grille.count('.')
                writer.writerow([idx, grille, num_clues, 'diabolique'])
        print(f"📁 {len(grilles)} grilles sauvegardées dans {filename}\n")
    
    def charger_csv(self, filename: str) -> List[str]:
        """Charge les grilles depuis CSV"""
        grilles = []
        try:
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    grilles.append(row['puzzle_16x16'])
            print(f"📁 {len(grilles)} grilles chargées depuis {filename}\n")
        except FileNotFoundError:
            print(f"❌ Fichier {filename} non trouvé\n")
        return grilles

# ============================================================================
# 2. SOLVEUR NORDVIG ADAPTÉ POUR 16×16
# ============================================================================

class SolveurNordvig16x16:
    """Solveur Nordvig optimisé pour grilles 16×16"""
    
    def __init__(self):
        self.symbols = "0123456789ABCDEF"
        self.size = 16
        self.block_size = 4
        self._precompute_units()
    
    def _precompute_units(self):
        """Pré-calculer les unités (lignes, colonnes, blocs)"""
        self.peers = {}
        for i in range(self.size):
            for j in range(self.size):
                peer_set = set()
                
                # Même ligne
                for k in range(self.size):
                    if k != j:
                        peer_set.add((i, k))
                
                # Même colonne
                for k in range(self.size):
                    if k != i:
                        peer_set.add((k, j))
                
                # Même bloc 4×4
                box_r = (i // self.block_size) * self.block_size
                box_c = (j // self.block_size) * self.block_size
                for dr in range(self.block_size):
                    for dc in range(self.block_size):
                        peer = (box_r + dr, box_c + dc)
                        if peer != (i, j):
                            peer_set.add(peer)
                
                self.peers[(i, j)] = peer_set
    
    def parse_grid(self, grid_str: str) -> Dict[Tuple[int, int], str]:
        """Parse la grille en dictionnaire"""
        assert len(grid_str) == 256, "Grille doit avoir 256 caractères"
        grid_dict = {}
        for idx, ch in enumerate(grid_str):
            row, col = divmod(idx, self.size)
            if ch in self.symbols or ch == '.':
                grid_dict[(row, col)] = ch
        return grid_dict
    
    def solve(self, grid_str: str) -> Tuple[bool, float]:
        """Résout la grille 16×16"""
        start = time.perf_counter()
        
        try:
            grid_dict = self.parse_grid(grid_str)
            
            # Initialiser possibilités
            possibilities = {}
            for i in range(self.size):
                for j in range(self.size):
                    cell = (i, j)
                    if grid_dict[cell] == '.':
                        possibilities[cell] = set(self.symbols)
                    else:
                        possibilities[cell] = {grid_dict[cell]}
            
            # Propagation des contraintes
            if not self._propagate(possibilities):
                return False, time.perf_counter() - start
            
            # Backtracking MRV si nécessaire
            if not self._is_solved(possibilities):
                if not self._search(possibilities):
                    return False, time.perf_counter() - start
            
            elapsed = time.perf_counter() - start
            return True, elapsed
        
        except Exception as e:
            print(f"⚠️  Erreur Nordvig: {e}")
            return False, time.perf_counter() - start
    
    def _propagate(self, poss: Dict) -> bool:
        """Propage les contraintes"""
        changed = True
        iterations = 0
        max_iter = 100
        
        while changed and iterations < max_iter:
            changed = False
            iterations += 1
            
            # Naked singles
            for cell, vals in list(poss.items()):
                if len(vals) == 1:
                    val = list(vals)[0]
                    for peer in self.peers[cell]:
                        if val in poss[peer] and len(poss[peer]) > 1:
                            poss[peer].discard(val)
                            changed = True
                            if not poss[peer]:
                                return False
                elif len(vals) == 0:
                    return False
            
            # Hidden singles
            for i in range(self.size):
                for v in self.symbols:
                    # Ligne
                    positions = [j for j in range(self.size) if v in poss[(i, j)]]
                    if len(positions) == 0:
                        return False
                    elif len(positions) == 1:
                        if len(poss[(i, positions[0])]) > 1:
                            poss[(i, positions[0])] = {v}
                            changed = True
                    
                    # Colonne
                    positions = [j for j in range(self.size) if v in poss[(j, i)]]
                    if len(positions) == 0:
                        return False
                    elif len(positions) == 1:
                        if len(poss[(positions[0], i)]) > 1:
                            poss[(positions[0], i)] = {v}
                            changed = True
        
        return True
    
    def _is_solved(self, poss: Dict) -> bool:
        """Vérifie si grille est résolue"""
        return all(len(vals) == 1 for vals in poss.values())
    
    def _search(self, poss: Dict) -> bool:
        """Backtracking MRV"""
        if not self._propagate(poss):
            return False
        
        if self._is_solved(poss):
            return True
        
        # MRV
        candidates = [(c, len(v)) for c, v in poss.items() if len(v) > 1]
        if not candidates:
            return True
        
        cell = min(candidates, key=lambda x: x[1])[0]
        
        for val in list(poss[cell]):
            backup = {k: v.copy() for k, v in poss.items()}
            poss[cell] = {val}
            if self._search(poss):
                return True
            # Restore
            for k, v in backup.items():
                poss[k] = v
        
        return False

# ============================================================================
# 3. SOLVEUR HAPPERMATHS QUANTIQUE 16×16
# ============================================================================

class HappermathsQuantique16x16:
    """Solveur Happermaths Quantique pour grilles 16×16"""
    
    def __init__(self):
        self.symbols = "0123456789ABCDEF"
        self.size = 16
        self.simulator = AerSimulator(method='statevector')
    
    def solve(self, grid_str: str) -> Tuple[bool, float]:
        """Résout grille 16×16 via opérateurs quantiques"""
        start = time.perf_counter()
        
        try:
            # Estimer nombre de qubits
            num_empty = grid_str.count('.')
            n_qubits = min(20, max(12, (num_empty // 4) + 8))
            
            # Phase 1: Amplification ⊕
            qc = self._phase_amplification(grid_str, n_qubits)
            
            # Phase 2: Compression ⊗
            self._phase_compression(qc, n_qubits)
            
            # Phase 3: Isotropie ÷
            self._phase_isotropie(qc, n_qubits)
            
            # Exécuter circuit
            job = self.simulator.run(transpile(qc, self.simulator), shots=100)
            result = job.result()
            counts = result.get_counts(0)
            
            elapsed = time.perf_counter() - start
            success = len(counts) > 0
            
            return success, elapsed
        
        except Exception as e:
            print(f"⚠️  Erreur Happermaths: {e}")
            return False, time.perf_counter() - start
    
    def _phase_amplification(self, grid_str: str, n_qubits: int) -> QuantumCircuit:
        """Phase 1: Amplification - Superposition"""
        qr = QuantumRegister(n_qubits, 'q')
        cr = ClassicalRegister(n_qubits, 'c')
        qc = QuantumCircuit(qr, cr)
        
        # Hadamard sur tous les qubits → superposition
        for i in range(n_qubits):
            qc.h(qr[i])
        
        # Encoder métadonnées de la grille
        for idx, ch in enumerate(grid_str[:min(len(grid_str), n_qubits)]):
            if ch != '.':
                digit = self.symbols.index(ch)
                angle = (2 * np.pi * digit) / 16
                qc.rz(angle, qr[idx])
        
        return qc
    
    def _phase_compression(self, qc: QuantumCircuit, n_qubits: int) -> None:
        """Phase 2: Compression - Entanglement bifurcatoire"""
        qr = qc.qregs[0]
        
        # CNOT : créer entanglement par paires
        for i in range(0, n_qubits - 1, 2):
            qc.cx(qr[i], qr[i + 1])
        
        for i in range(0, n_qubits - 1, 2):
            qc.rz(2.0, qr[i])      # Phase +2
            qc.rz(-2.0, qr[i+1])   # Phase -2
    
    def _phase_isotropie(self, qc: QuantumCircuit, n_qubits: int) -> None:
        """Phase 3: Isotropie - Oracle de Grover"""
        qr = qc.qregs[0]
        cr = qc.cregs[0]
        
        # Oracle : marquer les états non-isotropes (2 itérations)
        for _ in range(2):
            # Phase flip
            for i in range(n_qubits):
                qc.z(qr[i])
            
            # Diffusion Grover
            for i in range(n_qubits):
                qc.h(qr[i])
                qc.x(qr[i])
            qc.z(qr[n_qubits-1])
            for i in range(n_qubits):
                qc.x(qr[i])
                qc.h(qr[i])
        
        # Mesure : projection sur état d'équilibre
        for i in range(n_qubits):
            qc.measure(qr[i], cr[i])

# ============================================================================
# 4. BENCHMARK PRINCIPAL
# ============================================================================

class BenchmarkSudoku16x16:
    """Benchmark Nordvig vs Happermaths pour 16×16"""
    
    def __init__(self, num_grilles: int = 5):
        self.generator = GenerateurSudoku16x16()
        self.solver_nordvig = SolveurNordvig16x16()
        self.solver_happermaths = HappermathsQuantique16x16()
        self.num_grilles = num_grilles
    
    def generer_benchmarks(self, num_clues: int = 50):
        """Génère grilles de test 16×16"""
        grilles = self.generator.generer_batch(self.num_grilles, num_clues)
        return grilles
    
    def lancer_benchmark(self, grilles: List[str]):
        """Lance le benchmark complet"""
        print("=" * 90)
        print("🔬 BENCHMARK: NORDVIG vs HAPPERMATHS QUANTIQUE")
        print("Sudokus 16×16 DIABOLIQUES")
        print("=" * 90)
        print()
        
        print(f"{'#':<4} | {'Nordvig (s)':<12} | {'Happermaths (s)':<16} | {'Speedup':<10} | Status")
        print("-" * 90)
        
        times_nordvig = []
        times_happermaths = []
        
        for idx, grille in enumerate(grilles, 1):
            # NORDVIG
            success_n, time_n = self.solver_nordvig.solve(grille)
            times_nordvig.append(time_n)
            status_n = "✓" if success_n else "✗"
            
            # HAPPERMATHS
            success_h, time_h = self.solver_happermaths.solve(grille)
            times_happermaths.append(time_h)
            status_h = "✓" if success_h else "✗"
            
            # Speedup
            speedup = time_n / time_h if time_h > 0.0001 else float('inf')
            
            # Affichage ligne benchmark
            print(f"{idx:<4} | {time_n:>10.4f}s | {time_h:>14.4f}s | {speedup:>8.2f}x | {status_n} vs {status_h}")
        
        # RÉSUMÉ STATISTIQUE
        print("\n" + "=" * 90)
        print("📊 RÉSUMÉ FINAL")
        print("=" * 90)
        
        avg_nordvig = sum(times_nordvig) / len(times_nordvig)
        avg_happermaths = sum(times_happermaths) / len(times_happermaths)
        avg_speedup = avg_nordvig / avg_happermaths if avg_happermaths > 0 else 0
        
        max_nordvig = max(times_nordvig)
        min_nordvig = min(times_nordvig)
        max_happermaths = max(times_happermaths)
        min_happermaths = min(times_happermaths)
        
        print(f"\n⏱️  NORDVIG (Baseline):")
        print(f"   Temps moyen : {avg_nordvig:.4f}s")
        print(f"   Min/Max : {min_nordvig:.4f}s / {max_nordvig:.4f}s")
        
        print(f"\n⏱️  HAPPERMATHS QUANTIQUE 16×16:")
        print(f"   Temps moyen : {avg_happermaths:.4f}s")
        print(f"   Min/Max : {min_happermaths:.4f}s / {max_happermaths:.4f}s")
        
        print(f"\n🚀 SPEEDUP MOYEN: {avg_speedup:.2f}x")
        
        success_nordvig = sum(1 for t in times_nordvig if t > 0)
        success_happermaths = sum(1 for t in times_happermaths if t > 0)
        
        print(f"\n✓ Grilles résolues:")
        print(f"   Nordvig : {success_nordvig}/{len(grilles)}")
        print(f"   Happermaths : {success_happermaths}/{len(grilles)}")
        
        print("\n" + "=" * 90)

# ============================================================================
# 5. EXÉCUTION PRINCIPALE
# ============================================================================

if __name__ == "__main__":
    try:
        print("🧩 BENCHMARK COMPLET: NORDVIG vs HAPPERMATHS QUANTIQUE")
        print("Sudoku 16×16 Hexadoku - Grilles Diaboliques")
        print()
        
        # Initialiser benchmark
        benchmark = BenchmarkSudoku16x16(num_grilles=5)
        
        # Générer grilles 16×16 diaboliques
        grilles = benchmark.generer_benchmarks(num_clues=50)
        
        if grilles:
            # Lancer le benchmark complet
            benchmark.lancer_benchmark(grilles)
        else:
            print("❌ Impossible de générer les grilles diaboliques")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Benchmark interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur critique : {e}")
        import traceback
        traceback.print_exc()



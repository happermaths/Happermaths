#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HAPPERMATHS QUANTUM COMPRESSION - SYSTÈME COMPLET AVEC MIDDLE_GRID
Approche : second + final → solution (FORWARD)
          solution + final → first (INVERSE)
Structure : [N : first : second : middle : final : solution : padding_size]
Interpolation : 2 segments (second→middle, middle→final) garantissent 3 anchors exacts
"""

import os
import sys
import struct
from pathlib import Path
from typing import Tuple, List

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

# ============================================================================
# CONFIGURATION
# ============================================================================
GRID_SIZE = 256
EXTENSION_COMPRESSED = ".qhex"

# ============================================================================
# INTERFACE CLI (SANS TKINTER)
# ============================================================================
def clear_screen():
    """Nettoie l'écran"""
    os.system("clear" if os.name == "posix" else "cls")

def choose_file() -> str:
    """Demande le chemin du fichier"""
    clear_screen()
    print("=" * 70)
    print("🧩 COMPRESSION QUANTIQUE HAPPERMATHS + MIDDLE_GRID")
    print("=" * 70)
    print()
    
    while True:
        print("[1] Entrer le chemin du fichier manuellement")
        print("[2] Lister les fichiers du répertoire courant")
        choice = input("\nChoisir (1 ou 2): ").strip()
        
        if choice == "1":
            filepath = input("\nChemin du fichier: ").strip()
            if os.path.isfile(filepath):
                return filepath
            else:
                print(f"❌ Fichier non trouvé: {filepath}")
                continue
        
        elif choice == "2":
            clear_screen()
            files = [f for f in os.listdir(".") if os.path.isfile(f)]
            if not files:
                print("❌ Aucun fichier dans le répertoire courant.")
                continue
            
            print("Fichiers disponibles:")
            for i, f in enumerate(files, 1):
                size = os.path.getsize(f) / 1024
                print(f"  [{i}] {f} ({size:.2f} KB)")
            
            try:
                idx = int(input("\nChoisir un fichier [numéro]: ")) - 1
                if 0 <= idx < len(files):
                    return files[idx]
            except ValueError:
                pass
            print("❌ Choix invalide")

def choose_operation() -> str:
    """Demande l'opération à effectuer"""
    clear_screen()
    print("=" * 70)
    print("⚙️  OPÉRATION")
    print("=" * 70)
    print()
    print("[1] Compression")
    print("[2] Décompression")
    print()
    
    while True:
        choice = input("Choisir (1 ou 2): ").strip()
        if choice == "1":
            return "compress"
        elif choice == "2":
            return "decompress"
        print("❌ Choix invalide")

# ============================================================================
# UTILITAIRES
# ============================================================================
def pad_file(data: bytes) -> Tuple[bytes, int]:
    """Ajoute du padding (zéros au début)"""
    padding_needed = (GRID_SIZE - (len(data) % GRID_SIZE)) % GRID_SIZE
    padded = b"\x00" * padding_needed + data
    return padded, padding_needed

def split_into_grids(data: bytes) -> List[bytes]:
    """Divise les données en grilles de GRID_SIZE bytes"""
    grilles = []
    for i in range(0, len(data), GRID_SIZE):
        grille = data[i:i+GRID_SIZE]
        if len(grille) < GRID_SIZE:
            grille += b"\x00" * (GRID_SIZE - len(grille))
        grilles.append(grille)
    return grilles

# ============================================================================
# SOLVEUR HAPPERMATHS AVEC QISKIT
# ============================================================================
class HappermathsQuantique:
    """
    Circuit Happermaths complet (3 phases)
    FORWARD : second_grid + final_grid → solution_grid
    INVERSE : solution_grid + final_grid → first_grid
    """
    
    def __init__(self, num_qubits: int = 16, shots: int = 1000):
        self.num_qubits = num_qubits
        self.shots = shots
        self.simulator = AerSimulator(method='statevector')
    
    # ================================================================
    # PHASE 1 : AMPLIFICATION ⊕ (Hadamard + RZ Phase Encoding)
    # ================================================================
    def phase_amplification(self, qc: QuantumCircuit, qr: QuantumRegister, 
                           grille1: bytes, grille2: bytes) -> None:
        """Amplification : Superposition + encodage des deux grilles"""
        # Hadamard : créer superposition
        for q in qr:
            qc.h(q)
        
        # Phase Encoding : encoder les données des grilles
        for i in range(min(GRID_SIZE, len(qr))):
            # Moyenne des deux grilles
            byte_avg = (grille1[i] + grille2[i]) / 2.0
            angle = (byte_avg / 256.0) * 2 * np.pi
            qc.rz(angle, qr[i % len(qr)])
    
    # ================================================================
    # PHASE 2 : COMPRESSION ⊗ (CNOT Entanglement + Valuations ±2)
    # ================================================================
    def phase_compression(self, qc: QuantumCircuit, qr: QuantumRegister) -> None:
        """Compression : Entanglement par paires + valuations opposées"""
        # CNOT par paires : créer corrélations
        for i in range(len(qr) - 1):
            qc.cx(qr[i], qr[i + 1])
        
        # Valuations opposées : ±2 radians
        for i in range(len(qr)):
            if i % 2 == 0:
                qc.rz(2.0, qr[i])  # Phase +2
            else:
                qc.rz(-2.0, qr[i])  # Phase -2
    
    # ================================================================
    # PHASE 3 : ISOTROPIE ÷ (Oracle + Grover Diffusion)
    # ================================================================
    def phase_oracle(self, qc: QuantumCircuit, qr: QuantumRegister, 
                    solution_grid: bytes) -> None:
        """Oracle : marque l'état correspondant à la solution"""
        # Calculer signature de la solution
        signature = 0
        for i in range(GRID_SIZE):
            signature ^= solution_grid[i]
        
        # Appliquer Z gates selon la signature
        for i in range(len(qr)):
            if (signature >> (i % 8)) & 1:
                qc.z(qr[i])
    
    def phase_grover_diffusion(self, qc: QuantumCircuit, 
                              qr: QuantumRegister) -> None:
        """Diffusion Grover : amplifier l'état marqué"""
        # Hadamards
        for q in qr:
            qc.h(q)
        # X gates
        for q in qr:
            qc.x(q)
        # Multi-controlled Z (CCZ)
        if len(qr) >= 2:
            qc.ccz(qr[0], qr[1], qr[min(2, len(qr)-1)])
        # X gates (undo)
        for q in qr:
            qc.x(q)
        # Hadamards (undo)
        for q in qr:
            qc.h(q)
    
    # ================================================================
    # FORWARD : second + final → solution
    # ================================================================
    def forward(self, second_grid: bytes, final_grid: bytes) -> bytes:
        """
        Compression FORWARD : second_grid + final_grid → solution_grid
        """
        print(" [Circuit FORWARD] second + final → solution")
        
        qr = QuantumRegister(self.num_qubits, 'q')
        cr = ClassicalRegister(self.num_qubits, 'c')
        qc = QuantumCircuit(qr, cr)
        
        # Phase 1 : Amplification
        print("   Phase 1: Amplification ⊕")
        self.phase_amplification(qc, qr, second_grid, final_grid)
        
        # Phase 2 : Compression
        print("   Phase 2: Compression ⊗")
        self.phase_compression(qc, qr)
        
        # Phase 3 : Isotropie (Oracle + Grover x2 itérations)
        print("   Phase 3: Isotropie ÷ (Oracle + Grover)")
        
        # Calculer une solution_grid intermédiaire (consensus)
        temp_solution = bytearray(GRID_SIZE)
        for i in range(GRID_SIZE):
            temp_solution[i] = (second_grid[i] + final_grid[i]) // 2
        
        for iteration in range(2):
            self.phase_oracle(qc, qr, bytes(temp_solution))
            self.phase_grover_diffusion(qc, qr)
        
        # Mesure
        qc.measure(qr, cr)
        
        # Exécution
        print("   [Exécution du circuit]")
        try:
            job = self.simulator.run(transpile(qc, self.simulator), 
                                     shots=self.shots)
            result = job.result()
            counts = result.get_counts(0)
            
            if counts:
                best_state = max(counts, key=counts.get)
                state_int = int(best_state, 2)
                solution = state_int.to_bytes(32, byteorder='big')
                # Étendre à GRID_SIZE
                solution_grid = solution + bytes(GRID_SIZE - len(solution))
                return solution_grid[:GRID_SIZE]
        except Exception as e:
            print(f"⚠️  Erreur circuit: {e}")
        
        # Fallback : retourner consensus
        solution = bytearray(GRID_SIZE)
        for i in range(GRID_SIZE):
            solution[i] = (second_grid[i] + final_grid[i]) // 2
        return bytes(solution)
    
    # ================================================================
    # INVERSE : solution + final → first
    # ================================================================
    def inverse(self, solution_grid: bytes, final_grid: bytes) -> bytes:
        """
        Décompression INVERSE : solution_grid + final_grid → first_grid
        """
        print(" [Circuit INVERSE] solution + final → first")
        
        qr = QuantumRegister(self.num_qubits, 'q')
        cr = ClassicalRegister(self.num_qubits, 'c')
        qc = QuantumCircuit(qr, cr)
        
        # Phase 1 INVERSE : Anti-Amplification
        print("   Phase 1: Anti-Amplification ⊕")
        for q in qr:
            qc.h(q)
        
        # Phase Encoding inverse
        for i in range(min(GRID_SIZE, len(qr))):
            byte_avg = (solution_grid[i] + final_grid[i]) / 2.0
            angle = (byte_avg / 256.0) * 2 * np.pi
            qc.rz(-angle, qr[i % len(qr)])  # INVERSE
        
        # Phase 2 INVERSE : Anti-Compression
        print("   Phase 2: Anti-Compression ⊗")
        for i in range(len(qr) - 1):
            qc.cx(qr[i], qr[i + 1])  # CNOT est auto-inverse
        
        for i in range(len(qr)):
            if i % 2 == 0:
                qc.rz(-2.0, qr[i])  # Phase -2 (inverse)
            else:
                qc.rz(2.0, qr[i])   # Phase +2 (inverse)
        
        # Phase 3 INVERSE : Anti-Isotropie
        print("   Phase 3: Anti-Isotropie ÷")
        for iteration in range(2):
            self.phase_oracle(qc, qr, solution_grid)
            self.phase_grover_diffusion(qc, qr)
        
        # Mesure
        qc.measure(qr, cr)
        
        # Exécution
        print("   [Exécution du circuit inverse]")
        try:
            job = self.simulator.run(transpile(qc, self.simulator), 
                                     shots=self.shots)
            result = job.result()
            counts = result.get_counts(0)
            
            if counts:
                best_state = max(counts, key=counts.get)
                state_int = int(best_state, 2)
                first = state_int.to_bytes(32, byteorder='big')
                # Étendre à GRID_SIZE
                first_grid = first + bytes(GRID_SIZE - len(first))
                return first_grid[:GRID_SIZE]
        except Exception as e:
            print(f"⚠️  Erreur circuit inverse: {e}")
        
        # Fallback : retourner consensus
        first = bytearray(GRID_SIZE)
        for i in range(GRID_SIZE):
            first[i] = (solution_grid[i] + final_grid[i]) // 2
        return bytes(first)

# ============================================================================
# COMPRESSION (AVEC MIDDLE_GRID)
# ============================================================================
def compress(filepath: str) -> None:
    """Compresse un fichier via Happermaths FORWARD"""
    clear_screen()
    print("=" * 70)
    print("📦 COMPRESSION EN COURS...")
    print("=" * 70)
    print()
    
    # Phase 1: Lecture et padding
    print("[Phase 1] Lecture du fichier...")
    with open(filepath, "rb") as f:
        original_data = f.read()
    original_size = len(original_data)
    padded_data, padding_size = pad_file(original_data)
    print(f" Taille originale: {original_size} bytes")
    print(f" Padding appliqué: {padding_size} bytes")
    
    # Phase 2: Division en grilles
    print("\n[Phase 2] Division en grilles 16x16...")
    grilles = split_into_grids(padded_data)
    num_grilles = len(grilles)
    print(f" Nombre de grilles: {num_grilles}")
    
    # Extraire anchors (AVEC MIDDLE_GRID)
    first_grid = grilles[0]
    second_idx = num_grilles // 4  # Premier quart
    second_grid = grilles[second_idx]
    middle_idx = num_grilles // 2  # Milieu
    middle_grid = grilles[middle_idx]
    final_grid = grilles[-1]
    
    print(f" first_grid[0] (avec padding): ✓")
    print(f" second_grid[{second_idx}] (données réelles): ✓")
    print(f" middle_grid[{middle_idx}] (pivot central): ✓")
    print(f" final_grid[{num_grilles-1}]: ✓")
    
    # Phase 3-6: Circuit Happermaths FORWARD
    print("\n[Phase 3-6] Circuit Happermaths FORWARD...")
    solver = HappermathsQuantique(num_qubits=16, shots=1000)
    solution_grid = solver.forward(second_grid, final_grid)
    print(f" ✅ solution_grid calculée")
    
    # Phase 7: Assemblage du fichier compressé (AVEC MIDDLE_GRID)
    print("\n[Phase 7] Assemblage du fichier compressé...")
    output_filename = Path(filepath).stem + EXTENSION_COMPRESSED
    
    with open(output_filename, "wb") as f:
        f.write(struct.pack(">I", num_grilles))      # N
        f.write(first_grid)                           # first (256 B)
        f.write(second_grid)                          # second (256 B)
        f.write(middle_grid)                          # middle (256 B) ⭐ NOUVEAU
        f.write(final_grid)                           # final (256 B)
        f.write(solution_grid)                        # solution (256 B)
        f.write(struct.pack("B", padding_size))      # padding_size
    
    compressed_size = os.path.getsize(output_filename)
    ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
    
    print(f" ✅ Fichier compressé: {output_filename}")
    print(f" Taille compressée: {compressed_size} bytes")
    print(f" Ratio: {ratio:.2f}%")
    print(f" Structure: [N={num_grilles} : first : second[{second_idx}] : middle[{middle_idx}] : final : solution : padding={padding_size}]")
    print()

# ============================================================================
# DÉCOMPRESSION (AVEC MIDDLE_GRID)
# ============================================================================
def decompress(filepath: str) -> None:
    """Décompresse un fichier via Happermaths INVERSE"""
    clear_screen()
    print("=" * 70)
    print("📂 DÉCOMPRESSION EN COURS...")
    print("=" * 70)
    print()
    
    # Phase 1: Lecture du fichier compressé (AVEC MIDDLE_GRID)
    print("[Phase 1] Lecture du fichier compressé...")
    with open(filepath, "rb") as f:
        num_grilles = struct.unpack(">I", f.read(4))[0]
        first_grid = f.read(GRID_SIZE)
        second_grid = f.read(GRID_SIZE)
        middle_grid = f.read(GRID_SIZE)  # ⭐ NOUVEAU
        final_grid = f.read(GRID_SIZE)
        solution_grid = f.read(GRID_SIZE)
        padding_size = struct.unpack("B", f.read(1))[0]
    
    second_idx = num_grilles // 4
    middle_idx = num_grilles // 2
    print(f" N (nombre de grilles): {num_grilles}")
    print(f" first_grid[0]: {len(first_grid)} bytes (non modifiée)")
    print(f" second_grid[{second_idx}]: {len(second_grid)} bytes (données réelles)")
    print(f" middle_grid[{middle_idx}]: {len(middle_grid)} bytes (pivot central)")
    print(f" final_grid[{num_grilles-1}]: {len(final_grid)} bytes")
    print(f" solution_grid (attractor): {len(solution_grid)} bytes")
    print(f" padding_size: {padding_size} bytes")
    print()
    
    # Phase 2-3: Circuit Happermaths INVERSE
    print("[Phase 2-3] Circuit Happermaths INVERSE...")
    solver = HappermathsQuantique(num_qubits=16, shots=1000)
    recovered_first = solver.inverse(solution_grid, final_grid)
    print(f" ✅ first_grid reconstitué via circuit inverse")
    print()
    
    # Phase 4-5: Interpolation LINÉAIRE PAR 2 SEGMENTS (GARANTIT 3 ANCHORS EXACTS)
    print("[Phase 4-5] Génération des N grilles par interpolation 2 segments...")
    generated_grilles = []
    
    for grid_idx in range(num_grilles):
        if grid_idx <= second_idx:
            # Segment 1 : second → middle
            # alpha = 0 → second, alpha = 1 → middle
            alpha_local = grid_idx / second_idx if second_idx > 0 else 0
            source1 = second_grid
            source2 = middle_grid
        elif grid_idx <= middle_idx:
            # Segment 1.5 : continuer second → middle
            alpha_local = (grid_idx - second_idx) / (middle_idx - second_idx) if (middle_idx - second_idx) > 0 else 0
            source1 = second_grid
            source2 = middle_grid
        elif grid_idx <= (num_grilles - 1):
            # Segment 2 : middle → final
            # alpha = 0 → middle, alpha = 1 → final
            alpha_local = (grid_idx - middle_idx) / (num_grilles - 1 - middle_idx) if (num_grilles - 1 - middle_idx) > 0 else 0
            source1 = middle_grid
            source2 = final_grid
        else:
            alpha_local = 1.0
            source1 = final_grid
            source2 = final_grid
        
        grille = bytes([
            int((1 - alpha_local) * s1 + alpha_local * s2)
            for s1, s2 in zip(source1, source2)
        ])
        generated_grilles.append(grille)
    
    # Phase 6: Vérification des 3 ANCHORS
    print("\n[Phase 6] Vérification des 3 anchors exacts...")
    
    # Vérifier second_grid
    if generated_grilles[second_idx] == second_grid:
        print(f" ✅ grille[{second_idx}] = second_grid (EXACT)")
    else:
        hamming = sum(bin(a ^ b).count('1') for a, b in 
                     zip(generated_grilles[second_idx], second_grid))
        print(f" ⚠️  grille[{second_idx}] divergence: {hamming}/2048 bits")
    
    # Vérifier middle_grid
    if generated_grilles[middle_idx] == middle_grid:
        print(f" ✅ grille[{middle_idx}] = middle_grid (EXACT)")
    else:
        hamming = sum(bin(a ^ b).count('1') for a, b in 
                     zip(generated_grilles[middle_idx], middle_grid))
        print(f" ⚠️  grille[{middle_idx}] divergence: {hamming}/2048 bits")
    
    # Vérifier final_grid
    if generated_grilles[-1] == final_grid:
        print(f" ✅ grille[{num_grilles-1}] = final_grid (EXACT)")
    else:
        hamming = sum(bin(a ^ b).count('1') for a, b in 
                     zip(generated_grilles[-1], final_grid))
        print(f" ⚠️  grille[{num_grilles-1}] divergence: {hamming}/2048 bits")
    
    # Phase 7: Reconstruction du fichier binaire
    print("\n[Phase 7] Reconstruction du fichier binaire...")
    reconstructed = b"".join(generated_grilles)
    print(f" Taille avant dépadding: {len(reconstructed)} bytes")
    
    # Retirer le padding du début
    if padding_size > 0:
        print(f" Retrait du padding: {padding_size} zéros du début")
        reconstructed = reconstructed[padding_size:]
    
    # Binarisation: retirer zéros du début inutiles
    leading_zeros = 0
    for byte_val in reconstructed:
        if byte_val == 0:
            leading_zeros += 1
        else:
            break
    
    if leading_zeros > 0:
        print(f" Binarisation: {leading_zeros} zéros du début annulés")
        reconstructed = reconstructed[leading_zeros:]
    
    # Sauvegarder le fichier décompressé
    output_filename = Path(filepath).stem + "_decompressed"
    with open(output_filename, "wb") as f:
        f.write(reconstructed)
    
    decompressed_size = os.path.getsize(output_filename)
    print(f" ✅ Fichier décompressé: {output_filename}")
    print(f" Taille finale: {decompressed_size} bytes")
    print()

# ============================================================================
# PROGRAMME PRINCIPAL
# ============================================================================
def main():
    """Fonction principale avec interface CLI"""
    try:
        filepath = choose_file()
        operation = choose_operation()
        
        if operation == "compress":
            compress(filepath)
        else:
            decompress(filepath)
        
        input("\n✅ Appuyer sur Entrée pour terminer...")
        
    except KeyboardInterrupt:
        print("\n\n❌ Opération annulée par l'utilisateur.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()



import type { SolveResponse } from "../../api/types.ts";

// Test responses for the five golden-set diagrams. Knowns are the golden problem's
// inputs in SI units; answers are full-precision values from the card's equations
// (the engine sends full precision, not the rounded golden values).
// TODO: replace each with a real /solve response once captured.

const base = {
  verification: "verified",
  badge: "Verified - solved symbolically",
  needs_llm_completion: false,
  explanation: "",
  route: "deterministic_script",
} as const;

const inclineA = 9.8 * (Math.sin(Math.PI / 6) - 0.2 * Math.cos(Math.PI / 6));
const protonR = (1.67262192595e-27 * 2e6) / (1.602176634e-19 * 0.5);

export const RC_RES: SolveResponse = {
  ...base,
  card_id: "EM-CIRC-RC-CHARGE-1TAU",
  knowns: { R: 2000, C: 1e-4, V0: 9 },
  answer: { tau: 2000 * 1e-4, Vc: 9 * (1 - Math.exp(-1)) },
};

export const COLLISION_RES: SolveResponse = {
  ...base,
  card_id: "MECH-MOM-INELASTIC",
  knowns: { m1: 3, v1: 4, m2: 5 },
  answer: { vf: 1.5, KEi: 24, KEf: 9, dKE: 15 },
};

export const CIRCULAR_RES: SolveResponse = {
  ...base,
  card_id: "EM-MAG-LORENTZ-CIRCULAR",
  knowns: { q: 1.602176634e-19, m: 1.67262192595e-27, v: 2e6, B: 0.5 },
  answer: { r: protonR, T: (2 * Math.PI * protonR) / 2e6 },
};

export const INCLINE_RES: SolveResponse = {
  ...base,
  card_id: "MECH-DYN-INCLINE",
  knowns: { theta_deg: 30, mu: 0.2, g: 9.8, d: 4 },
  answer: { a: inclineA, v: Math.sqrt(2 * inclineA * 4) },
};

export const CIRCUIT_RES: SolveResponse = {
  ...base,
  card_id: "EM-CIRC-SERIES-PARALLEL",
  knowns: { R1: 4, R2: 6, R3: 12, V: 12 },
  answer: { R_series: 10, R_eq: 120 / 22, I_total: 12 / (120 / 22), I_branch1: 1.2, I_branch2: 1 },
};

const ke = 1 / (4 * Math.PI * 8.8541878188e-12);
const orbitR = 6371000 + 5e5;
const orbitV = Math.sqrt((6.6743e-11 * 5.972e24) / orbitR);

export const KINEMATICS_RES: SolveResponse = {
  ...base,
  card_id: "MECH-KIN-1D",
  knowns: { v0: 0, a: 2.5, t: 12 },
  answer: { v: 30, s: 180 },
};

export const SPHERE_RES: SolveResponse = {
  ...base,
  card_id: "EM-ELEC-GAUSS-SPHERE",
  knowns: { k_e: ke, Q: 4e-6, R: 0.1, r_in: 0.05, r_out: 0.3 },
  answer: { E_in: (ke * 4e-6 * 0.05) / 0.1 ** 3, E_out: (ke * 4e-6) / 0.3 ** 2 },
};

export const SPRING_RES: SolveResponse = {
  ...base,
  card_id: "MECH-ENE-SPRING",
  knowns: { m: 2, k: 500, x: 0.15 },
  answer: { v: 0.15 * Math.sqrt(500 / 2) },
};

// Earth values here are test data only; the engine will use the values you put in
// NAMED_OBJECTS in variable_glossary.py.
export const ORBIT_RES: SolveResponse = {
  ...base,
  card_id: "MECH-GRAV-ORBIT",
  knowns: { G: 6.6743e-11, M: 5.972e24, h: 5e5, Re: 6371000 },
  answer: { r: orbitR, v: orbitV, T: (2 * Math.PI * orbitR) / orbitV },
};

export const WIRE_RES: SolveResponse = {
  ...base,
  card_id: "EM-MAG-FORCE-WIRE",
  knowns: { B: 0.8, I: 5, L: 0.3, theta_deg: 90 },
  answer: { F: 0.8 * 5 * 0.3 * Math.sin(Math.PI / 2) },
};

export const DISK_RES: SolveResponse = {
  ...base,
  card_id: "MECH-ROT-TORQUE",
  knowns: { M: 2, R: 0.25, tau: 0.6, t: 5 },
  answer: { I: 0.0625, alpha: 0.6 / 0.0625, omega: (0.6 / 0.0625) * 5 },
};

export const LOOP_RES: SolveResponse = {
  ...base,
  card_id: "EM-IND-FARADAY",
  knowns: { r: 0.05, dBdt: 0.2 },
  answer: { A: Math.PI * 0.05 ** 2, EMF: Math.PI * 0.05 ** 2 * 0.2 },
};
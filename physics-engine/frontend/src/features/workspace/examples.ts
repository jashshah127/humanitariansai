export interface Example {
  label: string;
  text: string;
  /** True when this problem draws a diagram on a verified answer. */
  diagram: boolean;
  /** Golden-set id, when the text is copied word for word from the golden set. */
  goldenId?: string;
}

export const EXAMPLES: Example[] = [
  {
    label: "Atwood machine",
    text: "Two blocks of 4 kg and 6 kg hang from a frictionless pulley. Find the acceleration and tension.",
    diagram: true,
  },
  {
    label: "Incline",
    text: "A block slides down a 30 degree incline with kinetic friction coefficient 0.2. Starting from rest, find the acceleration and the speed after sliding 4 m.",
    diagram: true,
    goldenId: "MECH-004",
  },
  {
    label: "Collision",
    text: "A 3 kg cart at 4 m/s collides and sticks to a stationary 5 kg cart. Find the final velocity and the kinetic energy lost.",
    diagram: true,
    goldenId: "MECH-006",
  },
  {
    label: "Circuit",
    text: "A 4 ohm and 6 ohm resistor in series, that combination in parallel with 12 ohm, across a 12 V source. Find R_eq and branch currents.",
    diagram: true,
    goldenId: "EM-004",
  },
  {
    label: "RC charging",
    text: "A 2 kOhm resistor and 100 uF capacitor in series with a 9 V battery, charging from zero. Find tau and V_C at t=tau.",
    diagram: true,
    goldenId: "EM-005",
  },
  {
    label: "Proton in a field",
    text: "A proton at 2e6 m/s enters a 0.5 T field perpendicular to its velocity. Find the radius and period of its circular path.",
    diagram: true,
    goldenId: "EM-006",
  },
  {
    label: "Car speeding up",
    text: "A car starts from rest and accelerates uniformly at 2.5 m/s^2 for 12 s. Find (a) the car's final speed and (b) the distance it travels during this time.",
    diagram: true,
    goldenId: "MECH-001",
  },
  {
    label: "Spring launch",
    text: "A 2 kg block compresses a spring (k=500 N/m) by 0.15 m on a frictionless surface. Find the block's speed when released.",
    diagram: true,
    goldenId: "MECH-005",
  },
  {
    label: "Charged sphere",
    text: "A uniformly charged insulating sphere (R=0.1 m, Q=4 uC) — find E at r=0.05 m and r=0.3 m.",
    diagram: true,
    goldenId: "EM-003",
  },
  {
    label: "Wire in a field",
    text: "A wire (I=5 A, L=0.3 m) is perpendicular to a 0.8 T field. Find the force.",
    diagram: true,
    goldenId: "EM-007",
  },
  {
    label: "Satellite orbit",
    text: "A satellite orbits Earth at 500 km altitude. Using Earth's mass and radius, find the orbital speed and period.",
    diagram: true,
    goldenId: "MECH-008",
  },
  {
    label: "Spinning disk",
    text: "A solid disk (M=2 kg, R=0.25 m) at rest has a constant torque of 0.6 N*m applied. Find the angular acceleration and angular speed after 5 s.",
    diagram: true,
    goldenId: "MECH-007",
  },
  {
    label: "Loop in a changing field",
    text: "A circular loop (r=0.05 m) sits in a field changing at 0.2 T/s. Find the induced EMF.",
    diagram: true,
    goldenId: "EM-008",
  },
  {
    label: "Symbols",
    text: "Two masses m1 and m2 hang from a frictionless pulley. Find the acceleration and tension.",
    diagram: false,
  },
  {
    label: "Out of scope",
    text: "A 0.5 kg mass on a spring with damping constant 1.2 kg/s. Find the damped frequency.",
    diagram: false,
  },
];

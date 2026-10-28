import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Visualization } from "./Visualization.tsx";
import {
  CIRCUIT_RES,
  CIRCULAR_RES,
  COLLISION_RES,
  DISK_RES,
  INCLINE_RES,
  KINEMATICS_RES,
  ORBIT_RES,
  RC_RES,
  SPHERE_RES,
  SPRING_RES,
  LOOP_RES,
  WIRE_RES,
} from "./fixtures.ts";

describe("RC charging curve", () => {
  it("is chosen for the RC card and states the engine's numbers", () => {
    render(<Visualization data={RC_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/rises toward V0 = 9 V/);
    expect(img).toHaveAccessibleName(/τ = 0\.2 s, it is 5\.6891 V/);
    expect(screen.getByTestId("rc-curve")).toBeInTheDocument();
    expect(screen.getByTestId("rc-point")).toBeInTheDocument();
  });
});

describe("collision diagram", () => {
  it("is chosen for the collision card and states the engine's numbers", () => {
    render(<Visualization data={COLLISION_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/3 kg cart moving at 4 m\/s hits a 5 kg cart/);
    expect(img).toHaveAccessibleName(/move at 1\.5 m\/s/);
    expect(img).toHaveAccessibleName(/from 24 J to 9 J, so 15 J is lost/);
  });

  it("draws the after arrow shorter than the before arrow, to scale", () => {
    render(<Visualization data={COLLISION_RES} />);
    const len = (id: string) => {
      const el = screen.getByTestId(id);
      return Number(el.getAttribute("x2")) - Number(el.getAttribute("x1"));
    };
    expect(len("v-after") / len("v-before")).toBeCloseTo(1.5 / 4, 6);
  });
});

describe("circular path diagram", () => {
  it("is chosen for the circular-motion card and states the engine's numbers", () => {
    render(<Visualization data={CIRCULAR_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/radius r = 0\.041759 m/);
    expect(img).toHaveAccessibleName(/T = 1\.3119e-7 s/);
    expect(img).toHaveAccessibleName(/direction of travel is not shown/);
  });
});

describe("incline diagram", () => {
  it("is chosen for the incline card and states the engine's numbers", () => {
    render(<Visualization data={INCLINE_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/30° slope with friction coefficient 0\.2/);
    expect(img).toHaveAccessibleName(/3\.2026 m\/s² and reaches 5\.0617 m\/s after 4 m/);
  });

  it("draws weight, normal force and friction", () => {
    render(<Visualization data={INCLINE_RES} />);
    for (const id of ["force-mg", "force-N", "force-f", "accel"]) {
      expect(screen.getByTestId(id)).toBeInTheDocument();
    }
  });

  it("draws no friction arrow on a frictionless slope", () => {
    const a = 9.8 * 0.5;
    render(
      <Visualization
        data={{
          ...INCLINE_RES,
          knowns: { ...INCLINE_RES.knowns, mu: 0 },
          answer: { a, v: Math.sqrt(8 * a) },
        }}
      />,
    );
    expect(screen.queryByTestId("force-f")).toBeNull();
    expect(screen.getByRole("img")).toHaveAccessibleName(/no friction/);
  });
});

describe("circuit diagram", () => {
  it("is chosen for the circuit card and states the engine's numbers", () => {
    render(<Visualization data={CIRCUIT_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/R1 = 4 Ω and R2 = 6 Ω in series/);
    expect(img).toHaveAccessibleName(/parallel with R3 = 12 Ω, across a 12 V source/);
    expect(img).toHaveAccessibleName(
      /2\.2 A splits into 1\.2 A through R1 and R2, and 1 A through R3/,
    );
    for (const id of ["i-total", "i-branch1", "i-branch2"]) {
      expect(screen.getByTestId(id)).toBeInTheDocument();
    }
  });
});

describe("speed-time graph", () => {
  it("is chosen for the 1D kinematics card and states the engine's numbers", () => {
    render(<Visualization data={KINEMATICS_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/from 0 m\/s to 30 m\/s over 12 s/);
    expect(img).toHaveAccessibleName(/distance travelled, 180 m/);
    expect(screen.getByTestId("distance-area")).toBeInTheDocument();
  });
});

describe("charged sphere graph", () => {
  it("is chosen for the Gauss sphere card and states the engine's numbers", () => {
    render(<Visualization data={SPHERE_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/radius 0\.1 m/);
    expect(img).toHaveAccessibleName(/r = 0\.05 m \(inside\) E = 1797500 N\/C/);
    expect(img).toHaveAccessibleName(/r = 0\.3 m \(outside\) E = 399450 N\/C/);
    expect(screen.getByTestId("point-in")).toBeInTheDocument();
    expect(screen.getByTestId("point-out")).toBeInTheDocument();
  });
});

describe("spring diagram", () => {
  it("is chosen for the spring card and states the engine's numbers", () => {
    render(<Visualization data={SPRING_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/2 kg block pushes a spring with k = 500 N\/m in by 0\.15 m/);
    expect(img).toHaveAccessibleName(/moves off at 2\.3717 m\/s/);
    expect(screen.getByTestId("v-arrow")).toBeInTheDocument();
  });
});

describe("orbit diagram", () => {
  it("is chosen for the orbit card and states the engine's numbers", () => {
    render(<Visualization data={ORBIT_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/altitude h = 500000 m above a body of radius 6371000 m/);
    expect(img).toHaveAccessibleName(/orbit radius is r = 6871000 m/);
  });
});

describe("wire diagram", () => {
  it("is chosen for the wire card, states the engine's numbers, and shows no directions", () => {
    render(<Visualization data={WIRE_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/length 0\.3 m carrying 5 A, at 90° to a 0\.8 T/);
    expect(img).toHaveAccessibleName(/force on it is 1\.2 N/);
    expect(img).toHaveAccessibleName(/Directions are not shown/);
    expect(screen.getByTestId("right-angle")).toBeInTheDocument();
    expect(img.querySelector("marker")).toBeNull();
  });
});

describe("disk diagram", () => {
  it("is chosen for the torque card and states the engine's numbers", () => {
    render(<Visualization data={DISK_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(
      /mass 2 kg and radius 0\.25 m, with a constant torque of 0\.6 N·m/,
    );
    expect(img).toHaveAccessibleName(/inertia 0\.0625 kg·m², angular acceleration 9\.6 rad\/s²/);
    expect(img).toHaveAccessibleName(/grows steadily to 48 rad\/s after 5 s/);
  });
});

describe("loop diagram", () => {
  it("is chosen for the Faraday card, states the engine's numbers, and shows no directions", () => {
    render(<Visualization data={LOOP_RES} />);
    const img = screen.getByRole("img");
    expect(img).toHaveAccessibleName(/radius 0\.05 m, area 0\.007854 m²/);
    expect(img).toHaveAccessibleName(/changing at 0\.2 T\/s/);
    expect(img).toHaveAccessibleName(/EMF around the loop is 0\.0015708 V/);
    expect(img.querySelector("marker")).toBeNull();
  });
});

describe("Visualization", () => {
  it("draws nothing for a card with no diagram", () => {
    const { container } = render(
      <Visualization
        data={{ ...RC_RES, card_id: "EM-ELEC-COULOMB", knowns: {}, answer: { F: 3.37 } }}
      />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});

"""Animated GIF generation showing a compression spring's coils closing up
under progressive load (frame-by-frame 3D helix, driven by
simulate_progressive_compression's per-step geometry).
"""
import numpy as np
from pint import Quantity
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from ..pymodels.units import ureg
from .generic_lineal import VariableLinealSpring


class CompressionAnimator:
    """Renders a spring's progressive compression as an animated GIF.

    Usage::

        animator = CompressionAnimator(spring)
        animator.create_gif(max_deflection=40 * ureg.mm, output_path="compression.gif")
    """

    def __init__(self, spring: VariableLinealSpring):
        self.spring = spring

    def create_gif(self, max_deflection: Quantity, output_path: str = "compression.gif",
                    steps: int = 60, num_points: int = 300, fps: int = 12,
                    isometric: bool = True) -> str:
        """Simulate progressive compression and render it as an animated GIF.

        Returns output_path.
        """
        deflection, force, _, geometry = self.spring.simulate_progressive_compression(
            max_deflection=max_deflection, steps=steps, num_points=num_points, capture_geometry=True,
        )
        thetas = geometry["thetas"]
        z_history = geometry["z_history"]

        Ds = np.array([self.spring.f_mean_diameter(z * ureg.mm).to('mm').magnitude for z in z_history[0]])
        radii = Ds / 2.0
        xs = radii * np.cos(thetas)
        ys = radii * np.sin(thetas)

        deflection_mm = deflection.to('mm').magnitude
        force_n = force.to('N').magnitude

        fig = plt.figure()
        ax = fig.add_subplot(projection='3d')
        line, = ax.plot(xs, ys, z_history[0])

        ax.set_xlabel('X (mm)')
        ax.set_ylabel('Y (mm)')
        ax.set_zlabel('Z (mm)')
        # Fix the axis limits up front (from the free-state extent) so the
        # camera/scale doesn't jump around as the coils close up frame to frame.
        margin = max(np.ptp(xs), np.ptp(ys)) * 0.1
        ax.set_xlim(xs.min() - margin, xs.max() + margin)
        ax.set_ylim(ys.min() - margin, ys.max() + margin)
        ax.set_zlim(0, z_history[0].max())
        ax.set_box_aspect((np.ptp(xs), np.ptp(ys), z_history[0].max()))
        if isometric:
            ax.set_proj_type('ortho')
            ax.view_init(elev=35.264, azim=45)

        def update(frame_idx):
            z = z_history[frame_idx]
            line.set_data(xs, ys)
            line.set_3d_properties(z)
            ax.set_title(f"Deflection: {deflection_mm[frame_idx]:.1f} mm   Force: {force_n[frame_idx]:.1f} N")
            return (line,)

        anim = FuncAnimation(fig, update, frames=len(z_history), interval=1000 / fps)
        anim.save(output_path, writer=PillowWriter(fps=fps))
        plt.close(fig)

        return output_path

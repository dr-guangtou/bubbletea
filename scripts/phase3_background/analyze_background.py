"""Analyze background density results from Phase III.

Maps the density of UCD-mimic sources against galactic latitude,
fits a parametric model, and evaluates the scatter to define
search region criteria.
"""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scripts.config import BACKGROUND_RESULTS_DIR, FIGURES_DIR
from scripts.utils.plotting import set_style, save_figure

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Command for metadata
COMMAND = "PYTHONPATH=. uv run python scripts/phase3_background/analyze_background.py"

def exponential_model(b, a, b0, c):
    """Exponential decay model for density vs latitude."""
    return a * np.exp(-np.abs(b) / b0) + c

def analyze_density():
    """Load, plot, and model the background density."""
    results_path = BACKGROUND_RESULTS_DIR / "background_density_results_500.csv"
    if not results_path.exists():
        logger.error(f"Results file not found: {results_path}")
        return

    df = pd.read_csv(results_path)
    df = df[df['status'] == 'success'].copy()

    # Absolute galactic latitude
    df['abs_b'] = df['glat'].abs()

    # Sort for plotting
    df = df.sort_values('abs_b')

    # 1. Fit Model
    # Initial guess: a=3000, b0=20, c=100
    try:
        popt, pcov = curve_fit(exponential_model, df['abs_b'], df['density'], p0=[3000, 20, 100])
        logger.info(f"Fitted model: Density = {popt[0]:.1f} * exp(-|b|/{popt[1]:.1f}) + {popt[2]:.1f}")
    except Exception as e:
        logger.error(f"Fitting failed: {e}")
        popt = None

    # 2. Generate Figure
    set_style()
    fig, ax = plt.subplots(figsize=(10, 7))

    ax.scatter(df['abs_b'], df['density'], alpha=0.4, s=20, label='Random Fields (2 sq deg)')

    if popt is not None:
        b_range = np.linspace(df['abs_b'].min(), df['abs_b'].max(), 100)
        ax.plot(b_range, exponential_model(b_range, *popt), 'r-', lw=2, label='Exponential Fit')

        # Calculate residuals and scatter
        df['model_val'] = exponential_model(df['abs_b'], *popt)
        df['residual'] = df['density'] - df['model_val']
        std_resid = df['residual'].std()

        # Add 1-sigma band
        ax.fill_between(b_range,
                        exponential_model(b_range, *popt) - std_resid,
                        exponential_model(b_range, *popt) + std_resid,
                        color='r', alpha=0.1, label='1$\sigma$ Scatter')

    ax.set_yscale('log')
    ax.set_xlabel('|Galactic Latitude| (deg)')
    ax.set_ylabel('Background Density (sources / deg$^2$)')
    ax.set_title('UCD-Mimic Background Density vs Galactic Latitude')
    ax.grid(True, which="both", ls="-", alpha=0.2)
    ax.legend()

    # Add info text
    if popt is not None:
        text = f"Model: $A e^{{-|b|/b_0}} + C$\n$b_0 = {popt[1]:.1f}^\\circ$\nRMS Scatter = {std_resid:.1f}"
        ax.text(0.65, 0.7, text, transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.8))

    save_figure(
        fig, "background_density_vs_lat", phase=3,
        script_path="scripts/phase3_background/analyze_background.py",
        command=COMMAND,
        data_source="Gaia DR3 (500 random fields)",
        description="Background density of sources passing Model C selection as a function of "
                    "absolute galactic latitude. The exponential trend highlights the heavy "
                    "contamination near the galactic plane (|b| < 30 deg)."
    )
    plt.close(fig)

    # 3. Analyze Scatter and define criteria
    logger.info("\n[Analysis] Stastistics by Latitude Bin:")
    bins = [20, 30, 40, 50, 60, 90]
    df['b_bin'] = pd.cut(df['abs_b'], bins=bins)
    bin_stats = df.groupby('b_bin')['density'].agg(['mean', 'std', 'count'])
    logger.info("\n" + bin_stats.to_string())

    # Conclusion
    median_density = df['density'].median()
    low_lat_mean = df[df['abs_b'] < 30]['density'].mean()
    high_lat_mean = df[df['abs_b'] > 60]['density'].mean()

    logger.info(f"\nMedian Background Density: {median_density:.1f} / deg^2")
    logger.info(f"Contrast (|b|<30 vs |b|>60): {low_lat_mean/high_lat_mean:.1f}x")

    if low_lat_mean > 1000:
        logger.warning("Very high background detected at low latitudes. Stricter |b| cut recommended for pilot.")

if __name__ == "__main__":
    analyze_density()

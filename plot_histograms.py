import json
import glob
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_results():
    """Load all result files from the results directory."""
    result_files = glob.glob("results/results_*.json")
    results = []
    
    for file in result_files:
        with open(file, 'r') as f:
            data = json.load(f)
            results.append(data)
    
    return results

def _infer_range_from_result(result):
    """Best-effort attempt count range for a result."""
    if 'number_range' in result and isinstance(result['number_range'], int):
        return result['number_range']
    # Fallbacks
    if 'attempt_counts' in result:
        ac = result['attempt_counts']
        if isinstance(ac, list):
            return len(ac)
        if isinstance(ac, dict):
            # keys might be strings
            try:
                return max(int(k) for k in ac.keys())
            except Exception:
                return len(ac)
    if 'cumulative_percentage' in result:
        return len(result['cumulative_percentage'])
    return 0

def _attempt_percentages_for_result(result, max_range):
    """
    Return a length=max_range list of per-attempt success percentages for a single result.
    Prefers attempt_counts; falls back to diffs of cumulative_percentage.
    """
    num_games = float(result.get('num_games', 1)) or 1.0
    local_range = _infer_range_from_result(result)
    per_attempt_pct = np.zeros(max_range, dtype=float)

    if 'attempt_counts' in result and result['attempt_counts'] is not None:
        ac = result['attempt_counts']
        counts = np.zeros(local_range, dtype=float)
        if isinstance(ac, list):
            # Trim or pad to local_range
            for i in range(min(len(ac), local_range)):
                counts[i] = ac[i]
        elif isinstance(ac, dict):
            # Keys could be "1", 1, etc., and attempts are 1-indexed
            for k, v in ac.items():
                try:
                    idx = int(k) - 1
                    if 0 <= idx < local_range:
                        counts[idx] = float(v)
                except Exception:
                    continue
        # Convert to % of games
        with np.errstate(divide='ignore', invalid='ignore'):
            pct = (counts / num_games) * 100.0
        # Place into the max_range-length vector
        per_attempt_pct[:min(local_range, max_range)] = pct[:min(local_range, max_range)]
        return per_attempt_pct

    # Fallback: use diffs of cumulative percentages
    cum = result.get('cumulative_percentage', [])
    if not cum:
        return per_attempt_pct  # all zeros
    # Ensure numeric
    cum = [float(x) for x in cum[:local_range]]
    diffs = []
    for i, val in enumerate(cum):
        if i == 0:
            diffs.append(max(0.0, val))
        else:
            diffs.append(max(0.0, val - cum[i - 1]))
    diffs = np.array(diffs, dtype=float)
    per_attempt_pct[:min(local_range, max_range)] = diffs[:min(local_range, max_range)]
    return per_attempt_pct

def create_histogram_plot(results):
    """Create a grouped bar chart (histogram) of per-attempt success percentages."""
    fig, ax = plt.subplots(figsize=(12, 8))

    if not results:
        return fig

    # Determine the common x-axis based on the maximum range among results
    max_range = max(_infer_range_from_result(r) for r in results)
    attempts = np.arange(1, max_range + 1)

    # Colors
    colors = plt.cm.Set1(np.linspace(0, 1, max(2, len(results))))

    # Bar layout
    k = len(results)  # number of models
    total_group_width = 0.85
    bar_width = total_group_width / max(1, k)
    offsets = (np.arange(k) - (k - 1) / 2.0) * bar_width

    # Plot each model's bars side-by-side
    for i, result in enumerate(results):
        model = result.get('model', f'Model {i+1}')
        num_games = result.get('num_games', 0)

        per_attempt_pct = _attempt_percentages_for_result(result, max_range)
        ax.bar(
            attempts + offsets[i],
            per_attempt_pct,
            width=bar_width,
            label=f'{model} (n={num_games})',
            align='center',
            edgecolor='black',
            linewidth=0.5,
            color=colors[i % len(colors)],
        )

    # Aesthetics
    ax.set_xlabel('Attempt Number', fontsize=12)
    ax.set_ylabel('Success Percentage per Attempt (%)', fontsize=12)
    ax.set_title('Per-Attempt Success Distribution (Grouped Histogram)', fontsize=14, fontweight='bold')
    ax.set_xticks(attempts)
    ax.set_xlim(0.5, max_range + 0.5)
    ax.set_ylim(0, 100)
    ax.grid(True, axis='y', alpha=0.3)
    ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left')

    plt.tight_layout()
    return fig

def print_summary(results):
    """Print a summary of all loaded results."""
    print("Summary of Results:")
    print("=" * 50)
    
    for result in results:
        print(f"Model: {result.get('model')}")
        print(f"Games: {result.get('num_games')}")
        rng = _infer_range_from_result(result)
        # Prefer explicit number_range if present
        explicit_rng = result.get('number_range', rng)
        print(f"Range: 1-{explicit_rng}")
        print(f"Timestamp: {result.get('timestamp')}")
        print(f"Attempt distribution: {result.get('attempt_counts')}")
        final_cum = (result.get('cumulative_percentage') or [0])[-1]
        try:
            print(f"Final success rate: {float(final_cum):.1f}%")
        except Exception:
            print(f"Final success rate: {final_cum}")
        print("-" * 30)

def main():
    """Main function to load results and create plots."""
    results = load_results()
    
    if not results:
        print("No result files found. Make sure to run baseline.py first.")
        return
    
    print(f"Found {len(results)} result file(s)")
    print_summary(results)
    
    # Create and show the grouped histogram
    fig = create_histogram_plot(results)
    plt.show()
    
    # Optionally save the plot
    save_plot = input("Save plot to file? (y/n): ").lower() == 'y'
    if save_plot:
        filename = "attempt_histogram.png"
        fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Plot saved as {filename}")

if __name__ == "__main__":
    main()
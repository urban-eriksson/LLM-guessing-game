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

def create_staircase_plot(results):
    """Create a staircase plot of cumulative success rates."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = plt.cm.Set1(np.linspace(0, 1, len(results)))
    
    for i, result in enumerate(results):
        model = result['model']
        cumulative_percentage = result['cumulative_percentage']
        number_range = result['number_range']
        
        # Create staircase effect
        x_vals = []
        y_vals = []
        
        for j, percentage in enumerate(cumulative_percentage):
            # Add horizontal line segment
            if j == 0:
                x_vals.extend([j + 0.5, j + 1.5])
            else:
                x_vals.extend([j + 0.5, j + 1.5])
            y_vals.extend([percentage, percentage])
            
            # Add vertical line segment (except for the last point)
            if j < len(cumulative_percentage) - 1:
                x_vals.append(j + 1.5)
                y_vals.append(cumulative_percentage[j + 1])
        
        # Plot the staircase
        ax.plot(x_vals, y_vals, color=colors[i], linewidth=3, 
               label=f'{model} (n={result["num_games"]})')
        
        # Add markers at the step corners
        for j, percentage in enumerate(cumulative_percentage):
            ax.plot(j + 1, percentage, 'o', color=colors[i], markersize=8)
    
    # Customize the plot
    ax.set_xlabel('Attempt Number', fontsize=12)
    ax.set_ylabel('Cumulative Success Percentage (%)', fontsize=12)
    ax.set_title('Cumulative Success Rate in Number Guessing Game', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 105)
    
    # Set x-axis ticks
    max_range = max(result['number_range'] for result in results)
    ax.set_xlim(0.5, max_range + 0.5)
    ax.set_xticks(range(1, max_range + 1))
    
    # Add legend
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add theoretical perfect line for comparison
    if results:
        number_range = results[0]['number_range']  # Assume same range for all
        theoretical_x = list(range(1, number_range + 1))
        theoretical_y = [(i / number_range) * 100 for i in range(1, number_range + 1)]
        
        # Create theoretical staircase
        theo_x_vals = []
        theo_y_vals = []
        for j, percentage in enumerate(theoretical_y):
            theo_x_vals.extend([j + 0.5, j + 1.5])
            theo_y_vals.extend([percentage, percentage])
            if j < len(theoretical_y) - 1:
                theo_x_vals.append(j + 1.5)
                theo_y_vals.append(theoretical_y[j + 1])
        
        ax.plot(theo_x_vals, theo_y_vals, '--', color='gray', linewidth=2, 
               alpha=0.7, label='Theoretical Perfect')
    
    plt.tight_layout()
    return fig

def print_summary(results):
    """Print a summary of all loaded results."""
    print("Summary of Results:")
    print("=" * 50)
    
    for result in results:
        print(f"Model: {result['model']}")
        print(f"Games: {result['num_games']}")
        print(f"Range: 1-{result['number_range']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Attempt distribution: {result['attempt_counts']}")
        print(f"Final success rate: {result['cumulative_percentage'][-1]:.1f}%")
        print("-" * 30)

def main():
    """Main function to load results and create plots."""
    results = load_results()
    
    if not results:
        print("No result files found. Make sure to run baseline.py first.")
        return
    
    print(f"Found {len(results)} result file(s)")
    print_summary(results)
    
    # Create and show the plot
    fig = create_staircase_plot(results)
    plt.show()
    
    # Optionally save the plot
    save_plot = input("Save plot to file? (y/n): ").lower() == 'y'
    if save_plot:
        filename = "cumulative_success_staircase.png"
        fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Plot saved as {filename}")

if __name__ == "__main__":
    main()
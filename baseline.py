import os
import openai
import random
import json
from datetime import datetime

# Retrieve the OpenAI API key from the environment variable.
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    raise ValueError("The OPENAI_API_KEY environment variable is not set.")

client = openai.OpenAI()

def call_openai_api(conversation):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=conversation
        )
        assistant_message = response.choices[0].message.content
        return assistant_message
    except Exception as e:
        print(f"Error calling OpenAI: {e}")


# Configuration
NUMBER_RANGE = 5  # Numbers from 1 to this value
NUM_GAMES = 10
MODEL_NAME = "gpt-5-mini"

# Track attempts per game (index 0 = 1st attempt, index 1 = 2nd attempt, etc.)
attempt_counts = [0] * NUMBER_RANGE

def play_single_game():
    """Play one complete guessing game and return the number of attempts needed."""
    conversation = [
        {"role": "user", "content": f"Let's play a game! You think of a number from 1 to {NUMBER_RANGE}. Do not include the number in the output. I will then make guesses containing only a number. After each guess, please respond with the exact string 'correct' if I guessed right or the exact string 'not correct' if I guessed wrong."}
    ]
    
    # Get the model to think of a number
    gamesetup_response = call_openai_api(conversation)
    conversation.append({"role": "assistant", "content": gamesetup_response})
    print(gamesetup_response)
    
    # Create a random permutation of numbers 1 to NUMBER_RANGE
    guess_sequence = list(range(1, NUMBER_RANGE + 1))
    random.shuffle(guess_sequence)
    
    attempts = 0
    while attempts < len(guess_sequence):
        guess = guess_sequence[attempts]
        attempts += 1
        conversation.append({"role": "user", "content": str(guess)})
        
        response = call_openai_api(conversation)
        conversation.append({"role": "assistant", "content": response})
        
        print(f"Attempt {attempts}: Guess {guess} -> {response}")
        
        # Check if correct
        while not response.lower() in ['correct', 'not correct']:
            correction = "Please answer with the exact string 'correct' if I guessed right or the exact string 'not correct' if I guessed wrong"
            print(correction)
            conversation.append({"role": "user", "content": correction})
            response = call_openai_api(conversation)
            conversation.append({"role": "assistant", "content": response})

        if 'correct' in response.lower() and 'not correct' not in response.lower():
            return attempts
    
    # If we've tried all numbers and none were correct, something went wrong
    print("All numbers tried, no correct answer found")
    return None

# Run the experiment
for game in range(1, NUM_GAMES + 1):
    print(f"Game {game}\n{'='*40}")
    attempts_needed = play_single_game()
    
    # Record the result (subtract 1 for 0-based indexing)
    if attempts_needed is not None:
        attempt_counts[attempts_needed - 1] += 1
    
    print(f"Game completed in {attempts_needed} attempts\n")

# Calculate results
cumulative_percentage = []
cumulative_sum = 0

for i, count in enumerate(attempt_counts):
    cumulative_sum += count
    percentage = (cumulative_sum / NUM_GAMES) * 100
    cumulative_percentage.append(percentage)
    print(f"Attempt {i+1}: {count} games ({count / NUM_GAMES * 100:.1f}%), Cumulative: {percentage:.1f}%")

# Save results to file
import os
os.makedirs("results", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"results/results_{MODEL_NAME.replace('-', '_')}_{timestamp}.json"

results = {
    "model": MODEL_NAME,
    "timestamp": timestamp,
    "number_range": NUMBER_RANGE,
    "num_games": NUM_GAMES,
    "attempt_counts": attempt_counts,
    "cumulative_percentage": cumulative_percentage
}

with open(filename, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nTotal games played: {NUM_GAMES}")
print(f"Results by attempt: {attempt_counts}")
print(f"Results saved to: {filename}")
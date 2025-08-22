import os
import random
import json
from datetime import datetime

# Configuration
API_PROVIDER = "anthropic"  # Change to "openai" or "anthropic"
NUMBER_RANGE = 5  # Numbers from 1 to this value
NUM_GAMES = 10

# Model configuration based on provider
if API_PROVIDER == "openai":
    import openai
    MODEL_NAME = "gpt-4o-mini"  # or "gpt-4", "gpt-3.5-turbo", etc.
    
    # Retrieve the OpenAI API key from the environment variable
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        raise ValueError("The OPENAI_API_KEY environment variable is not set.")
    
    client = openai.OpenAI()
    
elif API_PROVIDER == "anthropic":
    import anthropic
    MODEL_NAME = "claude-3-5-sonnet-20241022"  # or "claude-3-opus-20240229", "claude-3-haiku-20240307"
    
    # Retrieve the Anthropic API key from the environment variable
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("The ANTHROPIC_API_KEY environment variable is not set.")
    
    client = anthropic.Anthropic(api_key=api_key)
    
else:
    raise ValueError(f"Unknown API provider: {API_PROVIDER}")

# Track attempts per game
attempt_counts = [0] * NUMBER_RANGE

def call_api(conversation):
    """Call the appropriate API based on the configured provider."""
    try:
        if API_PROVIDER == "openai":
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=conversation
            )
            return response.choices[0].message.content
            
        elif API_PROVIDER == "anthropic":
            # Convert OpenAI format to Anthropic format
            # Extract system message if present
            system_message = None
            messages = []
            
            for msg in conversation:
                if msg["role"] == "system":
                    system_message = msg["content"]
                elif msg["role"] == "user":
                    messages.append({"role": "user", "content": msg["content"]})
                elif msg["role"] == "assistant":
                    messages.append({"role": "assistant", "content": msg["content"]})
            
            # Call Anthropic API
            kwargs = {
                "model": MODEL_NAME,
                "messages": messages,
                "max_tokens": 1000
            }
            if system_message:
                kwargs["system"] = system_message
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
            
    except Exception as e:
        print(f"Error calling {API_PROVIDER} API: {e}")
        raise

def play_single_game():
    """Play one complete guessing game and return the number of attempts needed."""
    conversation = [
        {"role": "user", "content": f"Let's play a game! You think of a number from 1 to {NUMBER_RANGE}. Do not include the number in the output. I will then make guesses containing only a number. After each guess, please respond with the exact string 'correct' if I guessed right or the exact string 'not correct' if I guessed wrong."}
    ]
    
    # Get the model to think of a number
    gamesetup_response = call_api(conversation)
    conversation.append({"role": "assistant", "content": gamesetup_response})
    print(f"Model response: {gamesetup_response}")
    
    # Create a random permutation of numbers 1 to NUMBER_RANGE
    guess_sequence = list(range(1, NUMBER_RANGE + 1))
    random.shuffle(guess_sequence)
    
    attempts = 0
    while attempts < len(guess_sequence):
        guess = guess_sequence[attempts]
        attempts += 1
        conversation.append({"role": "user", "content": str(guess)})
        
        response = call_api(conversation)
        conversation.append({"role": "assistant", "content": response})
        
        print(f"Attempt {attempts}: Guess {guess} -> {response}")
        
        # Check if the response is valid
        response_lower = response.lower().strip()
        while response_lower not in ['correct', 'not correct']:
            correction = "Please answer with the exact string 'correct' if I guessed right or the exact string 'not correct' if I guessed wrong"
            print(f"Correction needed: {correction}")
            conversation.append({"role": "user", "content": correction})
            response = call_api(conversation)
            conversation.append({"role": "assistant", "content": response})
            response_lower = response.lower().strip()
            print(f"Corrected response: {response}")
        
        if response_lower == 'correct':
            return attempts
    
    # If we've tried all numbers and none were correct, something went wrong
    print("Warning: All numbers tried, no correct answer found")
    return None

# Main execution
print(f"Starting experiment with {API_PROVIDER} API using model {MODEL_NAME}")
print(f"Playing {NUM_GAMES} games with numbers from 1 to {NUMBER_RANGE}\n")

for game in range(1, NUM_GAMES + 1):
    print(f"\nGame {game}")
    print("=" * 40)
    attempts_needed = play_single_game()
    
    # Record the result (subtract 1 for 0-based indexing)
    if attempts_needed is not None:
        attempt_counts[attempts_needed - 1] += 1
        print(f"✓ Game completed in {attempts_needed} attempts")
    else:
        print(f"✗ Game failed to complete properly")
    
    print()

# Calculate and display results
print("\n" + "=" * 50)
print("RESULTS SUMMARY")
print("=" * 50)

cumulative_percentage = []
cumulative_sum = 0

for i, count in enumerate(attempt_counts):
    cumulative_sum += count
    percentage = (count / NUM_GAMES) * 100
    cumulative_percentage_value = (cumulative_sum / NUM_GAMES) * 100
    cumulative_percentage.append(cumulative_percentage_value)
    print(f"Attempt {i+1}: {count} games ({percentage:.1f}%), Cumulative: {cumulative_percentage_value:.1f}%")

# Save results to file
os.makedirs("results", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_model_name = MODEL_NAME.replace("-", "_").replace(".", "_")
filename = f"results/results_{API_PROVIDER}_{safe_model_name}_{timestamp}.json"

results = {
    "api_provider": API_PROVIDER,
    "model": MODEL_NAME,
    "timestamp": timestamp,
    "number_range": NUMBER_RANGE,
    "num_games": NUM_GAMES,
    "attempt_counts": attempt_counts,
    "cumulative_percentage": cumulative_percentage,
    "games_completed": sum(attempt_counts),
    "games_failed": NUM_GAMES - sum(attempt_counts)
}

with open(filename, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nTotal games played: {NUM_GAMES}")
print(f"Games completed successfully: {sum(attempt_counts)}")
print(f"Results by attempt: {attempt_counts}")
print(f"Results saved to: {filename}")
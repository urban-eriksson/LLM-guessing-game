import os
import random
import json
from datetime import datetime

# Configuration
API_PROVIDER = "anthropic"  # Change to "openai", "anthropic", "google", or "control"
NUMBER_RANGE = 10  # Numbers from 1 to this value
NUM_GAMES = 100

# Model configuration based on provider
if API_PROVIDER == "openai":
    import openai
    MODEL_NAME = "gpt-5-mini"  # or "gpt-4", "gpt-3.5-turbo", etc.
    
    # Retrieve the OpenAI API key from the environment variable
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    if not openai.api_key:
        raise ValueError("The OPENAI_API_KEY environment variable is not set.")
    
    client = openai.OpenAI()
    
elif API_PROVIDER == "anthropic":
    import anthropic
    MODEL_NAME = "claude-sonnet-4-20250514"  # or "claude-3-opus-20240229", "claude-3-haiku-20240307"
    
    # Retrieve the Anthropic API key from the environment variable
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("The ANTHROPIC_API_KEY environment variable is not set.")
    
    client = anthropic.Anthropic(api_key=api_key)

elif API_PROVIDER == "google":
    import google.generativeai as genai
    MODEL_NAME = "gemini-2.5-flash"  # or "gemini-1.5-pro", etc.
    
    # Retrieve the Google AI Studio API key from the environment variable
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("The GOOGLE_API_KEY environment variable is not set.")
    
    genai.configure(api_key=api_key)
    client = genai.GenerativeModel(MODEL_NAME)

elif API_PROVIDER == 'control':
    MODEL_NAME = "control"

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

        elif API_PROVIDER == "google":
            # For Gemini, the conversation history is managed differently.
            # We will send the entire conversation history in each call.
            # The role for the model is 'model', not 'assistant'.
            gemini_conversation = []
            for msg in conversation:
                role = "model" if msg["role"] == "assistant" else "user"
                gemini_conversation.append({"role": role, "parts": [msg["content"]]})
            
            # The last message should be from the user, so we pop it from the history
            # and use it as the prompt for the generate_content call.
            # The history parameter takes the rest of the conversation.
            *history, current_prompt = gemini_conversation
            chat_session = client.start_chat(history=history)
            response = chat_session.send_message(current_prompt["parts"])
            return response.text

        elif API_PROVIDER == "control":
            global CONTROL_NUMBER

            # Find the most recent user message
            last_user = None
            for msg in reversed(conversation):
                if msg["role"] == "user":
                    last_user = msg["content"].strip()
                    break

            if last_user is None:
                # Defensive: always return a valid string
                return "not correct"

            # Game setup message: pick a fresh secret number for this game
            if "Let's play a game!" in last_user:
                CONTROL_NUMBER = random.randint(1, NUMBER_RANGE)
                # Exactly this capitalization + period, per your prompt
                return "Okay, I have a number."

            # Guess handling
            try:
                guess = int(last_user)
            except ValueError:
                # If it's not a numeric guess (e.g. correction prompt), keep returning a valid token
                return "not correct"

            return "correct" if guess == CONTROL_NUMBER else "not correct"        
            
    except Exception as e:
        print(f"Error calling {API_PROVIDER} API: {e}")
        raise

def play_single_game():
    """Play one complete guessing game and return the number of attempts needed."""

    conversation = [
    {"role": "user", "content": f"""Let's play a game! You will think of a number from 1 to {NUMBER_RANGE}. I will then try to guess it.

    Your task is to respond to my guesses with one of two exact strings:
    - 'correct'
    - 'not correct'

    You must always reply. Under no circumstances should you give an empty or blank response. Do not add any other words or punctuation.

    First, think of your number. Let me know you are ready by responding with 'Okay, I have a number.'. Do not reveal the number."""}
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
        CONTROL_NUMBER = None  # used only when API_PROVIDER == "control"
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
# LLM-guessing-game

When using LLM:s lately I have come across some weird behavior. It can best be illustrated by running a number guessing game, originally proposed by Jan-Olof Wesström, and for which I have made a script utilizing API calls to gather some statistics for, testing some of the latest models from the big providers. Below is a short description of the game and how it is played:

_The game is about guessing numbers. The AI model is prompted to think of a number between 1 and 10, and asked not to reveal it. The script then makes guesses for the same number range but in a random order, and the model answers with ‘correct’ or ‘not correct’ depending on if the guess is the same as the selected number or not. When the guess is correct the number of  guesses needed to obtain the correct answer is stored and the game is played 100 times to gather statistics._

The purpose of the game is to test if the model has the capability of remembering what number it selected, or by some other method come up with an output which is equivalent to remembering the number. It turns out that it is unable to do so, which is quite clear from the graph of the collected statistics. Ideally the number of guesses needed to get the correct number should be around 10% and independent of the number of guesses needed. However, the statistics are quite skewed, and differ considerably between models. In addition to that, Google Gemini 2.5 flash does not end the game in a correct way in 7 attempts out of 100, because it answers ‘not correct’ for all the 10 numbers. The same happened with Anthropic’s claude-sonnet-4-20250514 in one case out of 100.

<p align="center"> 
<img src="https://github.com/urban-eriksson/LLM-guessing-game/blob/main/images/game_of_10.png">
</p>

The conclusion is that LLM:s do not have an internal memory, which is perhaps not very surprising to people familiar with the transformer model architecture. Still models nowadays are reasoning, and that reasoning is taking place on the server side. So the reasoning could in principle be viewed as an ‘inner monologue’, if that is made unavailable to the user. For that to work however, the model needs to be aware that there are two types of output, one that is internal to the model, and one that is accessible to the user. Another possibility is perhaps to put the ‘inner monologue’ in the model itself, which probably would require some architectural changes, but may have advantages if one could work at embedding level as well as with a tokenized context. 


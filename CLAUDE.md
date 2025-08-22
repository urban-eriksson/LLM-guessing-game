# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a research project that investigates LLM behavior in a simple guessing game scenario. The core experiment involves an LLM thinking of a number, then evaluating human guesses to determine if the LLM exhibits consistent behavior or biases in its responses.

## Architecture

- **Multiple script design**: There will multiple standalone experiments in separate pyhthon files.
- **API integration**: Uses OpenAI's API (specifically o3-mini model) for LLM interactions
- **Conversation flow**: Establishes a two-turn conversation where the LLM picks a number, then responds to a random guess
- **Result tracking**: Simple counters track correct vs incorrect responses across 100 iterations

## Running the Experiment

Experiments will be run using the python debugger from vscode

## Key Implementation Details

- Random number generation for guesses ensures no human bias in the experimental design
- The experiment specifically tests whether LLMs maintain consistency when asked to "think of" a number versus responding to guesses
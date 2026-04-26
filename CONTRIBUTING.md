# Contributing to Autonomous Research Agent

Thank you for your interest in contributing! This document outlines the process for contributing to this project.

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Autonomous-Research-Agent.git
   cd Autonomous-Research-Agent
   ```
3. Create a **virtual environment** and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and fill in your API keys.

## Making Changes

1. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes, following the [code style guidelines](#code-style) below.
3. Commit your changes with a clear, descriptive message:
   ```bash
   git commit -m "feat: add support for custom report templates"
   ```
4. Push your branch and open a **Pull Request** against `main`.

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
- Write clear docstrings for every public function and class.
- Keep functions focused and single-purpose.
- Handle exceptions gracefully and log meaningful error messages.

## Reporting Issues

- Search [existing issues](https://github.com/AjaySinghAdhikari/Autonomous-Research-Agent/issues) before opening a new one.
- Include a clear title, description, and steps to reproduce the problem.
- Attach relevant error logs or screenshots where possible.

## Feature Requests

Open a GitHub Issue with the label `enhancement` and describe:
- The problem you are trying to solve.
- Your proposed solution.
- Any alternatives you have considered.

## Code of Conduct

Please be respectful and constructive in all interactions. We are committed to maintaining a welcoming and inclusive community.

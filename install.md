# Developer Installation Guide

This guide provides instructions for setting up the development environment for the CoffeeCleaner application.

## Prerequisites

- Python 3.10 or later
- Git

## 1. Clone the Repository

First, clone the project repository to your local machine:

```bash
git clone https://github.com/your-username/coffeecleaner.git
cd coffeecleaner
```

## 2. Create and Activate a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## 4. Run the Application

Once the dependencies are installed, you can run the application:

```bash
python main.py
```

or 

```bash
venv/bin/python main.py
```
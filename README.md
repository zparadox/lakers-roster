# LA Lakers Roster Web Application

A modern web application that displays the current Los Angeles Lakers roster, including player information, statistics, and photos.

## Features

- Display of current Lakers roster
- Player information including position and physical stats
- Key performance statistics (PPG, RPG, APG)
- Player photos from NBA API
- Responsive design with Lakers-themed styling
- Modern card-based layout with smooth transitions

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Make sure you're in the project directory and your virtual environment is activated

2. Run the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── static/
│   ├── style.css      # CSS styling
│   └── default-player.png  # Default player image
└── templates/
    └── index.html     # Main HTML template
```

## Technologies Used

- Python Flask
- NBA API
- HTML5
- CSS3
- Google Fonts
- Responsive Design

## Note

The application uses the NBA API to fetch real-time data. Please ensure you have a stable internet connection for the best experience. 
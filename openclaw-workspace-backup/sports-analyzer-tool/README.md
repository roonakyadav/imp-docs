# Sports Analyzer Tool

A comprehensive sports analysis tool for analyzing player performance, team statistics, and game outcomes.

## Features

- **Player Management**: Track individual player statistics, performance metrics, and career progressions
- **Team Analysis**: Monitor team performance, head-to-head records, and seasonal achievements
- **Game Tracking**: Record and analyze game events, scores, and player performances
- **Statistical Analysis**: Advanced metrics including player ratings, efficiency ratios, and performance trends
- **Comparison Tools**: Compare players and teams across different seasons and competitions
- **Data Visualization**: Charts and graphs to visualize performance trends and statistics
- **RESTful API**: Well-structured API endpoints for data management and analysis

## Technologies Used

- **Backend**: Node.js, Express.js
- **Database**: MongoDB with Mongoose ODM
- **Frontend**: HTML, CSS, JavaScript with Bootstrap
- **Visualization**: Chart.js for data visualization
- **API**: RESTful API design
- **Environment**: Dotenv for environment variable management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/roonakyadav/sports-analyzer-tool.git
cd sports-analyzer-tool
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following content:
```
PORT=5000
MONGODB_URI=mongodb://localhost:27017/sports-analyzer
JWT_SECRET=your_jwt_secret_here
```

4. Start the development server:
```bash
npm run dev
```

## API Endpoints

### Player Management
- `GET /api/sports/players` - Get all players
- `GET /api/sports/players/:id` - Get player by ID
- `POST /api/sports/players` - Create new player
- `PUT /api/sports/players/:id` - Update player
- `DELETE /api/sports/players/:id` - Delete player

### Team Management
- `GET /api/sports/teams` - Get all teams
- `GET /api/sports/teams/:id` - Get team by ID
- `POST /api/sports/teams` - Create new team

### Game Management
- `GET /api/sports/games` - Get all games
- `GET /api/sports/games/:id` - Get game by ID
- `POST /api/sports/games` - Create new game

### Statistical Analysis
- `GET /api/analysis/players/:id/stats` - Get player statistics
- `GET /api/analysis/teams/:id/stats` - Get team statistics
- `GET /api/analysis/compare/players/:player1Id/:player2Id` - Compare two players
- `GET /api/analysis/compare/teams/:team1Id/:team2Id` - Compare two teams
- `GET /api/analysis/teams/:id/recent-games` - Get recent games for a team
- `GET /api/analysis/top-performers/:season` - Get top performers in a season

## Database Models

### Player Model
- Name, position, team, age, height, weight
- Nationality and physical attributes
- Seasonal statistics (goals, assists, points, etc.)

### Team Model
- Name, league, founded year, stadium
- Coach and location information
- Seasonal statistics (wins, losses, draws, goals, etc.)

### Game Model
- Home team, away team, date, venue
- Score, attendance, referee
- Player performances and game events
- Weather conditions and match status

## Usage Examples

### Get Player Statistics
```javascript
fetch('/api/analysis/players/playerId/stats')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Compare Two Players
```javascript
fetch('/api/analysis/compare/players/player1Id/player2Id')
  .then(response => response.json())
  .then(data => console.log(data));
```

### Get Top Performers in Season
```javascript
fetch('/api/analysis/top-performers/2023-2024')
  .then(response => response.json())
  .then(data => console.log(data));
```

## Frontend Interface

The application includes a responsive web interface built with Bootstrap that allows users to:
- View dashboard with key statistics
- Manage players and teams
- Access analytical reports
- Visualize data through interactive charts

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Chart.js for data visualization
- Bootstrap for responsive UI components
- MongoDB for flexible data storage
- Express.js for robust server framework
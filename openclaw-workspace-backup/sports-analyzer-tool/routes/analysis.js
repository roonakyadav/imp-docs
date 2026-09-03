const express = require('express');
const router = express.Router();
const Player = require('../models/Player');
const Team = require('../models/Team');
const Game = require('../models/Game');

// Player statistics analysis
router.get('/players/:id/stats', async (req, res) => {
  try {
    const player = await Player.findById(req.params.id);
    if (!player) {
      return res.status(404).json({ message: 'Player not found' });
    }

    // Calculate overall stats
    const totalStats = player.statistics.reduce((acc, stat) => {
      acc.gamesPlayed += stat.gamesPlayed || 0;
      acc.goals += stat.goals || 0;
      acc.assists += stat.assists || 0;
      acc.points += stat.points || 0;
      acc.minutes += stat.minutes || 0;
      acc.shots += stat.shots || 0;
      acc.passes += stat.passes || 0;
      acc.tackles += stat.tackles || 0;
      acc.saves += stat.saves || 0;
      return acc;
    }, {
      gamesPlayed: 0,
      goals: 0,
      assists: 0,
      points: 0,
      minutes: 0,
      shots: 0,
      passes: 0,
      tackles: 0,
      saves: 0
    });

    // Calculate averages
    const avgStats = {};
    for (const [key, value] of Object.entries(totalStats)) {
      avgStats[key] = totalStats.gamesPlayed > 0 ? (value / totalStats.gamesPlayed).toFixed(2) : 0;
    }

    // Goals per game ratio
    const goalsPerGame = totalStats.gamesPlayed > 0 ? (totalStats.goals / totalStats.gamesPlayed).toFixed(2) : 0;

    res.json({
      playerName: player.name,
      position: player.position,
      totalStats,
      averageStats: avgStats,
      goalsPerGame,
      careerStats: player.statistics
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Team statistics analysis
router.get('/teams/:id/stats', async (req, res) => {
  try {
    const team = await Team.findById(req.params.id);
    if (!team) {
      return res.status(404).json({ message: 'Team not found' });
    }

    // Calculate overall stats
    const totalStats = team.statistics.reduce((acc, stat) => {
      acc.wins += stat.wins || 0;
      acc.losses += stat.losses || 0;
      acc.draws += stat.draws || 0;
      acc.goalsFor += stat.goalsFor || 0;
      acc.goalsAgainst += stat.goalsAgainst || 0;
      acc.points += stat.points || 0;
      return acc;
    }, {
      wins: 0,
      losses: 0,
      draws: 0,
      goalsFor: 0,
      goalsAgainst: 0,
      points: 0
    });

    // Win percentage
    const totalGames = totalStats.wins + totalStats.losses + totalStats.draws;
    const winPercentage = totalGames > 0 ? ((totalStats.wins / totalGames) * 100).toFixed(2) : 0;

    // Goal difference
    const goalDifference = totalStats.goalsFor - totalStats.goalsAgainst;

    res.json({
      teamName: team.name,
      league: team.league,
      totalStats,
      winPercentage,
      goalDifference,
      seasonStats: team.statistics
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Compare two players
router.get('/compare/players/:player1Id/:player2Id', async (req, res) => {
  try {
    const [player1, player2] = await Promise.all([
      Player.findById(req.params.player1Id),
      Player.findById(req.params.player2Id)
    ]);

    if (!player1 || !player2) {
      return res.status(404).json({ message: 'One or both players not found' });
    }

    // Calculate stats for both players
    const calculatePlayerStats = (player) => {
      const totalStats = player.statistics.reduce((acc, stat) => {
        acc.gamesPlayed += stat.gamesPlayed || 0;
        acc.goals += stat.goals || 0;
        acc.assists += stat.assists || 0;
        acc.points += stat.points || 0;
        acc.minutes += stat.minutes || 0;
        acc.shots += stat.shots || 0;
        acc.passes += stat.passes || 0;
        acc.tackles += stat.tackles || 0;
        acc.saves += stat.saves || 0;
        return acc;
      }, {
        gamesPlayed: 0,
        goals: 0,
        assists: 0,
        points: 0,
        minutes: 0,
        shots: 0,
        passes: 0,
        tackles: 0,
        saves: 0
      });

      return {
        name: player.name,
        position: player.position,
        totalStats,
        goalsPerGame: totalStats.gamesPlayed > 0 ? (totalStats.goals / totalStats.gamesPlayed).toFixed(2) : 0,
        assistsPerGame: totalStats.gamesPlayed > 0 ? (totalStats.assists / totalStats.gamesPlayed).toFixed(2) : 0
      };
    };

    const stats1 = calculatePlayerStats(player1);
    const stats2 = calculatePlayerStats(player2);

    res.json({
      player1: stats1,
      player2: stats2,
      comparison: {
        betterGoalsPerGame: stats1.goalsPerGame >= stats2.goalsPerGame ? player1.name : player2.name,
        betterAssistsPerGame: stats1.assistsPerGame >= stats2.assistsPerGame ? player1.name : player2.name,
        moreGames: stats1.totalStats.gamesPlayed >= stats2.totalStats.gamesPlayed ? player1.name : player2.name
      }
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Get recent games for a team
router.get('/teams/:id/recent-games', async (req, res) => {
  try {
    const { limit = 5 } = req.query;
    const teamId = req.params.id;

    const recentGames = await Game.find({
      $or: [{ homeTeam: teamId }, { awayTeam: teamId }]
    })
    .sort({ date: -1 })
    .limit(parseInt(limit))
    .populate('homeTeam awayTeam');

    res.json(recentGames);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Get head-to-head record between two teams
router.get('/compare/teams/:team1Id/:team2Id', async (req, res) => {
  try {
    const team1Id = req.params.team1Id;
    const team2Id = req.params.team2Id;

    const games = await Game.find({
      $or: [
        { homeTeam: team1Id, awayTeam: team2Id },
        { homeTeam: team2Id, awayTeam: team1Id }
      ]
    }).populate('homeTeam awayTeam');

    let team1Wins = 0;
    let team2Wins = 0;
    let draws = 0;

    games.forEach(game => {
      if (game.homeTeam._id.toString() === team1Id) {
        if (game.homeScore > game.awayScore) team1Wins++;
        else if (game.awayScore > game.homeScore) team2Wins++;
        else draws++;
      } else {
        if (game.awayScore > game.homeScore) team1Wins++;
        else if (game.homeScore > game.awayScore) team2Wins++;
        else draws++;
      }
    });

    res.json({
      team1: (await Team.findById(team1Id)).name,
      team2: (await Team.findById(team2Id)).name,
      totalMatches: games.length,
      team1Wins,
      team2Wins,
      draws,
      games
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

// Get top performers in a season
router.get('/top-performers/:season', async (req, res) => {
  try {
    // Find players with stats in the given season
    const players = await Player.find({
      'statistics.season': req.params.season
    });

    // Extract stats for the specific season
    const seasonStats = [];
    players.forEach(player => {
      const seasonStat = player.statistics.find(stat => stat.season === req.params.season);
      if (seasonStat) {
        seasonStats.push({
          playerId: player._id,
          playerName: player.name,
          position: player.position,
          team: player.team,
          ...seasonStat
        });
      }
    });

    // Sort by different criteria
    const topGoalscorers = [...seasonStats].sort((a, b) => (b.goals || 0) - (a.goals || 0)).slice(0, 10);
    const topAssisters = [...seasonStats].sort((a, b) => (b.assists || 0) - (a.assists || 0)).slice(0, 10);
    const topPointScorers = [...seasonStats].sort((a, b) => (b.points || 0) - (a.points || 0)).slice(0, 10);
    const topRaters = [...seasonStats].filter(p => p.rating).sort((a, b) => (b.rating || 0) - (a.rating || 0)).slice(0, 10);

    res.json({
      season: req.params.season,
      topGoalscorers,
      topAssisters,
      topPointScorers,
      topRaters
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;
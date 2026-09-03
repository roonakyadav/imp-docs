const mongoose = require('mongoose');

const gameSchema = new mongoose.Schema({
  homeTeam: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Team',
    required: true
  },
  awayTeam: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Team',
    required: true
  },
  date: {
    type: Date,
    required: true
  },
  venue: {
    type: String,
    required: true
  },
  competition: {
    type: String,
    required: true
  },
  season: {
    type: String,
    required: true
  },
  homeScore: {
    type: Number,
    default: 0
  },
  awayScore: {
    type: Number,
    default: 0
  },
  halftimeScore: {
    home: Number,
    away: Number
  },
  attendance: {
    type: Number
  },
  referee: {
    type: String
  },
  weather: {
    temperature: Number,
    conditions: String
  },
  playerPerformances: [{
    player: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Player'
    },
    team: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Team'
    },
    minutesPlayed: Number,
    goals: Number,
    assists: Number,
    yellowCards: Number,
    redCards: Number,
    rating: Number,
    shots: Number,
    passes: Number,
    tackles: Number,
    otherStats: mongoose.Schema.Types.Mixed
  }],
  events: [{
    minute: Number,
    type: String, // 'goal', 'substitution', 'card', 'injury'
    player: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Player'
    },
    description: String
  }],
  status: {
    type: String,
    enum: ['scheduled', 'live', 'finished', 'postponed', 'cancelled'],
    default: 'scheduled'
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
});

gameSchema.pre('save', function(next) {
  this.updatedAt = Date.now;
  next();
});

module.exports = mongoose.model('Game', gameSchema);
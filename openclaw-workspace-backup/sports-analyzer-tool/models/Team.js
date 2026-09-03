const mongoose = require('mongoose');

const teamSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true
  },
  league: {
    type: String,
    required: true
  },
  founded: {
    type: Number,
    required: true
  },
  stadium: {
    type: String,
    required: true
  },
  coach: {
    type: String,
    required: true
  },
  city: {
    type: String,
    required: true
  },
  country: {
    type: String,
    required: true
  },
  statistics: [{
    season: String,
    wins: Number,
    losses: Number,
    draws: Number,
    goalsFor: Number,
    goalsAgainst: Number,
    points: Number,
    rank: Number,
    otherStats: mongoose.Schema.Types.Mixed
  }],
  players: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Player'
  }],
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
});

teamSchema.pre('save', function(next) {
  this.updatedAt = Date.now;
  next();
});

module.exports = mongoose.model('Team', teamSchema);
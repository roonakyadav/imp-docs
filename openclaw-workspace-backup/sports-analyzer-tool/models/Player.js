const mongoose = require('mongoose');

const playerSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    trim: true
  },
  position: {
    type: String,
    required: true
  },
  team: {
    type: String,
    required: true
  },
  age: {
    type: Number,
    required: true
  },
  height: {
    type: Number, // in cm
    required: true
  },
  weight: {
    type: Number, // in kg
    required: true
  },
  nationality: {
    type: String,
    required: true
  },
  statistics: [{
    season: String,
    gamesPlayed: Number,
    goals: Number,
    assists: Number,
    points: Number,
    minutes: Number,
    rating: Number,
    shots: Number,
    passes: Number,
    tackles: Number,
    saves: Number,
    otherStats: mongoose.Schema.Types.Mixed
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

playerSchema.pre('save', function(next) {
  this.updatedAt = Date.now;
  next();
});

module.exports = mongoose.model('Player', playerSchema);
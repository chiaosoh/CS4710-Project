var tileSize = 50;
var xoff = 80;
var yoff = 100;

//human playing vars
var humanPlaying = true;
var left = false;
var right = false;
var up = false;
var down = false;
var player;

//arrays
var tiles = [];
var solids = [];
var dots = [];
var savedDots = [];

var winArea; //a solid which is the win zone i.e. the green bits

var winCounter = 0;

function setup() {
  var canvas = createCanvas(1280, 720);
  canvas.parent("canvas");
  for (var i = 0; i < 22; i++) {
    tiles[i] = [];
    for (var j = 0; j < 10; j++) {
      tiles[i][j] = new Tile(i, j);
    }
  }

  setLevel1Walls();
  setLevel1Goal();
  setLevel1SafeArea();
  setEdges();
  setSolids();

  player = new Player();
  setDots();
  winArea = new Solid(tiles[17][2], tiles[19][7]);

  window.addEventListener(
    "keydown",
    function (e) {
      // space and arrow keys
      if ([32, 37, 38, 39, 40].indexOf(e.keyCode) > -1) {
        e.preventDefault();
      }
    },
    false
  );
}

function draw() {
  background(180, 181, 254);
  drawTiles();
  write();

  if (humanPlaying) {
    //if the user is controlling the square
    if ((player.dead && player.fadeCounter <= 0) || player.reachedGoal) {
      //reset player and dots
      if (player.reachedGoal) {
        winCounter++;
      }
      player = new Player();
      player.human = true;
      resetDots();
    } else {
      //update the dots and the players and show them to the screen
      moveAndShowDots();

      player.update();
      player.show();
    }
  }
}

function moveAndShowDots() {
  for (var i = 0; i < dots.length; i++) {
    dots[i].move();
    dots[i].show();
  }
}

function resetDots() {
  for (var i = 0; i < dots.length; i++) {
    dots[i].resetDot();
  }
}

function drawTiles() {
  for (var i = 0; i < tiles.length; i++) {
    for (var j = 0; j < tiles[0].length; j++) {
      tiles[i][j].show();
    }
  }
  for (var i = 0; i < tiles.length; i++) {
    for (var j = 0; j < tiles[0].length; j++) {
      tiles[i][j].showEdges();
    }
  }
}

function loadDots() {
  for (var i = 0; i < dots.length; i++) {
    dots[i] = savedDots[i].clone();
  }
}

function saveDots() {
  for (var i = 0; i < dots.length; i++) {
    savedDots[i] = dots[i].clone();
  }
}

function write() {
  fill(247, 247, 255);
  textSize(20);
  noStroke();
  textSize(36);
  text(winCounter, 110, 400);
}

function keyPressed() {
  if (humanPlaying) {
    switch (keyCode) {
      case UP_ARROW:
        up = true;
        break;
      case DOWN_ARROW:
        down = true;
        break;
      case RIGHT_ARROW:
        right = true;
        break;
      case LEFT_ARROW:
        left = true;
        break;
    }
    switch (key) {
      case "W":
        up = true;
        break;
      case "S":
        down = true;
        break;
      case "D":
        right = true;
        break;
      case "A":
        left = true;
        break;
    }
    setPlayerVelocity();
  }
  return false;
}

function keyReleased() {
  if (humanPlaying) {
    switch (keyCode) {
      case UP_ARROW:
        up = false;
        break;
      case DOWN_ARROW:
        down = false;
        break;
      case RIGHT_ARROW:
        right = false;
        break;
      case LEFT_ARROW:
        left = false;
        break;
    }
    switch (key) {
      case "W":
        up = false;
        break;
      case "S":
        down = false;
        break;
      case "D":
        right = false;
        break;
      case "A":
        left = false;
        break;
    }

    setPlayerVelocity();
  }
  return false;
}
//set the velocity of the player based on what keys are currently down
function setPlayerVelocity() {
  player.vel.y = 0;
  if (up) {
    player.vel.y -= 1;
  }
  if (down) {
    player.vel.y += 1;
  }
  player.vel.x = 0;
  if (left) {
    player.vel.x -= 1;
  }
  if (right) {
    player.vel.x += 1;
  }
}

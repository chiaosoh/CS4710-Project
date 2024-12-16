class Player {
  constructor() {
    this.pos = createVector(3 * tileSize + xoff, 4 * tileSize + yoff);
    this.vel = createVector(0, 0);
    this.size = tileSize / 2.0;
    this.playerSpeed = tileSize / 15.0;
    this.dead = false;
    this.reachedGoal = false;
    this.fadeCounter = 255;
    this.isBest = false;
    this.deathByDot = false;
    this.deathAtStep = 0;
    this.moveCount = 0;
    this.gen = 1;
    this.fitness = 0;
    this.nodes = [];
    this.fading = false;
    this.human = false;
    this.setNodes();
  }

  setNodes() {
    this.nodes[0] = new Node(tiles[6][7]);
    this.nodes[1] = new Node(tiles[17][2]);
    this.nodes[0].setDistanceToFinish(this.nodes[1]);
  }

  show() {
    fill(255, 0, 0, this.fadeCounter);
    if (this.isBest && !showBest) {
      fill(0, 255, 0, this.fadeCounter);
    }
    stroke(0, 0, 0, this.fadeCounter);
    strokeWeight(4);
    rect(this.pos.x, this.pos.y, this.size, this.size);
    stroke(0);
  }

  move() {
    var temp = createVector(this.vel.x, this.vel.y);
    temp.normalize();
    temp.mult(this.playerSpeed);
    for (var i = 0; i < solids.length; i++) {
      temp = solids[i].restrictMovement(
        this.pos,
        createVector(this.pos.x + this.size, this.pos.y + this.size),
        temp
      );
    }
    this.pos.add(temp);
  }

  checkCollisions() {
    for (var i = 0; i < dots.length; i++) {
      // if (
      //   dots[i].collides(
      //     this.pos,
      //     createVector(this.pos.x + this.size, this.pos.y + this.size)
      //   )
      // ) {
      //   this.fading = true;
      //   this.dead = true;
      //   this.deathByDot = true;
      // }
    }
    if (
      winArea.collision(
        this.pos,
        createVector(this.pos.x + this.size, this.pos.y + this.size)
      )
    ) {
      this.reachedGoal = true;
    }
    for (var i = 0; i < this.nodes.length; i++) {
      this.nodes[i].collision(
        this.pos,
        createVector(this.pos.x + this.size, this.pos.y + this.size)
      );
    }
  }

  update() {
    if (!this.dead && !this.reachedGoal) {
      this.move();
      this.checkCollisions();
    } else if (this.fading) {
      if (this.fadeCounter > 0) {
        if (humanPlaying || replayGens) {
          this.fadeCounter -= 10;
        } else {
          this.fadeCounter = 0;
        }
      }
    }
  }
}

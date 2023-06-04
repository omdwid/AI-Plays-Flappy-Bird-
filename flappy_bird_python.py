import random
import os
import pygame
import neat
import time
pygame.font.init()

WIN_WIDTH = 500
WIN_HEIGHT = 800
BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))
            ]

PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))


STAT_FONT = pygame.font.SysFont("comicsans",size=50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.img = self.IMGS[0]
        self.tilt = 0
        self.tick_count = 0
        self.height= self.y
        self.img_count = 0
        self.vel = 0
        
    def jump(self):
        self.vel = -10.5 # in pygame the coordinates start from the top left corner of the window to up direction is negative while the horizontal direction remains the same
        self.tick_count = 0
        self.height = self.y
    
    def move(self):
        self.tick_count += 1
        d = self.vel * self.tick_count + 1.5*self.tick_count**2
        
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2
        
        self.y = self.y + d
        
        if d <0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        elif self.tilt > -90:
            self.tilt = self.tilt - self.ROT_VEL
        
        
    def draw(self, win):
        self.img_count += 1
        
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
            
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2
        
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center = self.img.get_rect(topleft = (self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
        
    def get_mask(self): # in case of the collision
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5 # move the pipe backward so that the bird looks like it is moving forward
    def __init__(self, x): 
        self.x = x
        self.height = 0
        self.gap = 100 # denotes the gap between the top pipe and bottom pipe
        self.top = 0 # denotes the position of the top pipe image
        self.bottom = 0 # denotes the position of the bottom pipe image
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True) # this store the inverted image of pipe which will be at the top of the window
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.get_height()

    def get_height(self):
        self.height = random.randrange(40, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x = self.x - self.VEL


    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()    
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        t_point = bird_mask.overlap(top_mask, top_offset) # if not collide than it will return None
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)

        if t_point or b_point:
            return True
        return False

class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y) -> None:
        self.y = y
        self.x1 = 0 # denotes the starting position of the first image of base
        self.x2 = self.WIDTH # denotes the starting position of the second image of the base

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0 : #first image leaves the frame 
            self.x1 = self.x2 + self.WIDTH 
        if self.x2 + self.WIDTH< 0 : # second image leaves the frame
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))
 
def draw_window(win, birds, pipes, base, score, gen):
    if gen == 0:
        gen = 1
    win.blit(BG_IMG, (0,0))
    for bird in birds:
        bird.draw(win)

    for pipe in pipes:
        pipe.draw(win)

    score_label = STAT_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))


    text = STAT_FONT.render("Score:" + str(score), 1,(255,255,255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))
    # alive
    score_label = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))

    base.draw(win)
    pygame.display.update()
    
# genomes is the neural networks that keeps track of the birds
def main(genomes, config):
        
        ge = []
        nets = []
        birds = []

        for _,g in genomes:
            net = neat.nn.FeedForwardNetwork.create(g, config)
            nets.append(net)
            birds.append(Bird(230,350))
            g.fitness = 0
            ge.append(g)

        base = Base(730)
        pipes = [Pipe(600)]
        run = True
        win  = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        score = 0
        clock = pygame.time.Clock()
        
        while run:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.quit()
                    quit()

            pipe_ind = 0
            if len(birds) > 0:
                if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                    pipe_ind = 1    
            else:
                run = False
                break
                

            for x, bird in enumerate(birds):
                bird.move()
                ge[x].fitness += 0.1
                
                output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height),abs(bird.y - pipes[pipe_ind].bottom)))
                if output[0] > 0.5:
                    bird.jump()

            rm = []
            add_pipe = False
            for pipe in pipes:
                pipe.move()
                for x, bird in enumerate(birds):
                    if pipe.collide(bird):
                       ge[x].fitness -= 1 # decrease the fitness of the bird that collides so that it doesn't gets selected
                       birds.pop(x)
                       nets.pop(x)
                       ge.pop(x) 

                if not pipe.passed and bird.x > pipe.x:
                    pipe.passed = True
                    add_pipe = True

                if pipe.x + pipe.PIPE_TOP.get_width() < 0: # pipe has crossed the frame
                    rm.append(pipe)
                    
                    
            if add_pipe:
                score += 1
                # adding the fitness to the birds the make through the pipe
                pipes.append(Pipe(600))
                for g in ge:
                    g.fitness += 5

            for r in rm:
                pipes.remove(r)

            for x,bird in enumerate(birds):
                if bird.y + bird.img.get_height() - 10 >= 730 or bird.y < -50:
                    birds.pop(x)
                    ge.pop(x)
                    nets.pop(x)                
            base.move()      
            draw_window(win, birds, pipes, base, score, gen=0)
                    
        

#main()


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main,50) # fitness function - it is used to kind of evaluate the population 

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
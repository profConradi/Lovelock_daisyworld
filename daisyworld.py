import pygame as pg
import numpy as np
import sys
import serial, time

#serial config
port = "/dev/ttyACM0"
baud = 115200
s = serial.Serial(port)
s.baudrate = baud

#daisy world config
L = 128  #size
lmbd = 0.3  #probability of daisy death in each cycle
q = 2.06425 *10**9 # constant to calculate local temperature from local albedo
S_sigma = 1.68 *10**10 #star energy flux / Stefan-Boltzman constant
lumin = 1.0 #energy flux control parameter

#REF: Daisyworld revisited: quantifying biological effects on planetary self-regulation
#T. M. Lenton, J. Lovelock Published 2001 Tellus B: Chemical and Physical Meteorology


temp_history = []
#starting state
temp_field = np.ones((L,L), dtype = np.float)*20.
daisy_field = np.random.choice(3, size=(L,L), p=[0.5, 0.3, 0.2])+1

#daisy: 1->black, 2->ground, 3->white

pg.init()
screen = pg.display.set_mode((800, 600))
clock = pg.time.Clock()
colors = np.array([[0,0,0], [153, 153, 255], [160, 160, 160], [255, 255, 153]])
text_color = pg.Color('lightskyblue3')
font = pg.font.Font(None, 32)

def beta(t):
    return max(0,1-((22.5-t)/17.5)**2) #daisy growth rate funtion T in °C
vbeta = np.vectorize(beta)

def iterate(l_intensity=lumin):
    #my vectorized algorithm
    global daisy_field, temp_field
    white = np.where(daisy_field==3,1,0)
    black = np.where(daisy_field==1,1,0)
    ground = np.where(daisy_field==2,1,0)
    
    
    N_ground = (np.roll(ground,1,axis=0) + np.roll(ground,-1,axis=0) +
                          np.roll(ground,1,axis=1) + np.roll(ground,-1,axis=1))
    N_white = (np.roll(white,1,axis=0) + np.roll(white,-1,axis=0) + 
                          np.roll(white,1,axis=1) + np.roll(white,-1,axis=1))
    N_black = (np.roll(black,1,axis=0) + np.roll(black,-1,axis=0) + 
                          np.roll(black,1,axis=1) + np.roll(black,-1,axis=1))
  
    N_ground_ = N_ground.ravel()
    N_white_ = N_white.ravel()
    N_black_ = N_black.ravel()
    daisy_field_ = daisy_field.ravel()
    temp_field_ = temp_field.ravel()
    beta_ = vbeta(temp_field_)
    grows_ = np.random.uniform(size=(L,L)).ravel()
    die_ = np.random.uniform(size=(L,L)).ravel()
    

    Rule_growblack = np.argwhere( (daisy_field_==2) & (N_black_>N_white_) & (grows_<beta_))
    Rule_growwhite = np.argwhere( (daisy_field_==2) & (N_black_<N_white_) & (grows_<beta_))
    Rule_growrandom = np.argwhere( (daisy_field_==2) & (N_black_==N_white_) & (grows_<beta_))
    Rule_die = np.argwhere( ((daisy_field_==3) | (daisy_field_==1)) & (die_<lmbd))

    
    daisy_field_[Rule_die] = 2 
    daisy_field_[Rule_growblack] = 1
    daisy_field_[Rule_growwhite] = 3
    daisy_field_[Rule_growrandom] = np.random.choice([1,3])
    
    albedo_mean = np.average(0.25*daisy_field_)
    temp_mean = np.power(S_sigma*l_intensity*(1-albedo_mean),0.25)-273.
    temp_history.append(temp_mean)
    temp_field_[:] = np.power(q*(albedo_mean-0.25*daisy_field_)+(temp_mean+273)**4,0.25)-273.
    
    temp_field = 0.6*temp_field + 0.1*(np.roll(temp_field,1,axis=0) + np.roll(temp_field,-1,axis=0) + 
                          np.roll(temp_field,1,axis=1) + np.roll(temp_field,-1,axis=1))
    return temp_mean


running = True
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    screen.fill((30, 30, 30))
    data = s.readline()
    data = int(data[0:4])
    lumin = 0.6 + 0.9*(data/255)
    lum_surface = font.render("L = {:2.2f}".format(lumin), False, text_color)
    temperature = iterate(lumin)
    temp_surface = font.render("T = {:2.2f}".format(temperature), False, text_color)
    #gridarray = np.random.randint(3, size=(20, 20))
    surface = pg.surfarray.make_surface(colors[daisy_field])
    surface = pg.transform.scale(surface, (512, 512))  # Scaled a bit.
    screen.blit(lum_surface,(600,240))
    screen.blit(temp_surface,(600,280))
    screen.blit(surface, (50, 40))
    pg.display.flip()
    clock.tick(60)

pg.quit()
sys.exit()
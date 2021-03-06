import math, random, consts, items, utils, monsters, copy, tdl

# Represents a stylistic area of the dungeon.
class Area:
    def __init__(self, x, y, w, h, at=None):
        self.pos1 = (x, y)
        self.pos2 = (x+w, y+h)
        self.w = w
        self.h = h

        self.area_type = random.choice(['Marble',
                                        'Cave', 'Cave',
                                        'Planted', 'Planted', 'Planted'])
        if at: self.area_type = at
        
    # Check equality
    def __eq__(self, other):
        return other != None and self.__dict__ == other.__dict__
    
    def inside(self, pos):
        x1, y1 = self.pos1
        x2, y2 = self.pos2
        return x1 <= pos[0] and x2 >= pos[0] and y1 <= pos[1] and y2 >= pos[1]
    
    def edge_points(self):
        pnts = [(0,0)]
        for x in range(1, self.pos2[0]):
            pnts.append((x, self.pos1[1]))
            pnts.append((x, self.pos2[1]-1))
            
        for y in range(1, self.pos2[1]):
            pnts.append((self.pos1[0], y))
            pnts.append((self.pos2[0]-1, y))

        return pnts

# Represents a dungeon room.
class Room(Area):
    def __init__(self, x, y, w, h, rtype=None):
        super(Room, self).__init__(x, y, w, h)
        # Diagnostic: is this room connected according to the DGA?
        self.connected = False
        self.item_attempts = 0
        self.kills = 0
        self.monster_cnt = 0
        
        # Circle dimentions
        self.radius = math.floor(w/2)

        # Room type:
        self.room_type = rtype or random.choice([
            'Square', 'Square',
            'Square', 'Round',
            'Round', 'Sanctuary',
            'Square', 'Sancutary',
            'Pool'
        ])

        # Room center.
        self.center = (math.floor((self.pos1[0] - self.w) / 2),
                       math.floor((self.pos1[1] + self.h) / 2))
        if self.room_type == 'Sanctuary' and w < 9:
            self.room_type = 'Square'

    def add_corridor(self, tmap, other):
        start_x = random.randint(self.pos1[0], self.pos2[0])
        start_y = random.randint(self.pos1[1], self.pos2[1])
        
        goal_x = random.randint(other.pos1[0], other.pos2[0])
        goal_y = random.randint(other.pos1[1], other.pos2[1])
        
        temp = tdl.map.Map(consts.WIDTH, consts.HEIGHT)
        for x,y in temp:
            temp.walkable[x,y] = True
        p = temp.compute_path(
            start_x, start_y,
            goal_x, goal_y,
            diagonal_cost=0
        )
        for i, point in enumerate(p):
            tmap.place_cell(point, is_wall=False)
                
    # Checks if a room intersects the other.
    def intersects(self, room):
        x1, y1 = self.pos1
        x2, y2 = self.pos2
        return x1 <= room.pos2[0] and x2 >= room.pos1[0] and\
            y1 <= room.pos2[1] and y2 >= room.pos1[1]

    def create_block(self, tmap, spacing, raw_pos):
        pos = utils.tuple_add(self.pos1, raw_pos)
        wall = raw_pos[0] % spacing == 0 and raw_pos[1] % spacing == 0
        tmap.place_cell(pos, is_wall=wall)

        # Add decoration/fire and items.
        if not wall:
            if random.randint(0, 100) < int(consts.DIFFICULTY / 3.5) and self.num != 0 and self.monster_cnt < consts.DIFFICULTY:
                self.monster_cnt += 1
                m = copy.copy(random.choice(monsters.select_by_difficulty(tmap.dungeon_level)))
                m.pos = pos
                tmap.dungeon['monsters'].append(m)
            decor = ['FM', None, None, None]
            if tmap.is_hell_level():
                decor = ['FR', 'FL', None, None, None, None]
            if random.randint(1, 1000) < 5:
                decor = ['TTRAP', 'TTRAP', 'DTRAP', 'ITRAP']
            c = random.choice(decor)
            if c: tmap.dungeon['decor'][pos] = c

            if self.item_attempts < consts.ITEMS_PER_ROOM:
                n = random.randint(1, 100)
                pitems = list(filter(lambda x: n < x.probability,
                                     sorted(items.DUNGEON_ITEMS,
                                            key=lambda x: x.probability)))
                if len(pitems) > 0:
                    tmap.dungeon['items'][pos] = [pitems[0]]
                    self.item_attempts += 1
                else:
                    tmap.dungeon['items'][pos] = []
            else:
                tmap.dungeon['items'][pos] = []
                

    # Draws the room into the supplied terrain map.
    def draw_into_map(self, i, tmap):
        spacing = random.randint(4, 31)
        self.num = i
        
        if self.room_type == 'Square':
            for x in range(0, self.w):
                for y in range(0, self.h):
                    self.create_block(tmap, spacing, (x, y))
        elif self.room_type == 'Round':
            for x in range(-self.radius, self.radius):
                for y in range(-self.radius, self.radius):
                    if x*x + y*y <= pow(self.radius, 2):
                        self.create_block(tmap, spacing, (x, y))
        elif self.room_type == 'Sanctuary':
            tmap.dungeon['areas'].append(Area(self.pos1[0]-1, self.pos1[1]-1, self.w+1, self.h+1, at='Marble'))
            for x in range(0, self.w):
                for y in range(0, self.h):
                    self.create_block(tmap, 60, (x, y))
                    
            gap = random.randint(1, math.floor(self.w/2)-3)
            for x in range(gap, self.w-gap):
                for y in range(gap, self.h-gap):
                    pos = utils.tuple_add(self.pos1, (x, y))
                    if x != gap+1: 
                        tmap.place_cell(pos, is_wall=True)

            for x in range(gap+1, self.w-gap-1):
                for y in range(gap+1, self.h-gap-1):
                    pos = utils.tuple_add(self.pos1, (x, y))
                    tmap.place_cell(pos)
        elif self.room_type == 'Pool':
            for x in range(0, self.w):
                for y in range(0, self.h):
                    if x > 0 and y > 0 and x < self.w-1 and y < self.h-1:
                        tmap.dungeon['water'][x, y] = True
                    else:
                        tmap.place_cell((x,y), is_wall=False)
                        tmap.dungeon['items'][x,y] = []
                        tmap.dungeon['decor'][x,y] = None

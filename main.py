import pygame
from pygame.locals import (K_LEFT, K_RIGHT, K_UP, K_DOWN)
import math
import itertools
import pickle
import pygame_widgets
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox

class debug(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([3,3])
        self.image.fill((0, 0, 255))
        self.rect = self.image.get_rect()
    def setpos(self, where):
        self.rect.x = where[0]
        self.rect.y = where[1]
class Component(pygame.sprite.Sprite):
    def __init__(self):
        global hovering_component
        global components
        global current_wire
        global current_ID
        pygame.sprite.Sprite.__init__(self)
        self.id = current_ID
        current_ID += 1
        self.inputs = [Stick("input", self) for i in range(self.no_of_inputs)]
        self.outputs = [Stick("output", self) for i in range(self.no_of_outputs)]
        self.length = self.size[1]
        self.width = self.size[0]
        self.image = pygame.Surface(self.size)#store original of image for correct rotation purposes
        self.image.set_colorkey(remove_colour)
        component_image = self.getImage()
        component_image = pygame.transform.scale(component_image, (self.width, self.length))
        self.image.blit(component_image, (0, 0))
        self.rect = self.image.get_rect()
        hovering_component = self
        components.add(self)
    def update(self, left_mouse_held):
        global hovering_component
        global hovering_mouse_offset
        if hovering_component == None:
            if self.rect.collidepoint(mouse_pos) and mouse_down:#pick up object
                hovering_component = self
                hovering_mouse_offset = (mouse_pos[0] - self.rect.left, mouse_pos[1] - self.rect.top)
                if isinstance(self, Switch):
                    self.hold_start_pos = self.rect.topleft

            elif mouse_down and current_wire == None:#create wires from objects stick
                for i in self.inputs:
                    if closeEnough(i.connection_point, mouse_pos, 10) and not i.its_wires:#check if stick has no inputs
                        Wire(i, True, False)
                        break
                if current_wire == None:#if it still = none
                    for i in self.outputs:
                        if closeEnough((i.rect.right - 3, i.rect.centery), mouse_pos, 10):#allowed as many outputs as wanted
                            Wire(i, False, self.state)
                            break
        elif hovering_component == self:
            self.rect.x = mouse_pos[0] - hovering_mouse_offset[0]#move object to mouse position
            self.rect.y = mouse_pos[1] - hovering_mouse_offset[1]
            stick_seperation = 20
            stick_start_y = self.rect.centery - ((stick_seperation * self.no_of_inputs) / 2)
            for i in range(0, len(self.inputs)):#move sticks
                self.inputs[i].moveToInp(self.rect.left, stick_start_y + (stick_seperation * i))
            stick_start_y = self.rect.centery - ((stick_seperation * self.no_of_outputs) / 2)
            for i in range(0, len(self.outputs)):
                self.outputs[i].moveToOut(self.rect.right, stick_start_y + (stick_seperation * i))
            #move its connecting wires
            for i in itertools.chain(self.inputs, self.outputs):
                if i.its_wires:#if it has wire on the input/output
                    for j in i.its_wires:
                        j.connectTwoPoints(j.inputs.connection_point, j.outputs.connection_point)
            if left_mouse_held == False:
                if isinstance(self, Switch):
                    if self.hold_start_pos == self.rect.topleft:#if the object has moved
                        self.state = not self.state
                        self.image = pygame.Surface(self.size)
                        self.image.set_colorkey(remove_colour)
                        if self.state:
                            self.image.blit(switch_on, (0, 0))
                        else:
                            self.image.blit(switch_off, (0, 0))

                hovering_component = None
                global changes
                changes.append(self)
    def customMouseCollisions(self, mousePos):#little hider method only used in remove wire
        return (self.rect.collidepoint(mousePos))
    def logicUpdate(self):
        print ("no logic update method for this component")
    def offsetUpdate(self, direction):
        if direction[K_LEFT]:
            self.rect.x += 5
        elif direction[K_RIGHT]:
            self.rect.x -= 5
        elif direction[K_UP]:
            self.rect.y += 5
        elif direction[K_DOWN]:
            self.rect.y -= 5
        if not isinstance(self, Wire):
            stick_seperation = 20
            stick_start_y = self.rect.centery - ((stick_seperation * self.no_of_inputs) / 2)
            for i in range(0, len(self.inputs)):
                self.inputs[i].moveToInp(self.rect.left, stick_start_y + (stick_seperation * i))
            stick_start_y = self.rect.centery - ((stick_seperation * self.no_of_outputs) / 2)
            for i in range(0, len(self.outputs)):
                self.outputs[i].moveToOut(self.rect.right, stick_start_y + (stick_seperation * i))
    def turnOn(self):
        pass
    def save(self):
        return (type(self), self.size, self.no_of_inputs, self.no_of_outputs, self.state, self.rect.topleft, self.id)
    def load(self, save):
        global hovering_component
        global current_ID
        hovering_component = None
        self.size = save[1]
        self.no_of_inputs = save[2]
        self.no_of_outputs = save[3]
        self.state = save[4]
        if save[4]:
            self.turnOn()
        self.rect.topleft = save[5]
        self.id = save[6]
        stick_seperation = 20
        stick_start_y = self.rect.centery - ((stick_seperation * self.no_of_inputs) / 2)
        for i in range(0, len(self.inputs)):
            self.inputs[i].moveToInp(self.rect.left, stick_start_y + (stick_seperation * i))
        stick_start_y = self.rect.centery - ((stick_seperation * self.no_of_outputs) / 2)
        for i in range(0, len(self.outputs)):
            self.outputs[i].moveToOut(self.rect.right, stick_start_y + (stick_seperation * i))   
class Wire(Component):
    def __init__(self, stick, itoo, onoff):
        global current_wire
        self.size = [7, 75]
        self.length = self.size[1]
        self.width = self.size[0]
        self.rotation = 0
        if stick != "fake":#prevent error if loading from save
            self.rotate_around_coord = stick.connection_point
        self.outputs = None
        self.inputs = None
        self.pos_stick = stick#stores the potential stick to connect to when wire is placed
        self.itoo = itoo#(Input TO Output) stores if this wire was created by clicking on an input or an output
        self.state = onoff#make wire spawn in on state if it is created from a component that is on
        pygame.sprite.Sprite.__init__(self)
        self.original_image = pygame.Surface(self.size)
        self.original_image.set_colorkey(remove_colour)
        if self.state:
            self.component_image = pygame.image.load("images/green_wire.png").convert()
        else:
            self.component_image = pygame.image.load("images/red_wire.png").convert()
        self.original_image.blit(self.component_image, (0, 0))
        self.image = self.original_image
        self.rect = self.image.get_rect()
        hovering_component = self
        current_wire = self
        if stick != "fake":#prevent error if loading from save
            self.update()#if this is not called wire will be in wrong place for one frame
    def update(self):#only called on currentWire
        self.connected_both = False
        self.connectTwoPoints(mouse_pos, self.rotate_around_coord)
        self.setConnectionPointCoord()
        for i in sticks:#check if close to a stick
            if closeEnough(i.connection_point, self.connection_point, 15) and ((i.type == "output" and self.itoo) or (i.type == "input" and len(i.its_wires) == 0 and self.itoo == False)):
                self.connected_both = True
                self.connectTwoPoints(i.connection_point, self.rotate_around_coord)
                self.pos_stick2 = i
        if mouse_up:#if user lets go of mouse
            global current_wire
            current_wire = None
            if self.connected_both:#make wire fully placed with inputs and outputs
                if self.itoo == False:
                    self.inputs = self.pos_stick
                    self.outputs = self.pos_stick2
                else:
                    self.inputs = self.pos_stick2
                    self.outputs = self.pos_stick
                self.pos_stick.its_wires.append(self)
                self.pos_stick2.its_wires.append(self)
                self.state = None
                global wires
                wires.add(self)
                del self.pos_stick
                del self.pos_stick2
                del self.connected_both
                del self.itoo
                global changes
                changes.append(self)

            else:#or remove wire if it cant connect to anything
                self.kill()
    def spin(self, amount):
        self.image = pygame.transform.rotate(self.original_image, amount)
        self.rotation = amount
    def logicUpdate(self):
        self.state = self.inputs.its_component.state
        if self.state:
            self.original_image.blit(green_wire, (0, 0))
        else:
            self.original_image.blit(red_wire, (0, 0))
        self.image = self.original_image
        self.spin(self.rotation)
    def setCorrectCornerPos(self):
        if self.rotation < 90:#calculate actual top left corner pos
            self.correct_pos = (self.rect.left, self.rect.top + math.cos(math.radians(90-self.rotation))* self.width)
        elif self.rotation == 90:
            self.correct_pos = self.rect.left, self.rect.top + self.width
        elif self.rotation < 180:
            temp = self.rect.top + self.length * math.cos(math.radians(180-self.rotation))
            self.correct_pos = (self.rect.left + math.sin(math.radians(90-(180-self.rotation))) * self.width, temp + math.cos(math.radians(90-(180-self.rotation))) * self.width)
        elif self.rotation <= 270:
            temp = self.rect.left + (math.cos(math.radians(self.rotation-180)) * self.width)
            self.correct_pos = (temp + (math.sin(math.radians(self.rotation-180)) * self.length), self.rect.top + (math.cos(math.radians(self.rotation-180)) * self.length))
        elif self.rotation <= 360:
            self.correct_pos = (self.rect.left + (math.cos(math.radians(-90-self.rotation)) * self.length), self.rect.top)   
    def customMouseCollisions(self, mousePos):
        if self.rotation == 0:#skip if rotation is 0 for optimisation
            return (self.rect.collidepoint(mouse_pos))
        #pythag theorum
        distance = math.sqrt(((self.correct_pos[0] - mouse_pos[0]) ** 2) + ((self.correct_pos[1] - mouse_pos[1]) ** 2))
        if distance <= self.length + 10:#plus a little extra
            if distance != 0:#avoid divide by 0
                angle = math.degrees(math.asin((abs(mousePos[0] - self.correct_pos[0]))/ distance))
                #bearings from south clockwise positive
                if (mouse_pos[0] - self.correct_pos[0]) > 0:#mouse right of obj
                    if (mouse_pos[1] - self.correct_pos[1]) < 0:#mouse above obj
                        bearing = 180 - angle
                    else:#mouse bellow obj
                        bearing = angle
                else:#mouse left of obj
                    if (mouse_pos[1] - self.correct_pos[1]) < 0:#mouse above obj
                        bearing = 180 + angle
                    else:#mouse bellow obj
                        bearing = 360 - angle
            else:
                bearing = 0 
        else:
            return False

        new_bearing = bearing - self.rotation
        distance = distance * (75 / self.length)
        new_coord = (self.rect.left + (math.sin(math.radians(new_bearing)) * distance), (self.rect.top + (math.cos(math.radians(new_bearing)) * distance)))
        return self.rect.collidepoint(new_coord)
    def getCornerFromConnectionPoint(self, point):
        temp2 = (point[0] - ((self.width/2) * math.cos(math.radians(self.rotation)) + (0) * math.sin(math.radians(self.rotation))), point[1] + ((self.width/2) * math.sin(math.radians(self.rotation)) - (0) * math.cos(math.radians(self.rotation))))
        if self.rotation == 0:
            return temp2
        elif self.rotation <= 90:
            return (temp2[0], temp2[1] - math.cos(math.radians(90-self.rotation))* self.width)
        elif self.rotation <= 180:
            temp = temp2[1] - (self.width * math.sin(math.radians(180-self.rotation)))#wrong
            return (temp2[0] - math.cos(math.radians(180-self.rotation)) * self.width, temp - (math.cos(math.radians(180-self.rotation)) * self.length))
        elif self.rotation <= 270:
            return (temp2[0] - (math.sin(math.radians(self.rotation-180)) * self.length) - (math.cos(math.radians(self.rotation-180))*self.width), temp2[1] - (math.cos(math.radians(self.rotation-180)) * self.length))
        elif self.rotation <= 360:
            return (temp2[0] - math.cos(math.radians(-90-self.rotation))*self.length, temp2[1])
    def setConnectionPointCoord(self):
        self.setCorrectCornerPos()
        self.connection_point = (self.correct_pos[0] + ((self.width/2) * math.cos(math.radians(self.rotation)) + self.length * math.sin(math.radians(self.rotation))), self.correct_pos[1] - ((self.width/2) * math.sin(math.radians(self.rotation)) - self.length * math.cos(math.radians(self.rotation))))
    def currentWireOffsetUpdate(self, direction):
        if direction[K_LEFT]:
            self.rotate_around_coord = (self.rotate_around_coord[0] + 5, self.rotate_around_coord[1])
        elif direction[K_RIGHT]:
            self.rotate_around_coord = (self.rotate_around_coord[0] - 5, self.rotate_around_coord[1])
        elif direction[K_UP]:
            self.rotate_around_coord = (self.rotate_around_coord[0], self.rotate_around_coord[1] + 5)
        elif direction[K_DOWN]:
            self.rotate_around_coord = (self.rotate_around_coord[0], self.rotate_around_coord[1] - 5)
    def connectTwoPoints(self, point1, point2):
        #stretch
        self.length = math.sqrt(((point1[0] - point2[0]) ** 2 ) + ((point1[1] - point2[1]) ** 2 ))
        self.size[1] = self.length
        self.original_image = pygame.Surface(self.size)
        self.original_image.set_colorkey(remove_colour)
        if self.state:
            self.original_image.blit(green_wire, (0, 0))#made black if removed
        else:
            self.original_image.blit(red_wire, (0, 0))
        self.image = self.original_image
        #rotate around point
        if point1[1] == point2[1]:#avoid division by 0
            if point1[0] > point2[0]:
                bearing = 90
            else:
                bearing = 270
            #raise Exception("div by 0")
            #return
        else:
            angle = math.degrees(math.atan(abs(point1[0] - point2[0])/ abs(point1[1]- point2[1])))
            #bearings from south clockwise positive
            if (point1[0] - point2[0]) > 0:#mouse right of obj
                if (point1[1] - point2[1]) < 0:#mouse above obj
                    bearing = 180 - angle
                else:#mouse bellow obj
                    bearing = angle
            else:#mouse left of obj
                if (point1[1] - point2[1]) < 0:#mouse above obj
                    bearing = 180 + angle
                else:#mouse bellow obj
                    bearing = 360 - angle
        self.spin(bearing)
        #move to correct point
        self.rect.topleft = self.getCornerFromConnectionPoint(point2)
        self.setConnectionPointCoord()
    def save(self):
        return (self.state, self.inputs.its_component.id, self.outputs.its_component.id, self.outputs.its_component.inputs.index(self.outputs))
    def load(self, save):
        for i in components:
            if i.id == save[1]:
                self.inputs = i.outputs[0]
                i.outputs[0].its_wires.append(self)
            if i.id == save[2]:
                self.outputs = i.inputs[save[3]]
                i.inputs[save[3]].its_wires.append(self)
        self.state = save[0]
        self.connectTwoPoints(self.inputs.connection_point, self.outputs.connection_point)
        global wires
        wires.add(self)
class Stick(pygame.sprite.Sprite):
    def __init__(self, type, comp):
        pygame.sprite.Sprite.__init__(self)
        self.type = type#input stick or output stick
        self.its_component = comp
        self.its_wires = []
        self.image = pygame.Surface([30,10])#store original of image for correct rotation purposes
        self.image.set_colorkey(remove_colour)
        component_image = pygame.image.load("images/sticky bit.png").convert()
        self.image.blit(component_image, (0, 0))
        self.rect = self.image.get_rect()
        sticks.add(self)
    def moveToInp(self, x, y):
        self.rect.right = x
        self.rect.top = y+5
        self.connection_point = (self.rect.left + 3, self.rect.centery)
    def moveToOut(self, x, y):
        self.rect.left = x
        self.rect.top = y+5
        self.connection_point = (self.rect.right - 3, self.rect.centery)
class AndGate(Component):
    def __init__(self):
        self.size = [50,50]
        self.no_of_inputs = 2
        self.no_of_outputs = 1
        self.state = False
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/and gate.png").convert()
    def logicUpdate(self):
        for i in self.inputs:
            try:
                if i.its_wires[0].state == False:
                    self.state = False
                    break
            except:
                self.state = False
                break 
        else:
            self.state = True
class OrGate(Component):
    def __init__(self):
        self.size = [50, 50]
        self.no_of_inputs = 2
        self.no_of_outputs = 1
        self.state = False
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/or gate.png").convert()
    def logicUpdate(self):
        for i in self.inputs:
            try:
                if i.its_wires[0].state == True:
                    self.state = True
                    break
            except:
                pass
        else:
            self.state = False
class NotGate(Component):
    def __init__(self):
        self.size = [50, 50]
        self.no_of_inputs = 1
        self.no_of_outputs = 1
        self.state = True
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/not gate.png").convert()
    def logicUpdate(self):
        for i in self.inputs:
            try:
                self.state = not i.its_wires[0].state
            except:
                self.state = True
class Off(Component):
    def __init__(self):
        self.size = [70, 70]
        self.no_of_inputs = 0
        self.no_of_outputs = 1
        self.state = False
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/off.png").convert()
    def logicUpdate(self):
        pass
class On(Component):
    def __init__(self):
        self.size = [70, 70]
        self.no_of_inputs = 0
        self.no_of_outputs = 1
        self.state = True
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/on.png").convert()
    def logicUpdate(self):
        pass
class Bulb(Component):
    def __init__(self):
        self.size = [50, 50]
        self.no_of_inputs = 1
        self.no_of_outputs = 0
        self.state = False
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/lightbulb_off.png").convert()
    def turnOn(self):
        self.image.blit(lightbulb_on, (0, 0))
    def logicUpdate(self):
        for i in self.inputs:
            try:
                self.state = i.its_wires[0].state
            except:
                self.state = False
        if self.state == True:
            self.image.blit(lightbulb_on, (0, 0))
        else:
            self.image.blit(lightbulb_off, (0, 0))
class Switch(Component):
    def __init__(self):
        self.size = [50, 50]
        self.no_of_inputs = 0
        self.no_of_outputs = 1
        self.state = False
        self.hold_start_pos = None#switch specific
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/switch_off.png").convert()
    def turnOn(self):
        self.image.blit(switch_on, (0, 0))
    def logicUpdate(self):
        pass
class NorGate(Component):
    def __init__(self):
        self.size = [50,50]
        self.no_of_inputs = 2
        self.no_of_outputs = 1
        self.state = True
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/nor_gate.png").convert()
    def logicUpdate(self):
        for i in self.inputs:
            try:
                if i.its_wires[0].state == True:
                    self.state = False
                    break
            except:
                pass
        else:
            self.state = True
class NandGate(Component):
    def __init__(self):
        self.size = [50,50]
        self.no_of_inputs = 2
        self.no_of_outputs = 1
        self.state = False
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/nand_gate.png").convert()
    def logicUpdate(self):
        for i in self.inputs:
            try:
                if i.its_wires[0].state == False:
                    self.state = True
                    break
            except:
                self.state = True
                break 
        else:
            self.state = False
class XorGate(Component):#true when number of true inputs is odd
    def __init__(self):
        self.size = [50,50]
        self.no_of_inputs = 2
        self.no_of_outputs = 1
        self.state = False
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/xor_gate.png").convert()
    def logicUpdate(self):
        count = 0
        for i in self.inputs:
            try:
                if i.its_wires[0].state == True:
                    count += 1
            except:
                pass
        if count % 2 == 0:
            self.state = False
        else:
            self.state = True
class XnorGate(Component):#false when number of true inputs is odd
    def __init__(self):
        self.size = [50,50]
        self.no_of_inputs = 2
        self.no_of_outputs = 1
        self.state = False
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/xnor_gate.png").convert()
    def logicUpdate(self):
        count = 0
        for i in self.inputs:
            try:
                if i.its_wires[0].state == True:
                    count += 1
            except:
                pass
        if count % 2 == 0:
            self.state = True
        else:
            self.state = False
class DecimalOutput(Component):
    def __init__(self):
        self.size = [50,62]
        self.no_of_inputs = 5
        self.no_of_outputs = 0
        self.state = None#need solution for saving its funny state
        super().__init__()
    def getImage(self):
        return pygame.image.load("images/decimalOutput.png").convert()
    def load(self, save):#workaround to ensure text is created when loaded as text value not stored
        super().load(save)
        changes.append(self)
    def logicUpdate(self):
        num = ""
        for i in range(self.no_of_inputs):
            try:
                if self.inputs[i].its_wires[0].state == True:
                    num = num + "1"
                else:
                    num = num + "0"
            except:
                num = num + "0"
        num = int(num,2)#convert binary to decimal
        component_image = pygame.image.load("images/decimalOutput.png").convert()
        component_image = pygame.transform.scale(component_image, (self.width, self.length))
        self.image.blit(component_image, (0, 0))
        self.image.blit(font.render(str(num), True, (0,0,0)), (10, 10))
class GrabComponentButton(pygame.sprite.Sprite):
    def __init__(self,x,y,gate):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface([70,50])
        self.image.set_colorkey(remove_colour)
        component_image = pygame.image.load(gate).convert()
        component_image = pygame.transform.scale(component_image, [70,50])
        self.image.blit(component_image, (0, 0))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.gate = gate
    def IsClicked(self):
        global components
        if self.rect.collidepoint(mouse_pos) and hovering_component == None:
            if self.gate == "images/lightbulb_on.png":#instanciate the correct gate
                Bulb()
            elif self.gate == "images/and gate.png":
                AndGate()
            elif self.gate == "images/on.png":
                On()
            elif self.gate == "images/off.png":
                Off()
            elif self.gate == "images/or gate.png":
                OrGate()
            elif self.gate == "images/not gate.png":
                NotGate()
            elif self.gate == "images/switch_off.png":
                Switch()
            elif self.gate == "images/nor_gate.png":
                NorGate()
            elif self.gate == "images/nand_gate.png":
                NandGate()
            elif self.gate == "images/xor_gate.png":
                XorGate()
            elif self.gate == "images/xnor_gate.png":
                XnorGate()
            elif self.gate == "images/decimalOutput.png":
                DecimalOutput()
        
def isClickedSave():
    file = open("save", "wb")
    global current_ID
    pickle.dump(current_ID, file)#metadata
    pickle.dump(len(components), file)#metadata
    for i in itertools.chain(components, wires):#iterate over all components, wires and write save data to save
        t = i.save()
        pickle.dump(t, file)
    file.close
def isClickedLoad():
    for sprite in components:
        sprite.kill()
    for sprite in sticks:
        sprite.kill()
    for sprite in wires:
        sprite.kill()
    file = open("save", "rb")
    global current_ID
    current_ID = pickle.load(file)#metadata
    for i in range(pickle.load(file)):#load components
        save = pickle.load(file)
        if (str(save[0])[17:][:-2]) == "AndGate":#choose which component to make --must be a better solution than this
            component = AndGate()
        elif (str(save[0])[17:][:-2]) == "OrGate":
            component = OrGate()
        elif (str(save[0])[17:][:-2]) == "NotGate":
            component = NotGate()
        elif (str(save[0])[17:][:-2]) == "Off":
            component = Off()
        elif (str(save[0])[17:][:-2]) == "On":
            component = On()
        elif (str(save[0])[17:][:-2]) == "Bulb":
            component = Bulb()
        elif (str(save[0])[17:][:-2]) == "Switch":
            component = Switch()
        elif (str(save[0])[17:][:-2]) == "NorGate":
            component = NorGate()
        elif (str(save[0])[17:][:-2]) == "NandGate":
            component = NandGate()
        elif (str(save[0])[17:][:-2]) == "XorGate":
            component = XorGate()
        elif (str(save[0])[17:][:-2]) == "XnorGate":
            component = XnorGate()
        elif (str(save[0])[17:][:-2]) == "DecimalOutput":
            component = DecimalOutput()
        component.load(save)#add all saved data to component
        components.add(component)#add to components group
    while True:#load in wires
        try:
            save = pickle.load(file)
            wire = Wire("fake", True, True)
            global current_wire
            current_wire = None

            deb.setpos(wire.rect.topright)
            wire.load(save)
        except:
            break
    file.close
def isClickedClear():

    for sprite in components:
        sprite.kill()
    for sprite in sticks:
        sprite.kill()
    for sprite in wires:
        sprite.kill()
    global changes
    changes = []
def isClickedSimSpeed(inc):
    global sim_speed
    sim_speed += inc
    if sim_speed < 0:
        sim_speed = 0
    #simSpeedValue.image = font.render(str(sim_speed), True, (0,0,0))
def isClickedBackground():
    global background_num
    background_num += 1
    if background_num > 8:
        background_num = 0
    global background_colour
    background_colour = backgrounds[background_num]

def closeEnough(p1, p2, dist):
    if p1[0] > p2[0] - dist and p1[0] < p2[0] + dist:
        if p1[1] > p2[1] - dist and p1[1] < p2[1] + dist:
            return True
    return False
# Basic Pygame Structure
pygame.init()
font = pygame.font.SysFont('Arial', 25, 1 , False)

#read in settings
file = open("settings.txt", "r")
sim_speed = int(file.readline())
screen_height = int(file.readline())
screen_width = screen_height * (16/9)
backgrounds = ((0,51,51), (192,192,192), (100,100,0), (255,255,255), (255,52,52), (255,128,0), (128,255,0), (0,128,255), (127,0,255))
background_num = int(file.readline())
background_colour = backgrounds[background_num]
file.close

#initialise variables
remove_colour = (255,0,255)
screen = pygame.display.set_mode([screen_width, screen_height]) 
pygame.display.set_caption("Logic Gate Simulator")
mouse_pos = [0] * 2
running = True#controls main loop
current_ID = 0
clock = pygame.time.Clock()
changes = []
font = pygame.font.Font('freesansbold.ttf', 32)
hovering_component = None
hovering_mouse_offset = (0, 0)#if this is not used objects are allways picked up at the top left corner
current_wire = None

#load images that will be used later
green_wire = pygame.image.load("images/green_wire.png").convert()
red_wire = pygame.image.load("images/red_wire.png").convert()
lightbulb_off = pygame.image.load("images/lightbulb_off.png").convert()
lightbulb_off = pygame.transform.scale(lightbulb_off, (50, 50))
lightbulb_on = pygame.image.load("images/lightbulb_on.png").convert()
lightbulb_on = pygame.transform.scale(lightbulb_on, (50, 50))
switch_on = pygame.image.load("images/switch_on.png").convert()
switch_on = pygame.transform.scale(switch_on, (50, 50))
switch_off = pygame.image.load("images/switch_off.png").convert()
switch_off = pygame.transform.scale(switch_off, (50, 50))

#create groups
components = pygame.sprite.Group()
wires = pygame.sprite.Group()
sticks = pygame.sprite.Group()
comp_buttons = pygame.sprite.Group()

#component buttons
comp_buttons.add(GrabComponentButton(0, 0, "images/lightbulb_on.png"))
comp_buttons.add(GrabComponentButton(0, 50, "images/or gate.png"))
comp_buttons.add(GrabComponentButton(0, 100, "images/not gate.png"))
comp_buttons.add(GrabComponentButton(0, 150, "images/and gate.png"))
comp_buttons.add(GrabComponentButton(0, 200, "images/on.png"))
comp_buttons.add(GrabComponentButton(0, 250, "images/off.png"))
comp_buttons.add(GrabComponentButton(0, 300, "images/switch_off.png"))
comp_buttons.add(GrabComponentButton(0, 350, "images/nor_gate.png"))
comp_buttons.add(GrabComponentButton(0, 400, "images/nand_gate.png"))
comp_buttons.add(GrabComponentButton(0, 450, "images/xor_gate.png"))
comp_buttons.add(GrabComponentButton(0, 500, "images/xnor_gate.png"))
comp_buttons.add(GrabComponentButton(0, 550, "images/decimalOutput.png"))

#settings buttons
save_button = Button(screen, screen_width-80, 0, 80, 30, text='save', hoverColour=(255, 0, 0), inactiveColour=(165, 0, 0), pressedColour=(0, 255, 0), radius=4, onClick=lambda:isClickedSave())
load_button = Button(screen, screen_width-80, 30, 80, 30, text='load', hoverColour=(0, 255, 0), inactiveColour=(0, 165, 0), radius=4, onClick=lambda:isClickedLoad())
clear_button = Button(screen, screen_width-80, 60, 80, 30, text='clear', hoverColour=(50, 80, 255), inactiveColour=(135, 206, 242), radius=4, onClick=lambda:isClickedClear())
background_button = Button(screen, screen_width-80, 90, 80, 30, text='background', hoverColour=(200, 100, 0), inactiveColour=(255, 165, 0), radius=4, onClick=lambda:isClickedBackground())
sim_speed_slider = Slider(screen, screen_width-80, 132, 60, 8, min=0, max=99, step=1, handleRadius=7, handleColour=(69,69,69))
output = TextBox(screen, screen_width-32, 157, 0, 0, fontSize=30, borderThickness=0, colour=(0,15,0,80))

#______------____testing components___--------______
deb = debug()
#deb2 = debug()
#deb3 = debug()
#deb4 = debug()

try:
    isClickedLoad()
except:
    pass
# -------- Main Program Loop -----------
while running:
    #user inputs
    mouse_up = False
    mouse_down = False
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:#make close button work
            running = False
        if event.type == pygame.MOUSEMOTION:#store mouse position
            mouse_pos[:] = list(event.pos)
        if event.type == pygame.MOUSEBUTTONUP:
            mouse_up = True
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_down = True
            for sprite in comp_buttons:
                sprite.IsClicked()

        #remove components        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            for comp in itertools.chain(wires, components):
                if comp.customMouseCollisions(mouse_pos):#check if mouse is over a component
                    if isinstance(comp, Wire):#if it is a wire
                        changes.append(comp.outputs.its_component)#once wire is removed logic update is required
                        comp.outputs.its_wires.remove(comp)#remove references to the wire
                        comp.inputs.its_wires.remove(comp)#remove the wire
                        comp.kill()#inconsistant if this line not present
                        break
                    else:#if it is a component
                        if comp == hovering_component:
                            hovering_component = None#fixes a little bug
                        for stic in itertools.chain(comp.inputs, comp.outputs):#all traces of the component will be
                            for wire in stic.its_wires:#                        hunted down and defeated including
                                changes.append(wire.outputs.its_component)#     wires that connect to it and references
                                wire.inputs.its_wires.remove(wire)#             to those wires
                                wire.outputs.its_wires.remove(wire)
                                wires.remove(wire)
                            sticks.remove(stic)
                            stic.kill
                        components.remove(comp)
                        comp.kill
                        break#avoid unnessesary looping

    #allow move all components around with arrow keys
    keys=pygame.key.get_pressed()
    if keys[K_DOWN] or keys[K_UP] or keys[K_LEFT] or keys[K_RIGHT]:
        for i in components:
            i.offsetUpdate(keys)
        for i in wires:
            i.offsetUpdate(keys)
        try:
            current_wire.currentWireOffsetUpdate(keys)
        except:
            pass

    #update currentWire
    if current_wire != None:
        current_wire.update()
    #update components
    for sprite in components:
        sprite.update(pygame.mouse.get_pressed()[0])

    #apply logic updates to all components that have been changed
    if changes:
        for i in range(sim_speed):
            changes.append(False)#split changes into sections
            while True:
                if changes[0] != False:
                    changes[0].logicUpdate()
                    if isinstance(changes[0], Wire):#enqueue child nodes to changes
                        changes.append(changes[0].outputs.its_component)
                    else:
                        for j in changes[0].outputs:#not right
                            for k in j.its_wires:
                                changes.append(k)#add outputs to changes so they can be updated later
                    del changes[0]
                else:
                    del changes[0]
                    break#if nothing left to update or end of a section
    
    #draw to screen
    screen.fill(background_colour)
    wires.draw(screen)
    sticks.draw(screen)
    components.draw(screen)
    comp_buttons.draw(screen)
    if current_wire != None:
        screen.blit(current_wire.image, current_wire.rect)
    if hovering_component != None:
        screen.blit(hovering_component.image, hovering_component.rect)

    pygame_widgets.update(events)#update widgets
    output.setText(sim_speed_slider.getValue())
    #screen.blit(deb.image, deb.rect)
    #screen.blit(deb2.image, deb2.rect)
    #screen.blit(deb3.image, deb3.rect)
    #screen.blit(deb4.image, deb4.rect)
    pygame.display.flip()
    clock.tick(60)
    #print(clock.get_fps())
#saving
file = open("settings.txt", "w")
file.writelines([str(sim_speed), "\n", str(screen_height), "\n", str(background_num)])
file.close

#end pygame
pygame.quit()
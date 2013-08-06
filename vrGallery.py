# TODO: Suppress Panda3d console output

import glob, math, os, random, sys

from direct.showbase.ShowBase import ShowBase
from direct.showbase.DirectObject import DirectObject
from direct.task import Task 
from direct.interval.IntervalGlobal import *
from panda3d.core import *

# TODO: Rewrite controls code
class Controls(DirectObject):
	def __init__(self):
		self.mouseChangeX = 0
		self.windowSizeX = base.win.getXSize()
		self.windowSizeY = base.win.getYSize()
		self.centerX = self.windowSizeX / 2
		self.centerY = self.windowSizeY / 2
		self.H = base.camera.getH()
		self.P = base.camera.getP()
		self.pos = base.camera.getPos()
		self.sensitivity = .5
		self.speed = .2
		self.walking = False
	
	def movement(self, task):
		mouse = base.win.getPointer(0)
		x = mouse.getX()
		y = mouse.getY()
		if base.win.movePointer(0, self.centerX, self.centerY):
			self.mouseChangeX = self.centerX - x
			self.H += self.mouseChangeX * self.sensitivity
			base.camera.setHpr(self.H , 0, 0)
	
		self.accept("w", self.startWalking)
		self.accept("w-up", self.stopWalking)
		
		if self.walking:
			self.walk()
	
		return Task.cont
	
	def startMovement(self):
		base.camera.setPos(self.pos)
		base.camera.setZ(PLAYERHEIGHT)
		base.win.movePointer(0, self.centerX, self.centerY)
		taskMgr.add(self.movement, 'movement')
		
	def stopMovement(self):
		taskMgr.remove('movement')
	
	def startWalking(self):
		self.walking = True
	
	def stopWalking(self):
		self.walking = False
	
	def walk(self):
		dir = base.camera.getNetTransform().getMat().getRow3(1) 
		dir.setZ(0)
		dir.normalize()
		self.pos += dir * self.speed
		base.camera.setPos(self.pos)
		base.camera.setZ(PLAYERHEIGHT)

NUMWALLS			= 4
PLAYERHEIGHT 		= 4.0
MINCARDHEIGHT 		= 2.0
MAXCARDHEIGHT 		= 7.0
CARDCENTERHEIGHT 	= 4.0
MINCARDPADDING 		= 0.5
WALLHEIGHT			= 10.0

class VRGallery(ShowBase):
	def __init__(self):
		ShowBase.__init__(self)
		
		self.disableMouse()
		props = WindowProperties()
		props.setCursorHidden(True)
		base.win.requestProperties(props)
		
		# Exit when escape key is pressed
		self.accept("escape", sys.exit)
		
		# Did we get enough arguments?
		if len(sys.argv) <= 1:
			exit("You must specify the path for a directory of image files")
		
		# Get a list of all the files in the target directory
		path = sys.argv[1]
		
		# Is path a valid directory?
		if not os.path.isdir(path):
			exit("Not a directory")
			
		# Get a list of all the image files in the directory
		files = glob.glob(os.path.join(path, "*"))
		images = [{"path": f} for f in files if os.path.splitext(f)[1].lower() in [".jpg", ".jpeg", ".png"]]

		# Load textures from filesystem, store with related metadata
		for i in images:
			i["texture"] = loader.loadTexture(i["path"])
			i["aspect"] = float(i["texture"].getOrigFileXSize()) / float(i["texture"].getOrigFileYSize())
			i["height"] =  random.uniform(MINCARDHEIGHT, MAXCARDHEIGHT) # Set a random height
			i["width"] = i["height"] * i["aspect"]
		
		# Sort images by widths into "walls"
		# This is basically the partition problem: wikipedia.org/wiki/Partition_problem
		# TODO: Support variable wall lengths rather than only squares
		walls = [[] for _ in range(NUMWALLS)]	# Store our piles of images here
		totals = [0] * NUMWALLS 				# Store the total length of the images in each wall
		wall = 0 								# The current wall
		
		images = sorted(images, key=lambda image: image["width"], reverse=True) # Sort in descending order by width
		
		for i in images:
			smallest = totals.index(min(totals))
			walls[smallest].append(i)
			totals[smallest] += i["width"] + MINCARDPADDING
		
		# Render images
		wallLength = max([total + MINCARDPADDING * len(walls[t]) for t, total in enumerate(totals)])
		imageGroupNodes = [None] * NUMWALLS
		
		for indexW, w in enumerate(walls):
			imageGroupNodes[indexW] = render.attachNewNode(PandaNode("%i wall" % (indexW)))
			imageGroupNodes[indexW].setPos(0, 0, 0)
			
			padding = wallLength - totals[indexW]
			offset = padding / 2.0 # Set initial offset
			
			for indexI, i in enumerate(w):
				cm = CardMaker("%i %i card" % (indexW, indexI))
				cm.setFrame(0, i["width"], 0, i["height"])
				card = NodePath(cm.generate())
				card.setTexture(i["texture"])
				card.setPos(offset, 0, CARDCENTERHEIGHT - i["height"] / 2.0)
				card.reparentTo(imageGroupNodes[indexW])
				
				offset += i["width"] + padding
				
		# Position and rotate images
		imageGroupNodes[0].setPos(-wallLength / 2.0, wallLength / 2.0, 0)
		imageGroupNodes[0].setHpr(0, 0, 0)
		imageGroupNodes[1].setPos(wallLength / 2.0, wallLength / 2.0, 0)
		imageGroupNodes[1].setHpr(270, 0, 0)
		imageGroupNodes[2].setPos(wallLength / 2.0, -wallLength / 2.0, 0)
		imageGroupNodes[2].setHpr(180, 0, 0)
		imageGroupNodes[3].setPos(-wallLength / 2.0, -wallLength / 2.0, 0)
		imageGroupNodes[3].setHpr(90, 0, 0)
		
		# Render walls
		# FIXME: Should be procedural
		wallNodes = []
		fudge = 0.1 # Need to fudge widths a bit so pictures don't share a plane with the walls
		
		for index, w in enumerate(walls):
			cm = CardMaker("%i wall" % (index))
			cm.setFrame(-wallLength / 2 - fudge, wallLength + fudge * 2, -WALLHEIGHT / 2, WALLHEIGHT)
			card = NodePath(cm.generate())
			card.reparentTo(render)
			wallNodes.append(card)
			
		# Position and rotate walls
		# FIXME: Should be procedural
		wallNodes[0].setPos(-wallLength / 2.0 - fudge, wallLength / 2.0 + fudge, 0)
		wallNodes[0].setHpr(0, 0, 0)
		wallNodes[1].setPos(wallLength / 2.0 + fudge, wallLength / 2.0 + fudge, 0)
		wallNodes[1].setHpr(270, 0, 0)
		wallNodes[2].setPos(wallLength / 2.0 + fudge, -wallLength / 2.0 - fudge, 0)
		wallNodes[2].setHpr(180, 0, 0)
		wallNodes[3].setPos(-wallLength / 2.0 - fudge, -wallLength / 2.0 - fudge, 0)
		wallNodes[3].setHpr(90, 0, 0)
		
		# Render floor
		# FIXME: Should support odd room shapes
		cm = CardMaker("floor")
		cm.setFrame(-wallLength / 2 - fudge, wallLength + fudge * 2, -wallLength / 2 - fudge, wallLength + fudge * 2)
		floor = NodePath(cm.generate())
		floor.reparentTo(render)
		floor.setZ(-WALLHEIGHT / 2)
		floor.setHpr(0, 270, 0)
		wood = loader.loadTexture("wood.jpg")
		floor.setTexture(wood)
		floor.setTexScale(TextureStage.getDefault(), 10.0, 10.0) # FIXME: Should be dynamic
				
		# Initialize controls		
		controls = Controls()
		controls.startMovement()
		
app = VRGallery()
app.run()
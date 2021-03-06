# import adsk.core, traceback
import adsk.core, traceback
import re, math, time

LAYOUT = """
[["Esc",{x:1},"F1","F2","F3","F4",{x:0.5},"F5","F6","F7","F8",{x:0.5},"F9","F10","F11","F12",{x:0.25},"PrtSc","Scroll Lock","Pause Break"],
[{y:0.5},"~ `","! 1","@ 2","# 3","$ 4","% 5","^ 6","& 7","* 8","( 9",") 0","_ -","+ =",{w:2},"Backspace",{x:0.25},"Insert","Home","PgUp",{x:0.25},"Num Lock","/","*","-"],
[{w:1.5},"Tab","Q","W","E","R","T","Y","U","I","O","P","{ [","} ]",{w:1.5},"|",{x:0.25},"Delete","End","PgDn",{x:0.25},"7 Home","8 ↑","9 PgUp",{h:2},"+"],
[{w:1.75},"Caps Lock","A","S","D","F","G","H","J","K","L",": ;","'",{w:2.25},"Enter",{x:3.5},"4 ←","5","6 →"],
[{w:2.25},"Shift","Z","X","C","V","B","N","M","< ,","> .","? /",{w:2.75},"Shift",{x:1.25},"↑",{x:1.25},"1 End","2 ↓","3 PgDn",{h:2},"Enter"],
[{w:1.25},"Ctrl",{w:1.25},"Win",{w:1.25},"Alt",{a:7,w:6.25},"",{a:4,w:1.25},"Alt",{w:1.25},"Win",{w:1.25},"Menu",{w:1.25},"Ctrl",{x:0.25},"←","↓","→",{x:0.25,w:2},"0 Ins",". Del"]]
"""
# LAYOUT = """
# [["A","S"],["A","S"]]
# """
INIT_X = 0
INIT_Y = 0
INIT_Z = 0

class Layout:
  def __init__(self, layout):
    self.rawLayout = layout
    self.parse()

  @classmethod
  def key_file(cls, key):
    row = int(key['y'])
    size = int(key['size'] * 100)
    if key['height'] > 1:
      if row == 2:
        return 'r2-3_200vert'
      if row > 2:
        return 'r3-4_200vert'
    return 'r{}_{}'.format(row, size)

  def parse(self):
    self.layout = []

    rows = eval(re.sub(r'([a-z]):', r'"\1":', LAYOUT))
    w = 1
    y = 1
    h = 1

    for (_y, _row) in enumerate(rows):
      row = []
      x = 1
      for key in _row:
        if isinstance(key, dict):
          if key.get('w'):
            w = float(key.get('w'))
          if key.get('h'):
            h = float(key.get('h'))
          if key.get('x'):
            x += float(key.get('x'))
          if key.get('y'):
            y += float(key.get('y'))
          continue

        parts = key.split()
        if parts:
          key = parts[0]

        rowDict = {
          'x': x,
          'y': y,
          'size': w,
          'height': int(h),
          'name': key,
        }
        rowDict['file'] = Layout.key_file(rowDict)
        row.append(rowDict)
        x = x + w
        w = 1
        h = 1

      y += 1
      self.layout.append(row)

def find_file(files, file):
  for _file in files:
    if _file.name == file:
      return _file
  return None

def find_match(files, row, size):
  match_name = 'r{}_{}'.format(row, size)
  return find_file(files, match_name)

def find_key(files, file):
  perfect_match = find_file(files, file)
  if perfect_match:
    return perfect_match

  size = file.split('_')[1]
  row = int(file.split('_')[0][1])
  if row > 4:
    row = 4

  if row >= 1:
    for i in range(row, 5):
      match = find_match(files, i, size)
      if match:
        return match

  if row <= 4:
    for i in range(1, row+1):
      match = find_match(files, i, size)
      if match:
        return match

def find_keycap_component(app, keyDef):
  design = app.activeProduct
  for occ in design.activeComponent.allOccurrences:
    if occ.component.name.startswith(keyDef['file']):
      return occ.component

def add_keycap(files, app, keyDef):
  design = app.activeProduct
  rootComp = design.rootComponent

  transform = adsk.core.Matrix3D.create()
  x = keyDef['x']-1
  if keyDef['height'] > 1:
    x += .5

  transform.translation = adsk.core.Vector3D.create(INIT_X + (1.905 * x), INIT_Y, INIT_Z + (1.905 * (keyDef['y']-1)))
  rotX = adsk.core.Matrix3D.create()
  rotX.setToRotation(2 * math.pi/4, adsk.core.Vector3D.create(1,0,0), adsk.core.Point3D.create(0,0,0))
  transform.transformBy(rotX)

  try:
    # tries to find a match first
    match = find_keycap_component(app, keyDef)
    occ = None
    if match:
      occ = rootComp.occurrences.addExistingComponent(match, transform)
    else:
      keyFile = find_key(files, keyDef['file'])
      if not keyFile:
        raise Exception('Could not find suitable file')

      occ = rootComp.occurrences.addByInsert(keyFile, transform, True)
  except:
    app.userInterface.messageBox('Could not add file: {} - {}'.format(keyDef['file'], traceback.format_exc()))

def run(context):
    start_time = time.time()
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        design = app.activeProduct
        rootComp = design.rootComponent
        comp = design.activeComponent

        keyboard = Layout(LAYOUT)

        project = app.data.activeProject
        files = project.rootFolder.dataFiles
        missing = []
        for y, row in enumerate(keyboard.layout):
            for keyDef in row:
                add_keycap(files, app, keyDef)

        # your code
        elapsed_time = time.time() - start_time
        ui.messageBox('Done in {}s'.format(int(elapsed_time)))

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# files = [
#   {'name': 'r1_125'},
#   {'name': 'r2_125'},
#   {'name': 'r3_125'},
# ]
# # print find_key(files, 'r4_125')
# print add_keycap(files, None, {'file': 'r3_125'})

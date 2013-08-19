import sys
sys.path.insert(0, '/home/gb/dev/meteor-flux')
from flux.app import fluxapp
from werkzeug.debug import DebuggedApplication
application = DebuggedApplication(fluxapp, True)

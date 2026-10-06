# The test fit's model space has three panels stacked vertically: the zone outlines (top),
# the layout (middle) and the fire egress routes (bottom). Shift the top and bottom panels
# onto the layout. The offsets are the distance between the panels in this drawing.
import pickle, json
blk=pickle.load(open('dxf_blk.pkl','rb'))
TOP_DY=-53268    # zone outlines ('thh' block) → layout
BOT_DY=55301     # egress routes ('gj' block) → layout
zones=[[(x,y+TOP_DY) for x,y in e[3]] for e in blk['thh'][1:]]   # [0] is the panel frame
routes=[[(x,y+BOT_DY) for x,y in e[3]] for e in blk['gj']]
json.dump({'zones':zones,'loop':routes},open('zones.json','w'))
print('zones',len(zones),'routes',len(routes))

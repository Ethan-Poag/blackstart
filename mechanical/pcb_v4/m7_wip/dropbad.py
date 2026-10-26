import pcbnew,sys,json
b=pcbnew.LoadBoard(sys.argv[1]);add=set(json.load(open(sys.argv[1]+'.added.json')));d=json.load(open(sys.argv[2]))
bad=set()
for v in d['violations']:
  if v['severity']=='error':
    for i in v['items']:
      if i['uuid'] in add: bad.add(i['uuid'])
n=0
for t in list(b.GetTracks()):
  if t.m_Uuid.AsString() in bad: b.Delete(t);n+=1
print('dropped',n,'of',len(add));b.Save(sys.argv[3])

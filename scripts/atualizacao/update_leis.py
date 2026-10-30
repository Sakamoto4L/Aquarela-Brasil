# update_leis.py — mescla novidades do Senado nos arquivos data/leis/*.json do site Aquarela Brasil
# uso: python3 -I update_leis.py <pasta_com_os_5_json> <novidades.json>
# novidades.json = {"lista":[[id,tipo,numero,dataassinatura,ementa,apelido],...],
#                   "det":{"<id>":[situacao,revogadaPor,observacao,classes,catalogo,mpEventos,[[idRevogado,nomeNovo],...]]}}
import json,re,sys,os,collections
D=sys.argv[1]; NV=json.load(open(sys.argv[2]))
TMAP={'LEI-n':'L','LEI-sn':'L','LCP':'LC','EMC-n':'EC','EMC-sn':'EC','EMR':'ER','LDL':'LD','DEL':'DL','DEL-mpv':'DL','MPV-ss':'MP','MPV-cs':'MP','CON-v':'CF','CON-nv':'CF','DPL-n':'DP','DPL-sn':'DP'}
TN={'L':'Lei','LC':'Lei Complementar','EC':'Emenda Constitucional','ER':'Emenda Constitucional de Revisão','LD':'Lei Delegada','DL':'Decreto-Lei','MP':'Medida Provisória','CF':'Constituição','DP':'Decreto do Poder Legislativo'}
SMALL={'de','da','do','das','dos','e','a','o','em','no','na','para','por','com'}
def tcase(s):
    out=[]
    for i,w in enumerate(s.split(' ')):
        if re.fullmatch(r'\(?[A-Z]{2,}/[A-Z]{2}\)?',w) or re.fullmatch(r'[A-Z]{2,5}',w) and w in ('PLS','PL','PLC','PLV','PEC','MPV','PLP','PDL','PLN','CD','SF','MP'): out.append(w); continue
        lw=w.lower(); out.append(lw if (i and lw in SMALL) else lw[:1].upper()+lw[1:])
    return ' '.join(out)
def autor(ob):
    m=re.match(r'\s*AUTOR(?:ES|IA)?\s*:\s*(.+)',ob or '',re.I|re.S)
    if not m: return ''
    a=re.sub(r'\s+',' ',m.group(1)).strip()
    a=re.sub(r'\b([A-Z]{2,5})\.\s*(?=\d)',r'\1 ',a)
    a=re.split(r'\s+(?:OBS|NOTA)\s*:',a,flags=re.I)[0]
    a=re.split(r'\.\s',a)[0].strip().rstrip('.').strip()
    parts=[x.strip() for x in re.split(r'\s+-\s+',a) if x.strip()]
    who=[]; refs=[]
    for x in parts:
        r=re.fullmatch(r'([A-Z]{2,5})\.?\s*(\d+)\s*(?:/|DE)\s*(\d{4})\.?',x,re.I)
        if r: refs.append(f'{r.group(1).upper()} {r.group(2)}/{r.group(3)}')
        else: who.append(x)
    w=' - '.join(who)
    w=re.sub(r'\s+',' ',w)
    if re.fullmatch(r'(PODER )?EXECUTIVO',w,re.I): w='Poder Executivo'
    elif re.fullmatch(r'PRESIDENTE DA REP[UÚ]BLICA',w,re.I): w='Presidente da República'
    else: w=tcase(w)
    out=w+(' · origem: '+', '.join(refs) if refs else '')
    return out[:180]
def tema(cl):
    if not cl: return ''
    c=cl.split(' ;; ')[0].split(' / ')
    return c[1].strip() if len(c)>1 else ''
def mpst(mpl):
    mp=''
    for c,nm in mpl or []:
        if re.search(r'convers',c,re.I): return 'Convertida: '+nm
        if re.search(r'reedi',c,re.I) and not mp: mp='Reeditada: '+nm
        if re.search(r'rejei',c,re.I): mp='Rejeitada'
        if re.search(r'efic',c,re.I) and not mp: mp='Perdeu a eficácia'
    return mp
FILES=['leis','del','mpv','dpl']
grp=lambda t:'del' if t=='DL' else 'mpv' if t=='MP' else 'dpl' if t=='DP' else 'leis'
data={f:json.load(open(f'{D}/{f}.json')) for f in FILES}
idx={e[0]:e for f in FILES for e in data[f]}
def title(e):
    t,n,ds=e[1],e[2],e[3]
    if t=='CF': return f'Constituição de {ds[:4]}'
    if not n: return f'{TN[t]} de {ds[6:8]}/{ds[4:6]}/{ds[:4]}'
    a,_,b=str(n).partition('-'); a=f'{int(a):,}'.replace(',','.') if a.isdigit() else a
    return f'{TN[t]} nº {a}{"-"+b if b else ""}/{ds[:4]}'
novos=[]; alterados=[]; revogs=[]
for id_,tp,num,dt,em,ap in NV.get('lista',[]):
    t=TMAP.get(tp)
    if not t: continue
    id_=int(id_); dd,mm,yy=dt.split('/'); ds=yy+mm+dd
    if tp=='MPV-cs':
        m=re.match(r'MPV-(\d+)-(\d+)-',ap or ''); n=f'{m.group(1)}-{m.group(2)}' if m else (num or '')
    else: n=num or ''
    aps=' · '.join(a.strip() for a in (ap or '').split(' , ')[1:] if a.strip())
    em=re.sub(r'\s+',' ',em or '').strip()
    if id_ in idx:
        e=idx[id_]
        if e[4]!=em or e[5]!=aps: e[4]=em; e[5]=aps; alterados.append(title(e))
        continue
    e=[id_,t,n,ds,em,aps,0,'','','','',0]
    data[grp(t)].append(e); idx[id_]=e; novos.append(title(e))
for id_,X in NV.get('det',{}).items():
    e=idx.get(int(id_))
    if not e: continue
    s,rev,ob,cl,cat,mpl=X[:6]; rv=1 if (s=='R' or rev) else 0
    if rv and not e[6]: revogs.append(title(e))
    e[6]=rv; e[7]=rev or e[7] if rv else ''; e[8]=autor(ob); e[9]=tema(cl)
    if e[1]=='MP':
        st=mpst(mpl)
        if st!=e[10] and e[10]: alterados.append(title(e)+' → '+st)
        e[10]=st
    e[11]=1
    for rid,nome in (X[6] if len(X)>6 else []):
        r=idx.get(int(rid))
        if r and not r[6]: r[6]=1; r[7]=nome; revogs.append(title(r))
ap_idx=[]
for f in FILES:
    a=data[f]; a.sort(key=lambda e:(e[3],e[2]),reverse=True)
    json.dump(a,open(f'{D}/{f}.json','w'),ensure_ascii=False,separators=(',',':'))
    for e in a:
        if e[5]: ap_idx.append([e[0],e[1],e[2],e[3],e[5].split(' · ')[0][:90]])
json.dump(ap_idx,open(f'{D}/apelidos.json','w'),ensure_ascii=False,separators=(',',':'))
sem=[e[0] for f in FILES for e in data[f] if not e[11]]
import datetime
lim=(datetime.date.today()-datetime.timedelta(days=130)).strftime('%Y%m%d')
abertas=[e[0] for e in data['mpv'] if e[3]>=lim and not re.match(r'(Convertida|Rejeitada|Perdeu)',e[10] or '')]
json.dump({'sem_situacao':sem,'mp_abertas':abertas},open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])),'pendentes.json'),'w'))
print(json.dumps({'novos':novos,'revogadas_agora':sorted(set(revogs)),'alterados':alterados,'total':len(idx),'sem_situacao':len(sem),'mp_abertas':len(abertas)},ensure_ascii=False,indent=1))

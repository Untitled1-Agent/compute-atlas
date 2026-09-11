import json,re,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals'/'compute_model_data_per_gw_costs.json'
if not SOURCE.exists(): SOURCE=Path('/mnt/data/compute_model_data_per_gw_costs.json')
old=json.loads(SOURCE.read_text())
def slug(s):return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
companies=[]
# Research judgments, not investment recommendations. Numerical claims kept in source-linked records.
rows=[
('amazon','Amazon / AWS','AMZN','US','Cloud platform','#ffb36b','Custom silicon meets an anchor customer','Trainium and the Anthropic relationship make hardware choice, customer concentration and capital intensity inseparable.','A campus investment is not a full accelerator bill; customer commitments are not installed capacity.','Commissioning milestones; Trainium utilization; cash investment relative to operating cash flow.'),
('google','Alphabet / Google','GOOGL','US','Cloud platform','#7eacff','TPU scale, multiple ways to monetize','Evaluate external cloud demand alongside internal search and model workloads; a chip-equivalent scalar misses workload fit.','Tenant backstops and third-party capacity can hide outside conventional owned-PPE comparisons.','Cloud cash returns; TPU deployment milestones; uncommenced leases and guarantees.'),
('microsoft','Microsoft','MSFT','US','Cloud platform','#70d8e8','Demand can be owned; supply can be leased','Fairwater, purchased GPU services and customer contracts sit in different parts of the value chain.','Adding internal sites and outsourced supply without delivery mapping double-counts capacity.','Lease commencements; external service margins; site commissioning and cloud monetization.'),
('meta','Meta','META','US','Internal AI platform','#8d93ff','The return arrives through the product','Compute investment is principally evaluated through advertising and product economics, rather than an external cloud price.','A long-lived facility joint venture and a larger regional investment announcement need not cover the same assets.','Advertising uplift; utilization; JV guarantees and cash obligations beyond reported capex.'),
('oracle','Oracle','ORCL','US','Cloud platform','#ed8c87','Construction risk meets contracted demand','Distinguish backlog visibility from the liquidity and construction schedule needed to serve it.','Large nominal contracts do not reveal margin, annual delivery profile or future equipment-refresh costs.','Debt and lease funding; prepayments; commissioned capacity against delivery commitments.'),
('coreweave','CoreWeave','CRWV','US','GPU cloud','#abd3f3','The clearest exposure is not the simplest equity','Underwrite GPU services together with facility leases, OEM financing and customer concentration.','Contracted power, active power and utilized accelerator load describe different stages.','Cash and noncash capex; lease take-on; backlog conversion and accelerator refresh.'),
('tesla','Tesla','TSLA','US','Internal AI platform','#eab0ab','Compute is an enabling asset, not the whole thesis','Assess the infrastructure as an input to autonomy and robotics rather than as direct asset backing for the equity.','Company-wide capex cannot be assigned wholly to AI. A chart-based capacity target is not a site bill of materials.','Compute-specific disclosures; software commercialization; capex allocation.'),
('alibaba','Alibaba','BABA / 9988.HK','China','Cloud platform','#ffaf62','A local compute ecosystem with an external cloud business','Pair cloud monetization with equipment mix and domestic capital commitments; keep native-currency disclosures intact.','One observed Zhangbei campus is not the Alibaba fleet. H20 theoretical throughput is not application performance.','Cloud demand; realization of investment plans; procurement and utilization.'),
('tencent','Tencent','0700.HK','China','Internal AI / cloud','#67cfc2','Compute supports both applications and cloud','Evaluate game, advertising and enterprise uses separately; general server infrastructure is not a GPU inventory.','Designed server housing and announced investment cannot establish installed AI MW.','AI-related cash commitments; internal product returns; usable accelerator disclosures.'),
('baidu','Baidu','BIDU / 9888.HK','China','Cloud / AI platform','#869fff','Native compute measures need a precision label','Cloud and AI infrastructure may be disclosed in P or other compute units without a comparable numerical precision.','Do not convert an unspecified P figure to dense FP8 H100-equivalents.','Workload monetization; chip mix; attributable power and actual deployment.'),
('bytedance','ByteDance','Private','China','Internal AI / cloud','#70d9e0','Substantial strategic relevance; limited public granularity','Track as a private operator and potential customer, without fabricating fleet size from spending narratives.','No quantified, facility-mapped inventory is established by the attached reports.','Primary facility disclosures; ownership versus rented compute; power and hardware boundaries.'),
('huawei','Huawei','Private','China','Cloud / accelerator ecosystem','#f39782','Hardware and cloud are coupled','Ascend infrastructure connects domestic accelerator supply with cloud deployment; ecosystem maturity affects useful output.','Horinger is a modeled site estimate, not a company-wide installed fleet. Gui’an design scale is not deployed AI capacity.','Ascend deployments; software efficiency; site utilization and disclosure quality.'),
('china-mobile','China Mobile','0941.HK / 600941.SH','China','Telecom / cloud','#9fd5ed','Network infrastructure is not all AI compute','Evaluate telecom cloud capacity separately from general network assets and managed resources.','No owned-accelerator GW bridge is established in the supplied source set.','Precisely defined computing-power disclosures; AI utilization; non-AI capex separation.'),
('china-telecom','China Telecom','0728.HK / 601728.SH','China','Telecom / cloud','#a6bbe3','The unit and the ownership boundary matter','Managed computing resources and company-owned accelerator stock need separate denominators.','Do not translate aggregate cloud resources directly into owned H100-equivalents.','Resource ownership; precision; AI-only capital intensity.'),
('china-unicom','China Unicom','0762.HK / 600050.SH','China','Telecom / cloud','#d1a3b3','A capacity distributor as well as an operator','Distinguish orchestration and network access from ownership of the underlying compute.','Incomplete site disclosure should remain unknown rather than a zero or invented fleet estimate.','Operating versus managed capacity; deployed equipment; power commitments.'),
('gds','GDS','GDS / 9698.HK','China','Data-center landlord','#d6c296','Real estate economics, not an owned GPU fleet','For a landlord, utilization, contracted space and customer credit are more meaningful than an invented H100 count.','Data-center area cannot be translated to AI MW without rack density and workload information.','Leasing, utilization, construction cost and tenant concentration.'),
('vnet','VNET','VNET','China','Data-center landlord','#b8cba9','A power and leasing exposure','Analyze wholesale and retail infrastructure as infrastructure services, separately from tenant accelerators.','Facility power and utilized space are not proof of owned AI compute.','Committed versus utilized capacity; tenant economics and funding.'),
('sensetime','SenseTime','0020.HK','China','AI / compute services','#d2a4ec','Compute service capacity needs unit discipline','Separate announced computing capacity, precision and realized service revenue.','Lingang and Qianhai announcements establish identifiable projects, not a complete comparable AI fleet.','Utilization; cash conversion; clearly specified precision and equipment.'),
('xai','xAI / SpaceXAI','Private / structure not verified','US','AI operator','#d8dbec','Concentrated campus scale','Large single campuses focus commissioning, energy and workload-utilization risk.','Ownership labels in the original report are historical; no corporate restructuring is verified here.','Power delivery; hardware installation; operating evidence.'),
('openai','OpenAI','Private','US','Compute customer','#79ddb9','Demand contracts are not owned assets','Follow each demand commitment through cloud supplier, developer and facility before aggregating capacity.','The same site can appear in a developer announcement, cloud contract and model-customer program.','Delivery schedules; supplier diversification; payment structure.'),
('anthropic','Anthropic','Private','US','Compute customer','#d8b491','Multiple suppliers, overlapping milestones','Map AWS, Google and Microsoft commitments by timing and service scope, rather than sum headlines.','A future program can contain an earlier milestone. Price, term and power scope can differ.','Phased delivery; utilization; procurement concentration and overlap.'),
('qts','QTS','Private','US','Data-center landlord','#c8b084','Separate the building from its tenant','Property ownership does not imply ownership of accelerators deployed by a tenant.','Campus targets can overlap downstream cloud and model-company disclosures.','Leasing, delivered critical power and customer concentration.'),
('crusoe','Crusoe','Private','US','Developer / cloud','#a4cab3','Development is a separate layer','Connect construction and power development to cloud operators and end customers.','Abilene expansion records may overlap the Stargate campus program.','Project milestones; construction financing; contracted critical load.'),
('nebius','Nebius','NBIS','Europe','GPU cloud','#bcc7f5','Contract visibility with a capacity blind spot','A large GPU-services contract does not supply a defensible GW denominator where power is undisclosed.','Do not derive capacity from service value alone.','Commissioning; contractual capacity definitions; service economics.'),
('nscale','Nscale','Private','Europe','GPU cloud','#b7d9b3','Chip count is not installed IT power','A modeled conversion based on another site is an assumption, not an additional measured GW disclosure.','The original program-level derived power is retained as a model rather than confirmed supply.','Site-specific power; equipment generation; option exercise and delivery.'),
('iren','IREN','IREN','US','Infrastructure / GPU cloud','#d3c47f','A rare hardware and service cost bridge','Separate disclosed GPU procurement from multiyear managed-service consideration.','Hardware capex excludes some infrastructure and does not establish a full-fleet economic return.','Deployment milestones; financing; services versus equipment cost.'),
('galaxy','Galaxy','GLXY','US','Infrastructure owner','#bbade7','A landlord behind the GPU cloud','Helios links facility ownership to CoreWeave’s service business; contractual critical load differs from gross power.','Do not replace 526 MW critical IT with the 800 MW gross envelope.','Phased delivery; lease payments; facility capex and tenant risk.'),
('fluidstack','Fluidstack','Private','Europe','Compute services','#b2d2d5','A tenant and intermediary in the stack','Track facility leases and customer arrangements separately from ultimate ownership of chips.','Backstops, capacity reservations and service purchases are different obligations.','Project delivery; guarantees; pass-through power and hardware responsibilities.'),
('hut8','Hut 8','HUT','US','Infrastructure owner','#bfb18c','A lease benchmark with a third-party backstop','River Bend exposes the construction and lease layers more clearly than most bundled AI projects.','Google-linked payment support is not Alphabet-owned capex.','Delivered IT capacity; construction spend; tenant credit support.')]
for id,name,ticker,region,role,color,headline,thesis,risk,watch in rows:
 companies.append(dict(id=id,name=name,ticker=ticker,region=region,role=role,color=color,headline=headline,thesis=thesis,risk=risk,watch=watch,classification='Analyst synthesis; not a price target',sources=[]))
def company_ids(owner):
 text=owner.lower();ids=[]
 for k,words in {'amazon':['amazon','aws'],'google':['google','alphabet'],'microsoft':['microsoft'],'meta':['meta'],'oracle':['oracle'],'coreweave':['coreweave'],'tesla':['tesla'],'xai':['xai','spacexai'],'openai':['openai'],'anthropic':['anthropic'],'qts':['qts'],'crusoe':['crusoe'],'nebius':['nebius'],'nscale':['nscale'],'fluidstack':['fluidstack'],'alibaba':['alibaba'],'huawei':['huawei'],'tencent':['tencent'],'baidu':['baidu'],'sensetime':['sensetime'],'galaxy':['galaxy'],'iren':['iren'],'hut8':['hut 8']}.items():
  if any(w in text for w in words):ids.append(k)
 return ids
loc={
'Colossus 2':(35.15,-90.05,'Memphis, Tennessee','United States'),
'New Carlisle':(41.70,-86.51,'New Carlisle, Indiana','United States'),
'Fairwater Atlanta':(33.45,-84.45,'Fayetteville / Atlanta, Georgia','United States'),
'Prometheus':(40.08,-82.81,'New Albany, Ohio','United States'),
'New Albany':(40.08,-82.81,'New Albany, Ohio','United States'),
'Stargate Abilene':(32.45,-99.73,'Abilene, Texas','United States'),
'Fairwater Wisconsin':(42.71,-87.89,'Mount Pleasant, Wisconsin','United States'),
'Pryor North':(36.31,-95.32,'Pryor, Oklahoma','United States'),
'Columbus':(39.96,-83.0,'Columbus, Ohio','United States'),
'Madison':(32.46,-90.11,'Madison, Mississippi','United States'),
'Denton':(33.21,-97.13,'Denton, Texas','United States'),
'Bristow':(38.73,-77.54,'Bristow, Virginia','United States'),
'Council Bluffs East':(41.26,-95.86,'Council Bluffs, Iowa','United States'),
'Omaha':(41.26,-95.94,'Omaha, Nebraska','United States'),
'Papillion':(41.15,-96.04,'Papillion, Nebraska','United States'),
'Ridgeland':(32.43,-90.13,'Ridgeland, Mississippi','United States'),
'Goodyear':(33.44,-112.36,'Goodyear, Arizona','United States'),
'Project Osmium':(41.49,-93.77,'Cumming / West Des Moines, Iowa','United States'),
'Mesa':(33.42,-111.83,'Mesa, Arizona','United States'),
'Hillsboro 2':(45.52,-122.99,'Hillsboro, Oregon','United States'),
'Jeffersonville':(38.28,-85.74,'Jeffersonville, Indiana','United States'),
'Rosemount':(44.74,-93.13,'Rosemount, Minnesota','United States'),
'Storey':(39.54,-119.43,'Storey County, Nevada','United States'),
'The Dalles':(45.60,-121.18,'The Dalles, Oregon','United States'),
'Montgomery':(32.37,-86.30,'Montgomery, Alabama','United States'),
'Cheyenne':(41.14,-104.82,'Cheyenne, Wyoming','United States'),
'Kuna':(43.49,-116.42,'Kuna, Idaho','United States'),
'Temple':(31.10,-97.34,'Temple, Texas','United States'),
'Huntsville':(34.73,-86.59,'Huntsville, Alabama','United States'),
'Aiken':(33.56,-81.72,'Aiken, South Carolina','United States'),
'Lincoln':(40.81,-96.68,'Lincoln, Nebraska','United States'),
'Lancaster':(32.59,-96.76,'Lancaster, Texas','United States'),
'Eagle Mountain':(40.31,-112.00,'Eagle Mountain, Utah','United States'),
'Helios':(33.76,-100.82,'Afton, Texas','United States'),
'Berwick':(41.05,-76.23,'Berwick, Pennsylvania','United States'),
'Kansas City East':(39.10,-94.45,'Kansas City, Missouri','United States'),
'Midlothian':(32.48,-96.99,'Midlothian, Texas','United States'),
'Waltham Cross':(51.69,-0.03,'Waltham Cross, England','United Kingdom'),
'Gallatin':(36.39,-86.45,'Gallatin, Tennessee','United States'),
'Los Lunas':(34.81,-106.73,'Los Lunas, New Mexico','United States'),
'Sarpy':(41.11,-96.11,'Sarpy County, Nebraska','United States'),
'Arcola':(38.95,-77.53,'Arcola, Virginia','United States'),
'Red Oak':(32.52,-96.80,'Red Oak, Texas','United States'),
'SAT40':(29.42,-98.49,'San Antonio, Texas','United States'),
'Batam':(1.05,104.03,'Batam','Indonesia'),
'Ellendale':(46.0,-98.53,'Ellendale, North Dakota','United States'),
'Marble':(35.17,-83.94,'Marble, North Carolina','United States'),
'New Jersey':(40.0,-74.5,'New Jersey (state-level anchor)','United States'),
'SAT14':(29.42,-98.49,'San Antonio, Texas','United States'),
'Lake Mariner':(43.36,-78.59,'Somerset, New York','United States'),
'Dalton 1 & 2':(34.77,-84.97,'Dalton, Georgia','United States'),
'QTS Atlanta':(33.75,-84.39,'Atlanta, Georgia','United States'),
'Hyperion':(32.46,-91.75,'Richland Parish, Louisiana','United States'),
'Stargate New Mexico':(34.4,-106.1,'New Mexico (state-level anchor)','United States'),
'Stargate Shackelford':(32.74,-99.35,'Shackelford County, Texas','United States'),
'Cedar Rapids':(41.98,-91.67,'Cedar Rapids, Iowa','United States'),
'Stargate UAE':(24.45,54.38,'Abu Dhabi (metro anchor)','United Arab Emirates'),
'Stargate Michigan':(43.6,-84.6,'Michigan (state-level anchor)','United States'),
'Stargate Wisconsin':(44.5,-89.5,'Wisconsin (state-level anchor)','United States'),
'Stargate Milam':(30.65,-97.0,'Milam County, Texas','United States'),
'Abilene expansion':(32.45,-99.73,'Abilene, Texas','United States'),
'Fort Wayne':(41.07,-85.14,'Fort Wayne, Indiana','United States'),
'Lordstown':(41.16,-80.85,'Lordstown, Ohio','United States'),
'Muskogee':(35.75,-95.37,'Muskogee, Oklahoma','United States'),
'Narvik':(68.44,17.43,'Narvik','Norway'),
}
sources=copy.deepcopy(old['sources'])
for s in sources:s['review']='Imported reference; not comprehensively re-verified in this app build';s['date_note']='Date preserved from original source ledger; “Current” is not a fresh verification.'
def src(id,issuer,title,url,date,use,kind='Independent site estimate'):
 sources.append(dict(id=id,issuer=issuer,title=title,url=url,date=date,use=use,category=kind,review='Source page or indexed extract reviewed during app build; source vintage retained',accessed='2026-09-11'))
base='https://epoch.ai/data/ai-data-centers/directory/'
for a in [
('N01','Anthropic–Amazon New Carlisle','anthropic-amazon-new-carlisle'),
('N02','Microsoft Fairwater Wisconsin','microsoft-fairwater-wisconsin'),
('N03','OpenAI Stargate Abilene','openai-stargate-abilene'),
('N04','CoreWeave Helios','coreweave-helios'),
('N05','Alibaba Zhangbei','alibaba-zhangbei'),
('N06','Huawei Horinger','huawei-horinger'),
('N07','Microsoft Project Osmium','microsoft-project-osmium')]:
 src(a[0],'Epoch AI',a[1],base+a[2],'2026-08-09' if a[0]=='N02' else '2026-08-10','Site-level modeled IT MW, H100e, capex, hardware and phase information; not issuer measurements.')
src('N08','Alibaba Group','Three-year AI and cloud infrastructure investment plan','https://www.alibabagroup.com/en-US/document-1830678592242057216','2025-02-24','At least RMB380B over three years; investment plan, not installed compute.','Issuer announcement')
src('N09','Shenzhen government / Shenzhen Daily','Tencent Qingyuan data center','https://www.sz.gov.cn/en_szgov/business/news/content/post_7846637.html','2020-07-06','Opening; designed room for more than one million servers, not installed accelerators.','Government publication')
src('N10','Guiyang government','Huawei cloud data center opens in Gui’an','https://www.eguizhou.gov.cn/guiyang/2021-12/22/c_7369460.htm','2021-12-22','20 December 2021 opening; eventual 1M-server design housing and design PUE 1.12, not deployed AI capacity.','Government publication')
# Correct actual supplied URL spelling.
sources[-1]['url']='https://www.eguizhou.gov.cn/guiyang/2021-12/22/c_736946.htm'
src('N11','SenseTime','Lingang computing-power and electricity collaboration','https://sensetime.com/en/news/51169885','2025-08-07','Identifiable Lingang AIDC; no comparable IT MW disclosed in this source.','Issuer announcement')
src('N12','SenseTime','Qianhai intelligent computing center','https://sensetime.com/en/news/51167435','2024-01-09','500 petaflops initial capacity; precision not established for H100 conversion.','Issuer announcement')
src('N13','Yangquan government','Baidu cloud and computing expansion','https://www.goshanxi.com.cn/yangquan/2025-12/04/c_1146650.htm','2025-12-04','7000P cluster; precision and power not provided.','Government publication')
src('N14','GDS','Second-quarter 2026 results','https://www.sec.gov/Archives/edgar/data/1526125/000110465926095498/tm2621440d1_ex99-1.htm','2026-08-13','RMB3.088B revenue and RMB1.406B adjusted EBITDA; not owned accelerator capacity.','SEC furnished results')
src('N15','GDS','Second-quarter 2026 investor results','https://investors.gds-services.com/zh-hant/node/12756','2026-08-13','79.2% utilization by area; RMB10B FY2026 capex guidance.','Issuer results')
for item in sources:
 if item['id'] in ('N12','N13'): item['access_note']='Indexed source excerpt reviewed; full-page retrieval failed in the final spot check.'
# Company identifiers are labels, not pricing feeds.
for c in companies:
 c['sources']={'amazon':['S23','S24','S26','N01'],'google':['S20','S21','S22','S49'],'microsoft':['S12','S17','S18','N02'],'meta':['S27','S28','S29'],'oracle':['S31','S32','S33','N03'],'coreweave':['S37','S38','S42','N04'],'tesla':['S47'],'alibaba':['N05','N08'],'tencent':['N09'],'baidu':['N13'],'huawei':['N06','N10'],'gds':['N14','N15'],'sensetime':['N11','N12'],'xai':['S01'],'openai':['S33','S34'],'anthropic':['S21','S22','S24'],'nebius':['S18'],'nscale':['S16'],'iren':['S17'],'galaxy':['S42'],'hut8':['S49'],'fluidstack':['S49']}.get(c['id'],[])
 c['commitment']=next((v for v in old['commitments'] if c['id'] in company_ids(v['company'])),None)
 c['stock']=next((v for v in old['stock_rows'] if c['id'] in company_ids(v['company'])),None)
 c['legacy_summary']=next((v for v in old['company_summary'] if c['id'] in company_ids(v['company'])),None)
 c['facts']=[]
 if c['id']=='alibaba':c['facts']=[dict(label='Announced AI/cloud investment plan',value='≥ RMB380B / 3 years',date='2025-02-24',sources=['N08'],note='Plan, not a firm delivered GW inventory.')]
 if c['id']=='gds':c['facts']=[dict(label='Q2 revenue / adjusted EBITDA',value='RMB3.088B / RMB1.406B',date='2026-08-13',sources=['N14'],note='Reported quarterly metrics; adjusted EBITDA is non-GAAP.'),dict(label='Area utilization / FY2026 capex guidance',value='79.2% / RMB10B',date='2026-08-13',sources=['N15'],note='Floor-area measure; cannot convert to owned GPU power.')]
sites={}
for kind,key in [('snapshot','current_sites'),('target','planned_sites')]:
 for i,r in enumerate(old[key]):
  ids=company_ids(r['owner']); sid=slug(r['owner']+' '+r['site'])
  if sid not in sites:
   ll=loc.get(r['site']);sites[sid]=dict(id=sid,name=r['site'],owner_label=r['owner'],company_ids=ids,primary_company=ids[0] if ids else None,country=ll[3] if ll else ('Norway' if r['site']=='Norway' else 'Location not resolved'),location=ll[2] if ll else 'Location not resolved; not mapped',lat=ll[0] if ll else None,lon=ll[1] if ll else None,coordinate_precision='City / county / region anchor, manually assigned from the name; not a surveyed site coordinate' if ll else 'Unresolved',review='archive',sources=['S01','S02'],snapshot=None,target=None,raw=[],hardware=[],timeline=[],facts=[],caveats=['Original report site estimates are not operator-confirmed measurements. A modeled replacement cost is not disclosed historical project spending.'],roles=[dict(role='Original ownership label',entity=r['owner'],basis='Imported from report; hardware and property ownership may differ.')])
  s=sites[sid];s['raw'].append(dict(table=key,row=i+1,data=r))
  s[kind]=dict(it_mw=r.get('it_mw',r.get('target_it_mw')),h100e_k=r.get('h100e_k',r.get('target_h100e_k')),cost_b=r['modeled_cost_b'],date='2026-08-31' if kind=='snapshot' else None,evidence='Imported independent estimate; not re-verified',sources=['S01','S02'])
  if kind=='target':s['caveats'].append('Target is an end-state, not automatically incremental, contracted or available. Phase timing and IT/gross boundary need verification.')
# Merge labels only where same site and hardware owner clear; no cross-owner geographical merge.
def find(name,comp=None):return next(s for s in sites.values() if s['name']==name and (not comp or comp in s['company_ids']))
def update(name,comp,source,cur,target,hardware=None,roles=None,note=None):
 s=find(name,comp);s['review']='reviewed-model';s['sources']=[source]+s['sources'];
 if cur:s['snapshot']=dict(it_mw=cur[0],h100e_k=cur[1],cost_b=cur[2],date='2026-08-10',evidence='Epoch independent modeled estimate',sources=[source])
 if target:s['target']=dict(it_mw=target[0],h100e_k=target[1],cost_b=target[2],date=target[3],evidence='Epoch projected phase; not a signed supply claim',sources=[source])
 if hardware:s['hardware']=hardware
 if roles:s['roles']=roles
 if note:s['caveats'].insert(0,note)
 return s
s=update('New Carlisle','amazon','N01',(910,686,34.5),(1925,1746,72.9,'Q1 2028'),[dict(model='Trainium2',count=1045000,basis='Epoch modeled installed inventory',sources=['N01'])],[dict(role='Hardware owner',entity='Amazon',basis='Epoch site record'),dict(role='Compute customer',entity='Anthropic',basis='Project Rainier')],'Corrected displayed target from 2,310 to 1,925 MW IT. The approximately 2.3 GW gross facility envelope is not IT load. Original row preserved.')
s['timeline']=[dict(date='2024-02-09',label='Northern land clearing',mw=None,kind='observed',sources=['N01']),dict(date='2025-06-23',label='Buildings 1–7 estimated operational',mw=398,kind='modeled',sources=['N01']),dict(date='2025-12-23',label='Expanded estimated operation',mw=626,kind='modeled',sources=['N01']),dict(date='2026-03-23',label='Buildings 12–16 estimated operational',mw=910,kind='modeled',sources=['N01']),dict(date='2026-10-19',label='Projected phase',mw=1037,kind='projected',sources=['N01']),dict(date='2028-03-17',label='Projected expanded end-state',mw=1925,kind='projected',sources=['N01'])]
s=update('Fairwater Wisconsin','microsoft','N02',(369,446,14.0),(2263,4528,85.7,'Q2 2028'),[dict(model='NVIDIA B200',count=176400,basis='Epoch model; not an issuer GPU inventory',sources=['N02'])],note='Corrected the displayed projected IT boundary from 2,715 to 2,263 MW. The original row is retained for audit. Source served update: Aug. 9, 2026.')
s['snapshot']['date']='2026-08-09'
s=update('Stargate Abilene','oracle','N03',(421,509,15.9),(843,1019,31.9,'Q4 2026'),[dict(model='NVIDIA B200',count=100800,basis='Epoch estimate',sources=['N03']),dict(model='NVIDIA B300',count=100800,basis='Epoch estimate',sources=['N03'])],[dict(role='Hardware owner / cloud supplier',entity='Oracle',basis='Epoch site record'),dict(role='Compute customer',entity='OpenAI',basis='Stargate'),dict(role='Developer',entity='Crusoe',basis='Original report')],'843 MW IT is the source’s Q4 2026 modeled phase. It is not proof that the original 1,180 MW longer-range record describes the same boundary or date.')
s['company_ids'].append('crusoe')
s=update('Helios','coreweave','N04',(132,160,5.0),(528,638,20.0,'Q1 2029'),[dict(model='NVIDIA B200',count=63200,basis='Epoch model',sources=['N04'])],[dict(role='Facility owner',entity='Galaxy',basis='S42'),dict(role='Hardware owner / cloud operator',entity='CoreWeave',basis='N04'),dict(role='Potential customer',entity='OpenAI',basis='Speculative attribution, not established')],'Do not call the 800 MW gross envelope IT capacity. Preserve 526 MW contracted critical IT (S42) separately from the 528 MW engineering-model projection (N04).')
s['company_ids'].append('galaxy');s['sources'].append('S42');s['facts'].append(dict(label='Contract power boundary',value='526 MW critical IT / 800 MW gross',sources=['S42'],note='Imported Galaxy counterparty disclosure, not active power.'))
s=update('Project Osmium','microsoft','N07',(190,156,7.2),None,[dict(model='NVIDIA A100',count=25000,basis='Epoch estimate',sources=['N07']),dict(model='NVIDIA H100',count=32700,basis='Epoch estimate',sources=['N07']),dict(model='NVIDIA B200',count=45500,basis='Epoch estimate',sources=['N07'])],note='Location anchor corrected to Cumming / West Des Moines, Iowa. The source headline is rounded to 156k H100e; its hardware table is rounded to 155k. OpenAI usage is speculative.')
s['timeline']=[dict(date='2021-01-01',label='First modeled operating phase',mw=48,kind='modeled',sources=['N07']),dict(date='2023-06-30',label='Second modeled phase',mw=95,kind='modeled',sources=['N07']),dict(date='2025-03-01',label='Four-building modeled phase',mw=190,kind='modeled',sources=['N07']),dict(date='2026-06-16',label='No notable changes observed in the source',mw=190,kind='modeled',sources=['N07'])]
find('Abilene expansion')['caveats'].insert(0,'Potential overlap with Stargate Abilene. This separate developer record must not be added to the Oracle / OpenAI record without phase reconciliation.')

def addsite(name,comp,location,lat,lon,sources_,snapshot=None,hardware=None,facts=None,timeline=None):
 id=slug(comp+' '+name);c=next(c for c in companies if c['id']==comp)
 sites[id]=dict(id=id,name=name,owner_label=c['name'],company_ids=[comp],primary_company=comp,country='China',location=location,lat=lat,lon=lon,coordinate_precision='City / district anchor only; not a surveyed campus coordinate',review='reviewed-model' if snapshot else 'primary-noncomparable',sources=sources_,snapshot=dict(it_mw=snapshot[0],h100e_k=snapshot[1],cost_b=snapshot[2],date='2026-08-10',evidence='Epoch independent site model',sources=sources_) if snapshot else None,target=None,raw=[],hardware=hardware or [],facts=facts or [],timeline=timeline or [],roles=[dict(role='Associated company',entity=c['name'],basis='Linked source; scope in the source controls')],caveats=['A named facility is not the company fleet. Unknown AI MW remains unknown; server housing, floor area and unspecified computing units are not converted to H100-equivalents.'])
 return sites[id]
addsite('Zhangbei','alibaba','Zhangbei, Hebei',41.15,114.70,['N05'],(169,32,6.4),[dict(model='NVIDIA H20',count=213200,basis='Epoch estimate',sources=['N05'])],timeline=[dict(date='2025-09-17',label='First modeled operating phase',mw=85,kind='modeled',sources=['N05']),dict(date='2026-01-03',label='Expanded modeled phase',mw=169,kind='modeled',sources=['N05'])])
addsite('Horinger','huawei','Horinger / Hohhot, Inner Mongolia',40.38,111.82,['N06'],(242,117,9.2),[dict(model='Ascend 910C',count=154700,basis='Epoch estimate; headline H100e rounded differently from hardware table',sources=['N06'])],timeline=[dict(date='2025-06-01',label='Modeled phase',mw=48,kind='modeled',sources=['N06']),dict(date='2026-02-01',label='Modeled phase',mw=150,kind='modeled',sources=['N06'])])
addsite('Qingyuan','tencent','Qingyuan, Guangdong',23.68,113.05,['N09'],facts=[dict(label='Designed server housing',value='More than 1 million servers',sources=['N09'],note='2020 opening report; design capacity, not installed GPUs or current operating power.')])
addsite('Gui’an cloud data center','huawei','Gui’an New Area, Guizhou',26.40,106.47,['N10'],facts=[dict(label='Opening',value='20 December 2021',sources=['N10'],note='Historical commissioning date, not a measurement of current AI MW.'),dict(label='Eventual design housing',value='1 million servers',sources=['N10'],note='Planned eventual server housing; not a deployed GPU inventory.'),dict(label='Design PUE',value='1.12',sources=['N10'],note='Design claim in the 2021 source; not a verified current measured operating PUE.')])
addsite('Lingang AIDC','sensetime','Lingang, Shanghai',30.88,121.92,['N11'],facts=[dict(label='Project evidence',value='August 2025 collaboration',sources=['N11'],note='Identifies the facility; power and installed H100-equivalents not supplied.')])
addsite('Qianhai intelligent computing center','sensetime','Qianhai, Shenzhen',22.53,113.89,['N12'],facts=[dict(label='Initial computing capacity',value='500 petaflops',sources=['N12'],note='Precision unspecified in the cited announcement. No H100 conversion applied.')])
addsite('Yangquan cloud center','baidu','Yangquan, Shanxi',37.86,113.58,['N13'],facts=[dict(label='Announced specialized cluster',value='7,000P',sources=['N13'],note='December 2025 expansion description. Precision and power unspecified; not converted.')])
# Supplemental named facilities from contract footnotes; power refers to contracts, not operating estimate.
s=addsite('River Bend','hut8','Louisiana (state-level anchor)',31.1,-91.8,['S49']);s['country']='United States';s['company_ids']=['hut8','fluidstack','google'];s['review']='contract-record';s['facts']=[dict(label='Contracted critical IT load',value='245 MW',sources=['S49'],note='330 MW gross envelope; 15-year lease, not evidence of active power.'),dict(label='Base lease value',value='$7B / 15 years',sources=['S49'],note='Nominal; power/hardware scope must be retained.')];s['roles']=[dict(role='Facility provider',entity='Hut 8',basis='S49'),dict(role='Tenant',entity='Fluidstack',basis='S49'),dict(role='Payment backstop',entity='Google-linked',basis='S49; not direct ownership')]
# Original Tesla lacks a source row per physical facility. Keep unlocated campus-level note, not invented coordinates.
sites['tesla-undisclosed-clusters']=dict(id='tesla-undisclosed-clusters',name='AI clusters — location not reconciled',owner_label='Tesla',company_ids=['tesla'],primary_company='tesla',country='Location not resolved',location='Not geolocated in this dataset',lat=None,lon=None,coordinate_precision='Unresolved',review='archive',sources=['S47'],snapshot=None,target=None,raw=[],hardware=[],timeline=[],facts=[dict(label='Original report company-level floor',value='>205 MW',sources=['S47'],note='Not allocated to a verified facility; excluded from site power comparisons.')],roles=[dict(role='Company',entity='Tesla',basis='Original report')],caveats=['The historical report’s company-level cluster figure is not a geolocated facility disclosure. The map does not invent a Texas campus allocation.'])
# Keep all source report records in structured form, with corrected views separate from raw tables.
contracts=[]
for i,r in enumerate(old['signed_capacity']):
 c=copy.deepcopy(r);c.update(id='deal-'+str(i+1),company_ids=company_ids(r['vendor']+' '+r['counterparty']),review='Imported report disclosure; scope cautions apply',raw=copy.deepcopy(r));contracts.append(c)
costs=[]
for i,r in enumerate(old['contract_costs']):
 c=copy.deepcopy(r);c['id']='cost-'+str(i+1);c['company_ids']=company_ids(r['benchmark']);c['review']='Imported benchmark; not newly re-underwritten';costs.append(c)
corrections=[
 dict(id='C01',title='A modeled fleet is not confirmed installed compute',impact='High',before='max(named-site sum, modeled chip-owner IT, disclosed active power)',after='Removed as an operating-fleet total. No complete-fleet ranking in the app.',why='Delivered chips, estimated site power and operational service power have different dates and boundaries.',sources=['S01','S04','S05']),
 dict(id='C02',title='New Carlisle: gross power versus IT power',impact='High',before='2,310 MW described as target IT',after='1,925 MW projected IT, Q1 2028; retain original raw row.',why='The served site record distinguishes approximately 2.3 GW total facility power.',sources=['N01']),
 dict(id='C03',title='Fairwater Wisconsin: target IT boundary',impact='High',before='2,715 MW target IT',after='2,263 MW projected IT, Q2 2028.',why='Use the dated site-level modeled IT phase, not the larger gross envelope.',sources=['N02']),
 dict(id='C04',title='Abilene: different phases are not interchangeable',impact='High',before='1,180 MW target without a phase date',after='843 MW projected IT, Q4 2026, displayed; historical target kept separately.',why='A near-term phase is not evidence that all later campus plans have been canceled.',sources=['N03']),
 dict(id='C05',title='Helios: 800 gross ≠ 800 IT',impact='High',before='800 MW labeled target IT',after='526 MW contracted critical IT; 528 MW engineering projection for Q1 2029.',why='Contracted critical power and an engineering estimate are separate, while neither equals gross power.',sources=['N04','S42']),
 dict(id='C06',title='No silent PUE normalization of Amazon campus cost',impact='High',before='$7.81B/IT-GW from an assumed 1.25 PUE',after='$6.25B per disclosed GW; IT-GW cost unknown from that announcement alone.',why='$15B / 2.4 GW has a defensible arithmetic result but not an established full-stack IT boundary.',sources=['S26']),
 dict(id='C07',title='Reference-stack costs are not actual company costs',impact='High',before='Company tables repeated $37.883B/IT-GW as comparable capex',after='Common reference model confined to the scenario lab; observed layers shown separately.',why='A replacement-cost convention is neither an observed procurement quote nor equity asset backing.',sources=['S03']),
 dict(id='C08',title='Archived prices are not live quotes',impact='High',before='Historical 2026-08-31 values available without a current feed',after='Historical market card explicitly unverified; valuation assumptions are user-editable.',why='The finance:// reference cannot be independently opened as a conventional source URL.',sources=['S48']),
 dict(id='C09',title='China: unknown is not zero',impact='High',before='Absent from original source workbook',after='Eleven Chinese companies; seven named facilities and native-unit records.',why='Floor area, server housing and unspecified P computing measures cannot establish owned H100-equivalent GW.',sources=['N05','N06','N08','N09','N12','N13','N14']),
 dict(id='C10',title='Names are not exact coordinates',impact='Medium',before='No source-level coordinate registry in the supplied reports',after='City / county / state cartographic anchors with an explicit accuracy warning; unresolved sites remain in the list.',why='Useful geographic exploration must not imply a surveyed facility position.',sources=['N01','N02','N07']),
 dict(id='C11',title='Avoid inferred customer and landlord ownership',impact='High',before='Combined company labels on site and program records',after='Explicit hardware owner, property owner, customer and backstop roles where supported.',why='The same underlying campus may appear several times along the contracting chain.',sources=['S17','S18','S42','S49']),
]
D=dict(meta=dict(name='Compute Atlas',version='3.0',built='2026-09-11',snapshot='Source vintages vary; see each record',coverage='A research collection, not a census of globally available compute',geo='Approximate cartographic anchors only',market='Original 2026-08-31 snapshot, not a live verified feed',license='Original model supplied in this conversation; Epoch AI CC BY attribution; Natural Earth public-domain cartography.'),companies=companies,sites=list(sites.values()),sources=sources,contracts=contracts,costs=costs,direct_costs=old['direct_company_cost_evidence'],normalization=old['normalization'],commitments=old['commitments'],cost_model=old['cost_model_assumptions'],corrections=corrections,legacy_keys=list(old.keys()),manifest=json.load(open(ROOT/'data/manifest.json')))
(ROOT/'data/atlas.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
print('Companies',len(companies),'China',sum(c['region']=='China' for c in companies),'Sites',len(sites),'mapped',sum(s['lat'] is not None for s in sites.values()),'sources',len(sources))

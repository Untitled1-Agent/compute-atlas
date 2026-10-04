import json
from pathlib import Path
path=Path('data/evidence.json')
d=json.loads(path.read_text())
assert not any(s['id']=='P13' for s in d['sources'])
def source(sid,publisher,title,url,date):
    d['sources'].append(dict(id=sid,publisher=publisher,title=title,url=url,published_at=date,retrieved_at='2026-10-04',kind='primary',review_status='reviewed',refresh_hours=24,rights='Linked primary disclosure; source copyright retained. No source imagery redistributed.'))
source('P13','Applied Digital','Polaris Forge 1: July commissioned subtotal','https://ir.applieddigital.com/news-events/press-releases/detail/157/applied-digital-delivers-second-building-at-polaris-forge-1','2026-07-01')
source('P14','Applied Digital','Polaris Forge 1: October Building 2 completion','https://ir.applieddigital.com/news-events/press-releases/detail/161/applied-digital-brings-an-additional-75-mw-of-ai','2026-10-02')
source('P15','Hut 8 / SEC EDGAR','River Bend transaction presentation, slides 5–8','https://www.sec.gov/Archives/edgar/data/1964789/000110465925122052/hut-20251217xex99d2.htm','2025-12-17')
source('P16','OpenAI','Stargate UAE announcement','https://openai.com/index/introducing-stargate-uae/','2025-05-22')
source('P17','Meta','Nuclear agreements: grid context for Prometheus','https://about.fb.com/news/2026/01/meta-nuclear-energy-projects-power-american-ai-leadership/','2026-01-09')
source('P18','SenseTime','Lingang AIDC energy management disclosure','https://sensetime.com/en/news/51169885','2025-08-07')
dates={s['id']:s['published_at'] for s in d['sources']}
def obs(cid,site,source,value,boundary,status,scope,qualifier,*,metric='power',unit='MW',period=None,supersedes=None,comparison='stated'):
    d['observations'].append(dict(id=cid,site_id=site,source_id=source,metric=metric,value=value,unit=unit,boundary=boundary,status=status,scope=scope,qualifier=qualifier,as_of=dates[source],period=period,supersedes=supersedes,review_status='accepted',confidence='primary_reported',comparison=comparison))
def fact(cid,site,source,label,value,qualifier=''):
    d['facts'].append(dict(id=cid,site_id=site,source_id=source,label=label,value=value,qualifier=qualifier,as_of=dates[source],review_status='accepted',confidence='primary_reported'))
def rel(cid,site,source,company,role,status='disclosed'):
    d['relationships'].append(dict(id=cid,site_id=site,source_id=source,company_id=company,role=role,status=status,as_of=dates[source],review_status='accepted',confidence='primary_reported'))
site='coreweave-ellendale'
obs('ellendale-live-july',site,'P13',175,'critical_it','operating','Campus commissioned subtotal','July disclosure, replaced by October subtotal. Never add the two snapshots.')
obs('ellendale-live-october',site,'P14',250,'critical_it','operating','Campus commissioned subtotal','Issuer-reported commissioned capacity, not measured utilization.',supersedes='ellendale-live-july')
obs('ellendale-building2-it',site,'P14',150,'critical_it','delivered','Building 2 completed','Included within the 250 MW campus subtotal; not additional campus capacity.')
obs('ellendale-contracted-it',site,'P14',400,'critical_it','contracted','Full campus buildout','Includes delivered phases; not 400 MW of additional operating power.')
fact('ellendale-identity',site,'P14','Campus identity','Polaris Forge 1 · Ellendale, North Dakota')
fact('ellendale-developer',site,'P14','Developer / owner','Applied Digital','No new exact location or building footprint established by this release.')
site='hut8-river-bend'
obs('riverbend-contract-it',site,'P15',245,'critical_it','contracted','Base-term colocation lease','Contracted IT, not evidence of commissioning.',period='Initial delivery targeted Q2 2027')
obs('riverbend-utility',site,'P15',330,'utility_capacity','planned','Initial utility supply','Utility allocation, not IT load or measured consumption. December 2025 delivery expectation.',period='Expected availability July 2026')
obs('riverbend-lease-term',site,'P15',15,'contract_term','contracted','Base lease term','Three optional five-year renewals are excluded.',metric='lease_term',unit='years')
obs('riverbend-lease-value',site,'P15',7,'base_lease_value','contracted','Base-term lease value','USD billions of contractual revenue over the base term, not construction cost or present value.',metric='lease_value',unit='USD billion')
obs('riverbend-owned-acres',site,'P15',627,'site_area','disclosed','Owned land','Excludes land under option; no surveyed boundary imported.',metric='land_area',unit='acres')
fact('riverbend-place',site,'P15','Site locality','West Feliciana Parish, Louisiana','The archive anchor remains approximate; not a parcel pin.')
fact('riverbend-timing',site,'P15','Initial delivery target','Q2 2027','A December 2025 expectation, not confirmed completion.')
fact('riverbend-power-provider',site,'P15','Utility context','Entergy Louisiana','No utility line geometry is inferred from this disclosure.')
rel('riverbend-hut8-developer',site,'P15','hut8','Developer / landlord')
rel('riverbend-fluidstack-tenant',site,'P15','fluidstack','Colocation tenant','contracted')
rel('riverbend-google-backstop',site,'P15','google','Lease-payment financial backstop','contracted')
site='openai-stargate-uae'
obs('uae-announced-cluster',site,'P16',1000,'unspecified_compute','announced','Full Stargate UAE cluster','Source says 1 GW; converted to MW only. IT versus gross boundary is not specified.')
obs('uae-initial-tranche',site,'P16',200,'unspecified_compute','planned','Initial tranche','A 2025 expectation, not a verified 2026 commissioning event. Included in the cluster target.',period='2026 expected')
fact('uae-place',site,'P16','Announced location','Abu Dhabi, United Arab Emirates','No parcel geometry or precise campus coordinates disclosed.')
rel('uae-openai-partner',site,'P16','openai','Announced project partner','announced')
rel('uae-oracle-partner',site,'P16','oracle','Announced project partner','announced')
site='meta-prometheus'
obs('prometheus-it-undisclosed',site,'P17',None,'critical_it','not_disclosed','Site operating IT','This grid-supply announcement does not quantify site IT capacity; archive models remain separate.')
fact('prometheus-location',site,'P17','Named location','New Albany, Ohio')
fact('prometheus-nuclear-context',site,'P17','Grid supply context','Nuclear agreements support grids serving Meta operations, including Prometheus','Up to 6.6 GW concerns several generation projects through 2035, not this campus IT load. Article also bears a January 12 update date.')
rel('prometheus-meta-role',site,'P17','meta','Named supercluster operator')
site='sensetime-lingang-aidc'
obs('lingang-reported-pue',site,'P18',1.28,'annual_pue','disclosed','Reported annual PUE','Issuer-reported upper bound; measurement year and independent verification are not provided.',metric='pue',unit='ratio',period='Annual period not identified',comparison='lt')
obs('lingang-energy-saving',site,'P18',3000000,'reported_energy_savings','disclosed','Annual electricity saving','Issuer-reported annual energy saving. Not IT capacity; no MW or GPU conversion.',metric='energy_savings',unit='kWh/year',period='Annual period not identified')
fact('lingang-platform',site,'P18','Energy management platform','SenseCore with DaMao AI and CATL Capital','Disclosed pilot at Lingang AIDC; not a fleet-wide performance guarantee.')
rel('lingang-sensetime-role',site,'P18','sensetime','AIDC operator / SenseCore platform')
d['published_at']='2026-10-04'
old=next(x for x in d['observations'] if x['id']=='ellendale-live-july')
d['observations'].remove(old)
d.setdefault('revision_history',{})['observations']=[old]
path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

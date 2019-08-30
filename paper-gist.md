```
import readline
for i in range(readline.get_current_history_length()):
    print(readline.get_history_item(i + 1))
```

# Effective case count
```
print(f'''all_cases_count = list(grip.O.query().V().hasLabel('Case').count())
ccle_program_ids = list(grip.O.query().V().hasLabel('Program').has(gripql.within("program_id", ['CTRP', 'GDSC', 'CCLE'])).render('_gid'))
ccle_project_ids = list(grip.O.query().V(program_ids).out('projects').render('_gid'))
ccle_case_ids = list(grip.O.query().V(ccle_project_ids).out('cases').render('_gid'))
unique_ccle_cell_lines = set([c.split(':')[2] for c in ccle_case_ids])

effective_patient_count = all_cases_count - len(ccle_case_ids) + len(unique_ccle_cell_lines)

{effective_patient_count} = {all_cases_count} - {len(ccle_case_ids)} + {len(unique_ccle_cell_lines)}
''')
```

# CCLE case dedupes

```
# cell lines to check for
cell_line_names = ['CTRP', 'GDSC', 'CCLE']
# projects with those cell lines
project_gids = [project_gid for project_gid in list(grip.O.query().V().hasLabel('Project').render('_gid')) if any(n in project_gid for n in cell_line_names) ]
# cases in those projects
case_gids = list(grip.O.query().V(project_gids).as_("p").outE('cases').render(['$p._gid', '_to']))
# de-dupe
unique_cell_lines = set([c[1].split(':')[2] for c in case_gids])

same_as_gids = list(grip.O.query().V([c[1] for c in case_gids]).as_("c").outE('same_as').render(['$c._gid', '_to']))

def allele_count(case_gids):
  return list(grip.O.query().V(case_gids).out('samples').out('aliquots').out('somatic_callsets').out('alleles').count())[0].count

def drug_response_count(case_gids):
  return list(grip.O.query().V(case_gids).out('samples').out('aliquots').out('drug_response').count())[0].count


report = {}

for cell_line_name in cell_line_names:
    cell_line_projects = [p for p in project_gids if cell_line_name in p]
    for p in cell_line_projects:
        if cell_line_name not in report:
            report[cell_line_name] = {}
        if p not in report[cell_line_name]:
            report[cell_line_name][p] = {'cases': [c[1] for c in case_gids if p == c[0]]}
            report[cell_line_name][p]['allele_count'] = allele_count(report[cell_line_name][p]['cases'])
            report[cell_line_name][p]['drug_response_count'] = drug_response_count(report[cell_line_name][p]['cases'])



for cell_line_name, projects in report.items():
  case_count = 0
  allele_count = 0
  cases = []
  drug_response_count = 0
  same_as_count = defaultdict(int)
  for project_id, project in projects.items():
    case_count += len(project['cases'])
    allele_count += project['allele_count']
    drug_response_count += project['drug_response_count']
    cases.extend(project['cases'])
    for c in project['cases']:
      for same_as in same_as_gids:
        if c == same_as[0]:
          # get project out of case
          same_as_count[same_as[1].split(':')[1]] += 1
  unique_cases = set([c.split(':')[2] for c in cases])
  print(f'{cell_line_name}, project_count: {len(projects.keys())}, case_count: {case_count}, unique_cases:{len(unique_cases)}, drug_response_count: {drug_response_count}, allele_count: {allele_count}, same_as_count: {same_as_count.items()}')


ccle_cases = [item for sublist in  [p['cases'] for p in [p for p in report['CCLE'].values()]]    for item in sublist]

def allele_count(case_gids):
  c = defaultdict(int)
  l = list(grip.O.query().V(case_gids).as_('c').out('samples').out('aliquots').out('somatic_callsets').out('alleles').as_('a').render(['$c._gid', '$a._gid']))
  for t in l:
    c[t[0]] += 1
  return c

def drug_response_count(case_gids):
  c = defaultdict(int)
  l = list(grip.O.query().V(case_gids).as_('c').out('samples').out('aliquots').out('drug_response').as_('r').render(['$c._gid', '$r._gid']))
  for t in l:
    c[t[0]] += 1
  return c

ccle_allele_counts = allele_count(ccle_cases)
ccle_drug_response_counts = drug_response_count(ccle_cases)

```


# Using knowledge bases to identify potential therapy for cases

```
list(
   grip.O.query().V().hasLabel('G2PAssociation').has(gripql.eq('evidence_label', 'A'))
   .out('alleles').out('case').count()
)
>>> [<AttrDict({'count': 1476})>]



list(
  grip.O.query().V().hasLabel('G2PAssociation').has(gripql.eq('evidence_label', 'A'))
  .out('alleles')
  .count()
)
[<AttrDict({'count': 1855})>]

print(datetime.datetime.now())
list(
  grip.O.query().V().hasLabel('G2PAssociation').has(gripql.eq('evidence_label', 'A'))
  .out('alleles')
  .out('somatic_callsets')
  .out('aliquots')
  .out('samples')
  .out('case').render('_gid')
  )
print(datetime.datetime.now())  
```

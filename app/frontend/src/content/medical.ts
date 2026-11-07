// Medical content for the Learn page, CURB-65 calculator and result screen.
// Copied from docs/research/medical_content.md (Research agent, sources checked 2026-11-07).
// Do not add medical claims that are not in that file.

export interface Source {
  title: string
  publisher: string
  url: string
}

export const SOURCES = {
  whoFact: { title: 'Pneumonia fact sheet (updated 11 Nov 2022)', publisher: 'World Health Organization', url: 'https://www.who.int/news-room/fact-sheets/detail/pneumonia' },
  whoTop10: { title: 'The top 10 causes of death (2 Oct 2026)', publisher: 'World Health Organization', url: 'https://www.who.int/news-room/fact-sheets/detail/the-top-10-causes-of-death' },
  whoQuick: {
    title: 'Revised WHO classification and treatment of childhood pneumonia — quick reference guide (2014)',
    publisher: 'World Health Organization',
    url: 'https://www.childhealthtaskforce.org/sites/default/files/2019-06/Advocacy%20Package_Pneumonia%20Quick%20Reference%20Guide%28WHO%2C%202014%29_Thumbnail.pdf',
  },
  whoPocket: { title: 'Pocket Book of Hospital Care for Children, 2nd ed. (2013)', publisher: 'World Health Organization', url: 'https://www.ncbi.nlm.nih.gov/books/NBK154447/' },
  imci: { title: 'Tesfaye SH, et al. Pulse oximeter with IMCI (IMCI criteria quoted). BMJ Open 2020', publisher: 'BMJ Open', url: 'https://doi.org/10.1136/bmjopen-2020-036814' },
  cdcAbout: { title: 'About pneumonia (25 Feb 2026)', publisher: 'US Centers for Disease Control and Prevention', url: 'https://www.cdc.gov/pneumonia/about/index.html' },
  cdcRisk: { title: 'Pneumonia risk factors', publisher: 'US Centers for Disease Control and Prevention', url: 'https://www.cdc.gov/pneumonia/risk-factors/index.html' },
  cdcPrev: { title: 'Preventing pneumonia', publisher: 'US Centers for Disease Control and Prevention', url: 'https://www.cdc.gov/pneumonia/prevention/index.html' },
  nhs: { title: 'Pneumonia (reviewed 17 Jul 2026)', publisher: 'NHS (UK)', url: 'https://www.nhs.uk/conditions/pneumonia/' },
  nhlbi: { title: 'Pneumonia — Diagnosis (24 Mar 2022)', publisher: 'NHLBI, US National Institutes of Health', url: 'https://www.nhlbi.nih.gov/health/pneumonia/diagnosis' },
  india108: {
    title: 'Parliament of India reply listing 108 and 102 as National Health Mission ambulance numbers; 112 is the national emergency number',
    publisher: 'Rajya Sabha, Parliament of India',
    url: 'https://rsdebate.nic.in/bitstream/123456789/757940/1/PQ_267_04022025_U296_p534_p537.pdf',
  },
  lim2003: {
    title: 'Lim WS, et al. Defining community acquired pneumonia severity on presentation to hospital. Thorax 2003;58(5):377–382',
    publisher: 'Thorax (BMJ)',
    url: 'https://doi.org/10.1136/thorax.58.5.377',
  },
  mdcalc: { title: 'CURB-65 Score for Pneumonia Severity (BUN equivalence)', publisher: 'MDCalc', url: 'https://www.mdcalc.com/calc/324/curb-65-score-pneumonia-severity' },
  nice250: { title: 'NG250 Pneumonia: diagnosis and management (risk bands from CG191)', publisher: 'NICE (UK)', url: 'https://www.nice.org.uk/guidance/ng250/chapter/Recommendations' },
  nice110: { title: 'QS110 Quality statement on CRB65 in primary care', publisher: 'NICE (UK)', url: 'https://www.nice.org.uk/guidance/qs110' },
  rpConsolidation: { title: 'Consolidation (Gaillard F, et al.)', publisher: 'Radiopaedia', url: 'https://radiopaedia.org/articles/consolidation' },
  rpAirBronch: { title: 'Air bronchogram (Amini B, et al.)', publisher: 'Radiopaedia', url: 'https://radiopaedia.org/articles/air-bronchogram' },
  rpSilhouette: { title: 'Silhouette sign (Goel A, et al.)', publisher: 'Radiopaedia', url: 'https://radiopaedia.org/articles/silhouette-sign' },
  rpPneumonia: { title: 'Pneumonia (Hacking C, et al.)', publisher: 'Radiopaedia', url: 'https://radiopaedia.org/articles/pneumonia' },
  cherian2005: {
    title: 'Cherian T, et al. Standardized interpretation of paediatric chest radiographs. Bull World Health Organ 2005;83(5):353–359',
    publisher: 'Bulletin of the WHO',
    url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC2626240/',
  },
  hashmi2020: { title: 'Hashmi MF, et al. Diagnostics 2020;10(6):417', publisher: 'Diagnostics (MDPI)', url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC7345724/' },
  nneji2022: { title: 'Nneji GU, et al. Diagnostics 2022', publisher: 'Diagnostics (MDPI)', url: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC8870748/' },
  zech2018: {
    title: 'Zech JR, et al. Variable generalization performance of a deep learning model to detect pneumonia in chest radiographs. PLOS Medicine 2018;15(11):e1002683',
    publisher: 'PLOS Medicine',
    url: 'https://doi.org/10.1371/journal.pmed.1002683',
  },
} satisfies Record<string, Source>

export type SourceId = keyof typeof SOURCES

/* ------------------------------------------------------------------ Learn page */
export const LEARN = {
  what: {
    paragraphs: [
      'Pneumonia is an infection of the lungs. The lungs are made of tiny air sacs called alveoli. In pneumonia, these air sacs fill with pus and fluid. This makes breathing painful and lowers the amount of oxygen the body can take in.',
      'It can affect one lung or both. It can be mild, or it can be life-threatening, especially for babies, young children, older people and people with other illnesses.',
    ],
    sources: ['whoFact', 'cdcAbout'] as SourceId[],
  },
  causes: {
    rows: [
      {
        type: 'Bacteria',
        examples: 'Streptococcus pneumoniae (pneumococcus), Haemophilus influenzae type b (Hib), Mycoplasma pneumoniae, Legionella, whooping cough (pertussis)',
        note: 'In children, pneumococcus is the most common bacterial cause and Hib the second most common (WHO).',
      },
      {
        type: 'Viruses',
        examples: 'Respiratory syncytial virus (RSV), influenza (flu), COVID-19, human metapneumovirus, parainfluenza, rhinovirus; less often measles, chickenpox, adenovirus',
        note: 'RSV is the most common viral cause in children (WHO).',
      },
      {
        type: 'Fungi',
        examples: 'Pneumocystis jirovecii and others',
        note: 'Less common. Mostly affects people with a weak immune system, e.g., HIV-infected infants (WHO).',
      },
    ],
    footnote: 'Doctors cannot always find out which germ caused the infection (CDC).',
    sources: ['whoFact', 'cdcAbout'] as SourceId[],
  },
  adultSymptoms: {
    items: [
      'Cough (may bring up yellow or green mucus/phlegm)',
      'Shortness of breath',
      'High temperature (fever) or chills',
      'Chest pain, often worse when breathing or coughing',
      'Body aches and feeling very tired',
      'Loss of appetite',
      'Wheezing',
      'Confusion — common in older people',
      'Some people also have nausea, vomiting or diarrhoea',
    ],
    sources: ['nhs', 'cdcAbout'] as SourceId[],
  },
  child: {
    common: 'Cough and/or difficult breathing, with or without fever. Wheezing is more common when a virus is the cause.',
    fastBreathing: [
      { age: 'Under 2 months', limit: '60 or more breaths per minute' },
      { age: '2 to 11 months', limit: '50 or more breaths per minute' },
      { age: '1 to 5 years', limit: '40 or more breaths per minute' },
    ],
    indrawing: 'Chest indrawing: the lower chest wall pulls in when the child breathes in (instead of moving out).',
    danger: [
      'Not able to drink or breastfeed',
      'Vomiting everything',
      'Convulsions (fits)',
      'Very sleepy, hard to wake, or unconscious',
      'Stridor (a harsh noise when breathing in) while the child is calm',
      'Severe malnutrition',
      'Very sick babies may also be unable to feed, have a low body temperature, or become unconscious.',
    ],
    classification:
      'WHO classifies a child with fast breathing and/or chest indrawing as pneumonia (usually treated with oral antibiotics and home care advice by a health worker), and a child with any general danger sign as severe pneumonia (needs referral and injectable antibiotics).',
    sources: ['whoFact', 'whoQuick', 'whoPocket', 'imci'] as SourceId[],
  },
  emergency: {
    call: 'Call an ambulance (India: 108, or 112) or go to the nearest emergency department immediately if:',
    items: [
      'You are struggling to breathe — choking, gasping, unable to speak',
      'Skin, lips or tongue look pale, blue or blotchy',
      'You cough up blood',
      'You suddenly become confused',
      'A baby cannot be woken, or feels floppy',
      'A child shows any WHO danger sign',
    ],
    noDrive: 'Do not drive yourself. Ask someone to drive you, or call an ambulance.',
    sameDay:
      'See a doctor urgently (same day) if you have a cough with yellow or green phlegm, chest pain that comes and goes, feel short of breath, or are not better 2–3 days after starting antibiotics.',
    sources: ['nhs', 'whoQuick', 'india108'] as SourceId[],
  },
  risk: {
    items: [
      ['Young children', 'under 5 years, especially babies'],
      ['Older adults', '65 years and over'],
      ['People with long-term illnesses', 'heart disease, long-term lung disease, diabetes, liver disease'],
      ['People with a weak immune system', 'for example, HIV — highest risk'],
      ['People who smoke, or drink too much alcohol', ''],
      ['People who are often around sick people', ''],
      [
        'For children (WHO)',
        'malnutrition, not being exclusively breastfed, measles or HIV, smoke from cooking or heating with wood or dung, crowded homes, and parents who smoke',
      ],
    ] as [string, string][],
    sources: ['cdcRisk', 'nhs', 'whoFact'] as SourceId[],
  },
  prevention: {
    vaccines: [
      ['Pneumococcal vaccine', 'for babies, adults over 65 and people at higher risk'],
      ['Hib vaccine', 'for babies and young children'],
      ['Influenza (flu) vaccine', ''],
      ['Measles vaccine', ''],
      ['Pertussis (whooping cough) vaccine', ''],
      ['Also', 'COVID-19, RSV and chickenpox (varicella) vaccines or antibody products, where offered'],
    ] as [string, string][],
    whoNote:
      'WHO says immunisation against Hib, pneumococcus, measles and whooping cough is the most effective way to prevent pneumonia in children.',
    habits: [
      'Wash hands often with soap and water',
      'Cough or sneeze into a tissue or your elbow',
      'Do not smoke, and keep children away from cigarette smoke',
      'Use cleaner cooking stoves to reduce smoke inside the home',
      'Breastfeed babies only breast milk for the first 6 months, and give children good nutrition',
      'Keep long-term conditions such as asthma and diabetes well controlled',
      'Avoid close contact with people who are sick',
    ],
    sources: ['whoFact', 'cdcPrev', 'nhs'] as SourceId[],
  },
  diagnosis: {
    steps: [
      ['History', 'symptoms, when they started, vaccines, smoking, contact with sick people, travel.'],
      ['Physical exam', 'temperature, breathing rate, and listening to the lungs with a stethoscope.'],
      ['Chest X-ray', 'looks for inflammation in the lungs. Often used to confirm pneumonia.'],
      ['Pulse oximetry', 'a small clip on the finger or ear measures oxygen in the blood.'],
      ['Blood tests', 'e.g., complete blood count to look for infection; blood culture to find the germ.'],
      [
        'Other tests when needed',
        'sputum (phlegm) test, PCR test, arterial blood gas (very sick patients), chest CT scan, bronchoscopy, or testing fluid around the lung.',
      ],
    ] as [string, string][],
    sources: ['nhlbi', 'nhs'] as SourceId[],
  },
  homeCare: {
    items: [
      'Rest and drink plenty of fluids.',
      'Take paracetamol or ibuprofen for fever or pain only if your doctor or pharmacist says you can.',
      'If you are given antibiotics, take the full course, even if you feel better.',
      'Do not take cough medicine unless a doctor advises it — coughing helps clear the infection.',
      'Cover coughs and sneezes, wash hands, and do not smoke.',
      'Contact your doctor if you are not better after 2–3 days of antibiotics, or any time you feel worse. Go to hospital for any emergency warning sign.',
    ],
    sources: ['nhs'] as SourceId[],
  },
  stats: {
    rows: [
      { number: '740,180', fact: 'children under 5 died of pneumonia', year: '2019', source: 'whoFact' as SourceId },
      { number: '14%', fact: 'of all deaths in children under 5', year: '2019', source: 'whoFact' as SourceId },
      { number: '22%', fact: 'of deaths in children aged 1–5', year: '2019', source: 'whoFact' as SourceId },
      { number: '≈ ⅓', fact: 'of children with pneumonia get the antibiotics they need', year: '', source: 'whoFact' as SourceId },
      {
        number: '2.7 M',
        fact: 'deaths from lower respiratory infections (all ages, includes pneumonia): 4th leading cause of death worldwide',
        year: '2023',
        source: 'whoTop10' as SourceId,
      },
    ],
  },
  xray: {
    items: [
      [
        'Consolidation',
        'a white (opaque) area where air in the alveoli has been replaced by fluid or other material, such as pus in bacterial pneumonia. It hides the blood vessels and airway walls inside it. When it spreads through a whole lobe it is called lobar pneumonia.',
      ],
      ['Air bronchograms', 'dark, branching air-filled airways seen inside the white area. They are more typical of consolidation than of lung collapse.'],
      [
        'Silhouette sign',
        'when a white area touches the heart or diaphragm, the normal sharp edge disappears. Right heart border lost → right middle lobe; left heart border lost → lingula (left upper lobe); a hemidiaphragm lost → the lower lobe on that side.',
      ],
      [
        'Pleural effusion',
        'fluid in the space around the lung. The WHO standard for reading children’s X-rays counts “alveolar consolidation or pleural effusion” as primary end-point pneumonia.',
      ],
      ['Interstitial / patchy pattern', 'streaky or patchy shadows in both lungs; viral pneumonia often shows a more diffuse “interstitial” pattern.'],
    ] as [string, string][],
    remember:
      'A chest X-ray cannot tell which germ caused the pneumonia. Other conditions (heart failure, bleeding, some cancers) can also cause consolidation. Always read the X-ray with the clinical picture.',
    sources: ['rpConsolidation', 'rpAirBronch', 'rpSilhouette', 'rpPneumonia', 'cherian2005', 'hashmi2020', 'nneji2022'] as SourceId[],
  },
}

/* ------------------------------------------------------------------ CURB-65 */
export const CURB_CRITERIA = [
  { key: 'confusion', letter: 'C', name: 'Confusion', rule: 'Mental Test Score of 8 or less, or new disorientation in person, place or time' },
  { key: 'urea', letter: 'U', name: 'Urea', rule: 'Urea > 7 mmol/L (BUN > 19 mg/dL)' },
  { key: 'resp', letter: 'R', name: 'Respiratory rate', rule: 'Respiratory rate ≥ 30 /min' },
  { key: 'bp', letter: 'B', name: 'Blood pressure', rule: 'Systolic < 90 mmHg or diastolic ≤ 60 mmHg' },
  { key: 'age', letter: '65', name: 'Age', rule: 'Age ≥ 65 years' },
] as const

export type CurbKey = (typeof CURB_CRITERIA)[number]['key']

export const CURB_THRESHOLDS = { ureaMmol: 7, bunMgDl: 19, resp: 30, sbp: 90, dbp: 60, age: 65 }

export interface CurbGroup {
  scores: number[]
  group: string
  risk: 'Low' | 'Intermediate' | 'High'
  mortality: string
  care: string
  nice: string
}

/** Lim et al. 2003, Figure 2 (derivation cohort) + NICE bands. */
export const CURB65_GROUPS: CurbGroup[] = [
  { scores: [0, 1], group: 'Group 1', risk: 'Low', mortality: '1.5% (5/324)', care: 'Likely suitable for home treatment', nice: 'NICE: low risk (< 3% mortality)' },
  { scores: [2], group: 'Group 2', risk: 'Intermediate', mortality: '9.2% (17/184)', care: 'Consider hospital-supervised treatment (short-stay inpatient or hospital-supervised outpatient)', nice: 'NICE: intermediate risk (3–15% mortality)' },
  { scores: [3, 4, 5], group: 'Group 3', risk: 'High', mortality: '22% (47/210)', care: 'Manage in hospital as severe pneumonia; assess for ICU especially if score 4–5', nice: 'NICE: high risk (> 15% mortality)' },
]

/** Lim et al. 2003, Table 4: 30-day mortality per score (derivation / validation). */
export const CURB65_PER_SCORE: Record<number, { derivation: string; validation: string; care: string }> = {
  0: { derivation: '1/137 (0.7%)', validation: '0/36 (0%)', care: 'Likely suitable for home treatment' },
  1: { derivation: '4/187 (2.1%)', validation: '0/54 (0%)', care: 'Likely suitable for home treatment' },
  2: { derivation: '17/184 (9.2%)', validation: '5/60 (8.3%)', care: 'Consider hospital-supervised treatment (short-stay inpatient or hospital-supervised outpatient)' },
  3: { derivation: '20/138 (14.5%)', validation: '9/42 (21.4%)', care: 'Manage in hospital as severe pneumonia' },
  4: { derivation: '26/65 (40%)', validation: '5/19 (26.3%)', care: 'Manage in hospital as severe pneumonia; assess for ICU' },
  5: { derivation: '1/7 (14%)*', validation: '1/3 (33.3%)', care: 'Manage in hospital as severe pneumonia; assess for ICU' },
}
export const CURB65_SCORE5_NOTE =
  '*Only 7 patients scored 5; 1 died and 3 others needed mechanical ventilation in intensive care and survived (Lim et al.). The small number explains the odd percentage.'

/** Lim et al. 2003, Figure 3 + NICE CRB65 bands. */
export const CRB65_GROUPS: CurbGroup[] = [
  { scores: [0], group: 'Group 1', risk: 'Low', mortality: '1.2% (2/167)', care: 'Likely suitable for home treatment', nice: 'NICE: low risk (< 1% mortality)' },
  { scores: [1, 2], group: 'Group 2', risk: 'Intermediate', mortality: '8.15% (37/455)', care: 'Likely need hospital referral and assessment', nice: 'NICE: intermediate risk (1–10% mortality)' },
  { scores: [3, 4], group: 'Group 3', risk: 'High', mortality: '31% (30/96)', care: 'Urgent hospital admission', nice: 'NICE: high risk (> 10% mortality)' },
]

export const CURB_NOTE =
  'CURB-65 is for adults with pneumonia. Do not use it for children; for children use the WHO danger signs. Always use clinical judgement alongside the score.'
export const CURB_SOURCES: SourceId[] = ['lim2003', 'mdcalc', 'nice250', 'nice110']

/* ------------------------------------------------------------------ Result screen + disclaimer */
export const DISCLAIMER =
  'PneumoScan AI is an educational and decision-support tool, not a medical diagnosis. Its result can be wrong and must be checked by a qualified doctor, who will consider your symptoms, examination and other tests. If you feel very unwell or have trouble breathing, seek emergency care immediately.'

export const MODEL_LIMITATION =
  'The model was trained and tested on paediatric chest X-rays (ages 1–5) from a single hospital in Guangzhou, China. It may perform worse on adults, other hospitals or other X-ray machines.'

export const RESULT_TEXT = {
  PNEUMONIA: {
    headline: 'Pneumonia likely',
    explanation:
      'The model found patterns in this X-ray that it learned to associate with pneumonia. The heatmap shows the regions that most influenced this decision. This is a screening signal for a doctor to review, not a diagnosis.',
    steps: [
      'Show this result and the original X-ray to a qualified doctor. Only a doctor can confirm or rule out pneumonia.',
      'Doctors confirm pneumonia with the history, a physical exam and tests such as pulse oximetry and blood tests.',
      'For adults, the doctor may use a severity score such as CURB-65 to decide where care should happen.',
    ],
  },
  NORMAL: {
    headline: 'No pneumonia detected',
    explanation:
      'The model did not find the patterns it associates with pneumonia in this X-ray. The result can be wrong: if symptoms are present or getting worse, a doctor should still assess the patient.',
    steps: [
      'If there are symptoms such as cough, fever or shortness of breath, see a doctor anyway.',
      'See a doctor the same day for a cough with yellow or green phlegm, chest pain that comes and goes, or shortness of breath.',
    ],
  },
  urgent:
    'Call an ambulance (India: 108, or 112) for struggling to breathe, pale, blue or blotchy skin, lips or tongue, coughing up blood, or sudden confusion.',
}

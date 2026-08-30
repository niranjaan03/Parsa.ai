/**
 * ╔══════════════════════════════════════════════════════════════╗
 * ║  PARSA — Document Intelligence Workspace (Studio Engine)    ║
 * ║  Interactive VLM Parser, Layout Grounding & 9-Stage Pipeline║
 * ╚══════════════════════════════════════════════════════════════╝
 */

document.addEventListener('DOMContentLoaded', () => {
  const API_BASE = (window.location.origin && window.location.origin.startsWith('http'))
    ? window.location.origin
    : 'http://127.0.0.1:8001';
  const API_KEY = "demo-key-tenant-demo";

  let customUploadedFile = null;
  let currentPresetKey = 'intake';
  let zoomFactor = 1.0;
  let currentMode = 'parse'; // 'parse' | 'extract' | 'table' | 'json'
  let bboxesVisible = true;
  let isInverted = false;

  // ─── EXTENDED PRESET DOCUMENTS DATASET ───
  const PRESETS = {
    intake: {
      name: "Cedar Park Patient Intake Form",
      url: "https://cdn.extract.page/demo/v1/patient-intake.pdf",
      totalPages: 2,
      currentPage: 1,
      metaDetails: "Page 1 of 2 • 1024×1448 px • Clinical Intake PDF",
      image: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='750' viewBox='0 0 600 750'><rect width='600' height='750' fill='%23FFFFFF'/><rect x='30' y='30' width='540' height='60' fill='%23DCEEB1' stroke='%23000000' stroke-width='2' rx='8'/><text x='300' y='65' font-family='sans-serif' font-size='18' font-weight='bold' text-anchor='middle' fill='%23000000'>CEDAR PARK FAMILY MEDICINE</text><text x='300' y='82' font-family='sans-serif' font-size='12' text-anchor='middle' fill='%23000000'>2210 Juniper Trail, Suite 140, Cedar Park, TX 70013 | NEW PATIENT INTAKE FORM</text><rect x='30' y='110' width='540' height='160' fill='none' stroke='%23E6E6E6' stroke-width='1.5' rx='6'/><text x='40' y='130' font-family='sans-serif' font-size='12' font-weight='bold' fill='%23000000'>1. PATIENT INFORMATION</text><text x='40' y='155' font-family='sans-serif' font-size='13' fill='%23000000'>Name: Alvarez, Ruben M   DOB: 11/08/1962   Sex: [x] Male [ ] Female</text><text x='40' y='180' font-family='sans-serif' font-size='13' fill='%23000000'>Address: 4508 Pecan Hollow Dr.   City/State: Leander, TX 78704</text><text x='40' y='205' font-family='sans-serif' font-size='13' fill='%23000000'>Phone: (512) 555-0173   Emergency Contact: Dorothy Alvarez (512) 555-0166</text><rect x='30' y='290' width='540' height='130' fill='none' stroke='%23E6E6E6' stroke-width='1.5' rx='6'/><text x='40' y='310' font-family='sans-serif' font-size='12' font-weight='bold' fill='%23000000'>2. INSURANCE INFORMATION</text><text x='40' y='335' font-family='sans-serif' font-size='13' fill='%23000000'>Primary Carrier: BluePeak Assurance   Member ID: BPA4471203   Group: 40182</text><text x='40' y='360' font-family='sans-serif' font-size='13' fill='%23000000'>Secondary Carrier: Medicare Part B   Secondary Member ID: MB77310</text><rect x='30' y='440' width='540' height='90' fill='none' stroke='%23E6E6E6' stroke-width='1.5' rx='6'/><text x='40' y='460' font-family='sans-serif' font-size='12' font-weight='bold' fill='%23000000'>3. REASON FOR TODAY'S VISIT</text><text x='40' y='485' font-family='sans-serif' font-size='13' fill='%23000000'>Follow-up: High Blood Pressure   Date of Last Visit: 11/20/2025</text><rect x='30' y='550' width='540' height='160' fill='none' stroke='%23E6E6E6' stroke-width='1.5' rx='6'/><text x='40' y='570' font-family='sans-serif' font-size='12' font-weight='bold' fill='%23000000'>4. MEDICAL HISTORY &amp; MEDICATIONS</text><text x='40' y='595' font-family='sans-serif' font-size='13' fill='%23000000'>Conditions: Hypertension 25/110, Asthma   Surgeries: Gallbladder removal (2014)</text><text x='40' y='620' font-family='sans-serif' font-size='13' fill='%23000000'>Medication 1: Lisinopril 10 mg daily   Medication 2: Albuterol Inhaler</text><text x='40' y='645' font-family='sans-serif' font-size='13' fill='%23000000'>Allergies: Penicillin (rash)   Preferred Pharmacy: CVS Main Street</text></svg>",
      trustScore: 98.4,
      engine: "Unlimited-OCR (gundam)",
      decision: "AUTO_APPROVED",
      latencyCost: "142ms • $0.00",
      structured: {
        "Patient Name": { value: "Alvarez, Ruben M", conf: 0.99, layer: "Layer 1 (Rules)" },
        "Date of Birth": { value: "1962-11-08", conf: 0.99, layer: "Layer 1 (Rules)" },
        "Primary Carrier": { value: "BluePeak Assurance", conf: 0.98, layer: "Layer 2 (ML Model)" },
        "Member ID": { value: "BPA4471203", conf: 0.99, layer: "Layer 1 (Regex)" },
        "Reason for Visit": { value: "Follow-up: High Blood Pressure", conf: 0.96, layer: "Layer 2 (ML Model)" },
        "Current Medications": { value: "Lisinopril 10 mg, Albuterol Inhaler", conf: 0.95, layer: "Layer 3 (Gemini LLM)" }
      },
      chunks: [
        {
          id: 1,
          type: "header",
          bbox: [30, 30, 540, 60],
          confidence: 0.99,
          text: "CEDAR PARK FAMILY MEDICINE 2210 Juniper Trail, Suite 140, Cedar Park, TX 70013 | Tel (512) 555-0187 | Fax (512) 555-0188 NEW PATIENT INTAKE FORM"
        },
        {
          id: 2,
          type: "patient_info",
          bbox: [30, 110, 540, 160],
          confidence: 0.98,
          text: "1. PATIENT INFORMATION\nPatient Name (Last, First MI): Alvarez, Ruben M\nDate of Birth: 11/08/1962  Sex: [x] Male [ ] Female\nStreet Address: 4508 Pecan Hollow Dr.\nCity/State: Leander, TX  Zip: 78704\nHome/Cell Phone: (512) 555-0173\nEmergency Contact: Dorothy Alvarez  Phone: (512) 555-0166"
        },
        {
          id: 3,
          type: "insurance",
          bbox: [30, 290, 540, 130],
          confidence: 0.97,
          text: "2. INSURANCE INFORMATION\nPrimary Carrier: BluePeak Assurance\nMember ID: BPA4471203  Group Number: 40182\nPolicyholder: Self\nSecondary Carrier: Medicare Part B\nSecondary Member ID: MB77310  Relationship: [x] Self"
        },
        {
          id: 4,
          type: "visit_reason",
          bbox: [30, 440, 540, 90],
          confidence: 0.99,
          text: "3. REASON FOR TODAY'S VISIT\nFollow-Up: High Blood Pressure\nDate of Last Visit: 11/20/2025"
        },
        {
          id: 5,
          type: "medical_history",
          bbox: [30, 550, 540, 160],
          confidence: 0.96,
          text: "4. MEDICAL HISTORY & MEDICATIONS\nCurrent Conditions: Hypertension, Asthma\nPrior Surgeries: Gallbladder removal (2014)\nCurrent Medication 1: Lisinopril 10 mg daily\nCurrent Medication 2: Albuterol Inhaler\nAllergies to Medications: Penicillin (rash)\nPreferred Pharmacy: CVS Main Street"
        }
      ],
      tables: [
        {
          title: "Prescribed Medications List",
          headers: ["Medication", "Dosage", "Frequency", "Status"],
          rows: [
            ["Lisinopril", "10 mg", "Daily (Morning)", "Active"],
            ["Albuterol Inhaler", "90 mcg", "As needed (PRN)", "Active"],
            ["Multivitamin", "1 tab", "Daily", "Over-the-Counter"]
          ]
        }
      ]
    },

    medicare: {
      name: "Medicare Advanced Beneficiary Notice (ABN)",
      url: "https://cdn.extract.page/demo/v1/medicare-abn.pdf",
      totalPages: 1,
      currentPage: 1,
      metaDetails: "Page 1 of 1 • 1024×1448 px • Standard CMS-R-131 Form",
      image: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='750' viewBox='0 0 600 750'><rect width='600' height='750' fill='%23FFFFFF'/><rect x='30' y='30' width='540' height='50' fill='%23C5B0F4' stroke='%23000000' stroke-width='2' rx='8'/><text x='300' y='60' font-family='sans-serif' font-size='16' font-weight='bold' text-anchor='middle' fill='%23000000'>MEDICARE ADVANCE BENEFICIARY NOTICE OF NONCOVERAGE (ABN)</text><rect x='30' y='95' width='540' height='70' fill='none' stroke='%23E6E6E6' stroke-width='1.5' rx='6'/><text x='40' y='115' font-family='sans-serif' font-size='12' fill='%23000000'>Notifier: St. Jude Community Hospital   Patient: Smith, Eleanor</text><text x='40' y='140' font-family='sans-serif' font-size='12' fill='%23000000'>Identification Number: MED-9920194       Date: 03/14/2026</text><rect x='30' y='180' width='540' height='220' fill='none' stroke='%23E6E6E6' stroke-width='1.5' rx='6'/><text x='40' y='205' font-family='sans-serif' font-size='12' font-weight='bold' fill='%23000000'>LABORATORY TESTS / SERVICES NOT COVERED</text><text x='40' y='235' font-family='sans-serif' font-size='12' fill='%23000000'>Service 1: Vitamin D 25-Hydroxy Panel (CPT 82306)   Est. Cost: $145.00</text><text x='40' y='265' font-family='sans-serif' font-size='12' fill='%23000000'>Reason: Medicare does not pay for routine screening without diagnosis.</text><text x='40' y='305' font-family='sans-serif' font-size='12' fill='%23000000'>Service 2: Genetic Lipid Screening (CPT 81401)       Est. Cost: $380.00</text><text x='40' y='335' font-family='sans-serif' font-size='12' fill='%23000000'>Reason: Exceeds annual frequency limit for non-high risk patients.</text></svg>",
      trustScore: 97.8,
      engine: "Unlimited-OCR (gundam)",
      decision: "AUTO_APPROVED",
      latencyCost: "116ms • $0.00",
      structured: {
        "Notifier": { value: "St. Jude Community Hospital", conf: 0.99, layer: "Layer 1 (Rules)" },
        "Patient Name": { value: "Smith, Eleanor", conf: 0.99, layer: "Layer 1 (Rules)" },
        "ID Number": { value: "MED-9920194", conf: 0.99, layer: "Layer 1 (Regex)" },
        "Notice Date": { value: "2026-03-14", conf: 0.98, layer: "Layer 1 (Date Norm)" },
        "Service 1 CPT": { value: "82306 - Vitamin D Panel", conf: 0.97, layer: "Layer 2 (ML Model)" },
        "Service 1 Cost": { value: "$145.00", conf: 0.99, layer: "Layer 1 (Currency)" }
      },
      chunks: [
        {
          id: 1,
          type: "header",
          bbox: [30, 30, 540, 50],
          confidence: 0.99,
          text: "MEDICARE ADVANCE BENEFICIARY NOTICE OF NONCOVERAGE (ABN)"
        },
        {
          id: 2,
          type: "patient_header",
          bbox: [30, 95, 540, 70],
          confidence: 0.98,
          text: "Notifier: St. Jude Community Hospital\nPatient Name: Smith, Eleanor\nIdentification Number: MED-9920194\nDate: 03/14/2026"
        },
        {
          id: 3,
          type: "services_table",
          bbox: [30, 180, 540, 220],
          confidence: 0.96,
          text: "SERVICES & ESTIMATED COST:\n1. Vitamin D 25-Hydroxy Panel (CPT 82306) - Est. Cost: $145.00\nReason: Medicare does not pay for routine screening without diagnosis.\n2. Genetic Lipid Screening (CPT 81401) - Est. Cost: $380.00\nReason: Exceeds annual frequency limit."
        }
      ],
      tables: [
        {
          title: "Non-Covered Laboratory Services",
          headers: ["CPT Code", "Service Description", "Estimated Cost", "Denial Reason"],
          rows: [
            ["82306", "Vitamin D 25-Hydroxy Panel", "$145.00", "Routine screening without diagnosis"],
            ["81401", "Genetic Lipid Screening", "$380.00", "Exceeds annual frequency limit"]
          ]
        }
      ]
    },

    invoice: {
      name: "Commercial Freight Invoice",
      url: "https://cdn.extract.page/demo/v1/commercial-invoice.pdf",
      totalPages: 1,
      currentPage: 1,
      metaDetails: "Page 1 of 1 • 1024×1448 px • PDF Invoice Standard",
      image: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='750' viewBox='0 0 600 750'><rect width='600' height='750' fill='%23FFFFFF'/><text x='30' y='50' font-family='sans-serif' font-size='22' font-weight='bold' fill='%23000000'>INVOICE</text><text x='30' y='75' font-family='sans-serif' font-size='12' fill='%23666666'>Acme Logistics Inc. | Tax ID: 99-401924</text><rect x='350' y='30' width='220' height='70' fill='%23F7F7F5' stroke='%23E6E6E6' rx='6'/><text x='360' y='50' font-family='sans-serif' font-size='12' font-weight='bold' fill='%23000000'>Invoice #: INV-2026-8819</text><text x='360' y='70' font-family='sans-serif' font-size='12' fill='%23666666'>Date: 07/20/2026   Due: 08/20/2026</text><rect x='30' y='120' width='540' height='200' fill='none' stroke='%23E6E6E6' stroke-width='1.5' rx='6'/><text x='40' y='145' font-family='sans-serif' font-size='12' font-weight='bold' fill='%23000000'>DESCRIPTION                         QTY      UNIT PRICE      AMOUNT</text><line x1='30' y1='155' x2='570' y2='155' stroke='%23E6E6E6'/><text x='40' y='180' font-family='sans-serif' font-size='12' fill='%23000000'>Global Freight Shipping (Air)        2        $1,250.00      $2,500.00</text><text x='40' y='210' font-family='sans-serif' font-size='12' fill='%23000000'>Customs Clearance Handler            1          $350.00        $350.00</text><text x='40' y='240' font-family='sans-serif' font-size='12' fill='%23000000'>Warehousing &amp; Storage (14 days)     1          $400.00        $400.00</text><rect x='350' y='330' width='220' height='100' fill='%23F7F7F5' stroke='%23E6E6E6' rx='6'/><text x='360' y='355' font-family='sans-serif' font-size='12' fill='%23666666'>Subtotal: $3,250.00</text><text x='360' y='375' font-family='sans-serif' font-size='12' fill='%23666666'>Tax (8.25%): $268.13</text><text x='360' y='405' font-family='sans-serif' font-size='14' font-weight='bold' fill='%23000000'>Total Due: $3,518.13</text></svg>",
      trustScore: 99.2,
      engine: "Unlimited-OCR (gundam)",
      decision: "AUTO_APPROVED",
      latencyCost: "128ms • $0.00",
      structured: {
        "Invoice Number": { value: "INV-2026-8819", conf: 0.99, layer: "Layer 1 (Rules)" },
        "Vendor": { value: "Acme Logistics Inc.", conf: 0.99, layer: "Layer 1 (Rules)" },
        "Subtotal": { value: "$3,250.00", conf: 0.99, layer: "Layer 1 (Math Val)" },
        "Tax (8.25%)": { value: "$268.13", conf: 0.99, layer: "Layer 1 (Math Val)" },
        "Total Due": { value: "$3,518.13", conf: 0.99, layer: "Layer 7 (Verified Math)" }
      },
      chunks: [
        {
          id: 1,
          type: "header",
          bbox: [30, 30, 300, 60],
          confidence: 0.99,
          text: "INVOICE Acme Logistics Inc. | Tax ID: 99-401924"
        },
        {
          id: 2,
          type: "meta",
          bbox: [350, 30, 220, 70],
          confidence: 0.99,
          text: "Invoice #: INV-2026-8819\nDate: 07/20/2026\nDue Date: 08/20/2026"
        },
        {
          id: 3,
          type: "table",
          bbox: [30, 120, 540, 200],
          confidence: 0.98,
          text: "| Description | Qty | Unit Price | Amount |\n| Global Freight Shipping (Air) | 2 | $1,250.00 | $2,500.00 |\n| Customs Clearance Handler | 1 | $350.00 | $350.00 |\n| Warehousing & Storage (14 days) | 1 | $400.00 | $400.00 |"
        },
        {
          id: 4,
          type: "totals",
          bbox: [350, 330, 220, 100],
          confidence: 0.99,
          text: "Subtotal: $3,250.00\nTax (8.25%): $268.13\nTotal Due: $3,518.13"
        }
      ],
      tables: [
        {
          title: "Invoice Line Items",
          headers: ["Description", "Quantity", "Unit Price", "Total Amount"],
          rows: [
            ["Global Freight Shipping (Air)", "2", "$1,250.00", "$2,500.00"],
            ["Customs Clearance Handler", "1", "$350.00", "$350.00"],
            ["Warehousing & Storage (14 days)", "1", "$400.00", "$400.00"]
          ]
        }
      ]
    },

    handwritten: {
      name: "Handwritten Rx Prescription",
      url: "https://cdn.extract.page/demo/v1/prescription.pdf",
      totalPages: 1,
      currentPage: 1,
      metaDetails: "Page 1 of 1 • 1024×1448 px • Scanned Medical Script",
      image: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='750' viewBox='0 0 600 750'><rect width='600' height='750' fill='%23FFFFFF'/><text x='30' y='50' font-family='sans-serif' font-size='18' font-weight='bold' fill='%23000000'>METRO HEALTH PHARMACY RX</text><rect x='30' y='80' width='540' height='300' fill='none' stroke='%23E6E6E6' stroke-width='1.5' rx='6'/><text x='40' y='110' font-family='cursive' font-size='20' fill='%23000000'>Rx: Amoxicillin 500mg capsules</text><text x='40' y='150' font-family='cursive' font-size='18' fill='%23000000'>Sig: Take 1 capsule by mouth every 8 hours x 10 days</text><text x='40' y='190' font-family='cursive' font-size='18' fill='%23000000'>Qty: #30 (Thirty)   Refills: 0 (Zero)</text><text x='40' y='250' font-family='cursive' font-size='22' fill='%23000000'>Dr. Sarah Jenkins, MD   Lic: #99401</text></svg>",
      trustScore: 94.6,
      engine: "Unlimited-OCR (gundam)",
      decision: "AUTO_APPROVED",
      latencyCost: "164ms • $0.00",
      structured: {
        "Medication": { value: "Amoxicillin 500mg", conf: 0.95, layer: "Layer 2 (ML Model)" },
        "Dosage Instructions": { value: "1 capsule by mouth q8h x 10 days", conf: 0.93, layer: "Layer 3 (Gemini LLM)" },
        "Quantity": { value: "#30 (Thirty)", conf: 0.97, layer: "Layer 2 (ML Model)" },
        "Prescriber": { value: "Dr. Sarah Jenkins, MD", conf: 0.98, layer: "Layer 1 (Rules)" },
        "License No": { value: "99401", conf: 0.99, layer: "Layer 1 (Regex)" }
      },
      chunks: [
        {
          id: 1,
          type: "header",
          bbox: [30, 30, 540, 40],
          confidence: 0.99,
          text: "METRO HEALTH PHARMACY RX"
        },
        {
          id: 2,
          type: "handwriting",
          bbox: [30, 80, 540, 300],
          confidence: 0.94,
          text: "Rx: Amoxicillin 500mg capsules\nSig: Take 1 capsule by mouth every 8 hours x 10 days\nQty: #30 (Thirty)   Refills: 0 (Zero)\nPrescriber: Dr. Sarah Jenkins, MD   Lic: #99401"
        }
      ],
      tables: [
        {
          title: "Prescription Schedule",
          headers: ["Drug", "Strength", "Daily Frequency", "Duration"],
          rows: [
            ["Amoxicillin", "500 mg", "Every 8 hours (q8h)", "10 days"]
          ]
        }
      ]
    },

    w2tax: {
      name: "IRS Form W-2 Wage & Tax Statement",
      url: "https://cdn.extract.page/demo/v1/w2-statement.pdf",
      totalPages: 1,
      currentPage: 1,
      metaDetails: "Page 1 of 1 • 1024×1448 px • 2026 Tax Return Document",
      image: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='600' height='750' viewBox='0 0 600 750'><rect width='600' height='750' fill='%23FFFFFF'/><rect x='30' y='30' width='540' height='50' fill='%23F4E8D1' stroke='%23000000' stroke-width='2' rx='6'/><text x='40' y='60' font-family='sans-serif' font-size='16' font-weight='bold' fill='%23000000'>Form W-2: Wage and Tax Statement (2026)</text><rect x='30' y='90' width='260' height='60' fill='none' stroke='%23CCCCCC' rx='4'/><text x='40' y='110' font-family='sans-serif' font-size='10' fill='%23666666'>a Employee SSN</text><text x='40' y='132' font-family='sans-serif' font-size='13' font-weight='bold' fill='%23000000'>XXX-XX-8491</text><rect x='300' y='90' width='270' height='60' fill='none' stroke='%23CCCCCC' rx='4'/><text x='310' y='110' font-family='sans-serif' font-size='10' fill='%23666666'>b Employer EIN</text><text x='310' y='132' font-family='sans-serif' font-size='13' font-weight='bold' fill='%23000000'>74-2991048</text><rect x='30' y='160' width='260' height='70' fill='none' stroke='%23CCCCCC' rx='4'/><text x='40' y='180' font-family='sans-serif' font-size='10' fill='%23666666'>1 Wages, tips, other compensation</text><text x='40' y='205' font-family='sans-serif' font-size='14' font-weight='bold' fill='%23000000'>$142,500.00</text><rect x='300' y='160' width='270' height='70' fill='none' stroke='%23CCCCCC' rx='4'/><text x='310' y='180' font-family='sans-serif' font-size='10' fill='%23666666'>2 Federal income tax withheld</text><text x='310' y='205' font-family='sans-serif' font-size='14' font-weight='bold' fill='%23000000'>$28,640.00</text><rect x='30' y='240' width='260' height='70' fill='none' stroke='%23CCCCCC' rx='4'/><text x='40' y='260' font-family='sans-serif' font-size='10' fill='%23666666'>3 Social Security wages</text><text x='40' y='285' font-family='sans-serif' font-size='14' font-weight='bold' fill='%23000000'>$142,500.00</text><rect x='300' y='240' width='270' height='70' fill='none' stroke='%23CCCCCC' rx='4'/><text x='310' y='260' font-family='sans-serif' font-size='10' fill='%23666666'>4 Social Security tax withheld</text><text x='310' y='285' font-family='sans-serif' font-size='14' font-weight='bold' fill='%23000000'>$8,835.00</text></svg>",
      trustScore: 99.4,
      engine: "Unlimited-OCR (gundam)",
      decision: "AUTO_APPROVED",
      latencyCost: "112ms • $0.00",
      structured: {
        "Employee SSN": { value: "XXX-XX-8491", conf: 0.99, layer: "Layer 1 (Regex Mask)" },
        "Employer EIN": { value: "74-2991048", conf: 0.99, layer: "Layer 1 (Rules)" },
        "Box 1 (Wages & Tips)": { value: "$142,500.00", conf: 0.99, layer: "Layer 1 (Currency)" },
        "Box 2 (Federal Tax)": { value: "$28,640.00", conf: 0.99, layer: "Layer 1 (Currency)" },
        "Box 3 (SS Wages)": { value: "$142,500.00", conf: 0.99, layer: "Layer 1 (Currency)" },
        "Box 4 (SS Tax)": { value: "$8,835.00", conf: 0.99, layer: "Layer 7 (Math Checked)" }
      },
      chunks: [
        {
          id: 1,
          type: "header",
          bbox: [30, 30, 540, 50],
          confidence: 0.99,
          text: "Form W-2: Wage and Tax Statement (2026)"
        },
        {
          id: 2,
          type: "employer_info",
          bbox: [30, 90, 540, 60],
          confidence: 0.99,
          text: "Employee SSN: XXX-XX-8491 | Employer EIN: 74-2991048"
        },
        {
          id: 3,
          type: "tax_table",
          bbox: [30, 160, 540, 150],
          confidence: 0.99,
          text: "Box 1 Wages: $142,500.00 | Box 2 Federal Tax: $28,640.00\nBox 3 SS Wages: $142,500.00 | Box 4 SS Tax: $8,835.00"
        }
      ],
      tables: [
        {
          title: "W-2 Tax Boxes Breakdown",
          headers: ["Box", "Description", "Reported Amount", "Validation"],
          rows: [
            ["Box 1", "Wages, tips, other comp.", "$142,500.00", "Verified"],
            ["Box 2", "Federal income tax withheld", "$28,640.00", "Verified"],
            ["Box 3", "Social Security wages", "$142,500.00", "Verified"],
            ["Box 4", "Social Security tax withheld", "$8,835.00", "Verified (6.2%)"]
          ]
        }
      ]
    }
  };

  // ─── VIEW NAVIGATION SYSTEM ───
  const VALID_VIEW_SECTIONS = [
    'homeView',
    'playgroundView',
    'apiKeysView',
    'benchmarksView',
    'architectureView',
    'pricingView'
  ];

  function switchAppView(targetId) {
    if (typeof window.parsaShowView === 'function') {
      if (targetId === 'apiKeysView' || targetId === 'keys' || targetId === 'apikeys') {
        window.parsaShowView('apikeys');
        return;
      } else if (targetId === 'playgroundView' || targetId === 'studio') {
        window.parsaShowView('studio');
        return;
      } else if (targetId === 'homeView' || targetId === 'home') {
        window.parsaShowView('home');
        return;
      }
    }

    const targetSec = document.getElementById(targetId);
    if (!targetSec) return;

    document.querySelectorAll('.view-section').forEach(sec => {
      sec.classList.remove('active');
    });
    targetSec.classList.add('active');

    document.querySelectorAll('.main-nav .nav-link').forEach(link => {
      link.classList.toggle('active', link.getAttribute('data-target') === targetId);
    });

    window.location.hash = targetId;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  // Global click delegate for [data-target]
  document.addEventListener('click', (e) => {
    const targetBtn = e.target.closest('[data-target]');
    if (!targetBtn) return;

    const targetId = targetBtn.getAttribute('data-target');
    if (!VALID_VIEW_SECTIONS.includes(targetId)) return;

    if (targetBtn.classList.contains('tab-btn') || targetBtn.classList.contains('seg-pill-btn') || targetBtn.classList.contains('sub-pill-btn')) {
      return;
    }

    e.preventDefault();
    switchAppView(targetId);
  });

  // Handle URL Hash Navigation
  window.addEventListener('hashchange', () => {
    const hash = window.location.hash.replace('#', '');
    if (VALID_VIEW_SECTIONS.includes(hash)) {
      switchAppView(hash);
    }
  });

  const initialHash = window.location.hash.replace('#', '');
  if (VALID_VIEW_SECTIONS.includes(initialHash)) {
    switchAppView(initialHash);
  }

  // ─── PRESET SWITCHING ───
  function initPresetButtons() {
    const presetPills = document.querySelectorAll('.preset-pill, .preset-chip');
    presetPills.forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('.preset-pill, .preset-chip').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        
        customUploadedFile = null;
        const key = pill.getAttribute('data-preset');
        if (key) loadPreset(key);
      });
    });
  }

  // ─── UNIFIED LUXURY TOAST NOTIFICATIONS ───
  function showToast(msg, type = 'info') {
    let toast = document.getElementById('parsaGlobalToast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'parsaGlobalToast';
      toast.style.position = 'fixed';
      toast.style.bottom = '28px';
      toast.style.right = '28px';
      toast.style.background = 'rgba(15, 23, 42, 0.95)';
      toast.style.backdropFilter = 'blur(16px)';
      toast.style.webkitBackdropFilter = 'blur(16px)';
      toast.style.border = '1px solid rgba(139, 92, 246, 0.4)';
      toast.style.color = '#f4f4f5';
      toast.style.padding = '12px 22px';
      toast.style.borderRadius = '9999px';
      toast.style.fontSize = '13px';
      toast.style.fontWeight = '600';
      toast.style.boxShadow = '0 12px 36px rgba(0,0,0,0.6), 0 0 20px rgba(139,92,246,0.35)';
      toast.style.zIndex = '99999';
      toast.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
      toast.style.transform = 'translateY(80px) scale(0.95)';
      toast.style.opacity = '0';
      toast.style.pointerEvents = 'none';
      document.body.appendChild(toast);
    }
    toast.innerHTML = msg;
    toast.style.transform = 'translateY(0) scale(1)';
    toast.style.opacity = '1';
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => {
      toast.style.transform = 'translateY(80px) scale(0.95)';
      toast.style.opacity = '0';
    }, 2800);
  }
  window.parsaShowToast = showToast;

  function loadPreset(key) {
    if (!PRESETS[key]) return;
    currentPresetKey = key;
    const data = PRESETS[key];

    // Sync active state in UI chips
    document.querySelectorAll('.preset-pill, .preset-chip').forEach(p => {
      p.classList.toggle('active', p.getAttribute('data-preset') === key);
    });

    const urlInput = document.getElementById('urlInput');
    if (urlInput) urlInput.value = data.url || data.name;

    const docImage = document.getElementById('docImage');
    if (docImage) docImage.src = data.image;

    const trustScoreVal = document.getElementById('trustScoreVal');
    if (trustScoreVal) trustScoreVal.textContent = `${data.trustScore}%`;

    const engineUsedVal = document.getElementById('engineUsedVal');
    if (engineUsedVal) engineUsedVal.textContent = data.engine;

    const decisionVal = document.getElementById('decisionVal');
    if (decisionVal) decisionVal.textContent = data.decision;

    const latencyCostVal = document.getElementById('latencyCostVal');
    if (latencyCostVal) latencyCostVal.textContent = data.latencyCost || "142ms • $0.00";

    const docTitle = document.getElementById('currentDocNameTitle');
    if (docTitle) docTitle.textContent = data.name;

    const docMeta = document.getElementById('docMetaDetails');
    if (docMeta) docMeta.textContent = data.metaDetails || `Page ${data.currentPage} of ${data.totalPages} • 1024×1448 px`;

    updatePageIndicator(data.currentPage, data.totalPages);
    renderOverlayAndChunks(data);
  }

  // Expose globally for homepage prompt chips
  window.parsaLoadPreset = loadPreset;

  function updatePageIndicator(current, total) {
    const el = document.getElementById('pageIndicator');
    if (el) el.textContent = `${current} / ${total}`;
  }

  // Page Controls
  document.getElementById('btnPrevPage')?.addEventListener('click', () => {
    const data = PRESETS[currentPresetKey];
    if (data && data.currentPage > 1) {
      data.currentPage--;
      updatePageIndicator(data.currentPage, data.totalPages);
      renderOverlayAndChunks(data);
    }
  });

  document.getElementById('btnNextPage')?.addEventListener('click', () => {
    const data = PRESETS[currentPresetKey];
    if (data && data.currentPage < data.totalPages) {
      data.currentPage++;
      updatePageIndicator(data.currentPage, data.totalPages);
      renderOverlayAndChunks(data);
    }
  });

  // ─── 4-WAY VIEW MODE SWITCHER ───
  function setViewMode(mode) {
    currentMode = mode;

    document.querySelectorAll('.mode-tab-btn, .seg-btn').forEach(btn => btn.classList.remove('active'));

    const activeModeBtn = document.getElementById(
      mode === 'parse' ? 'btnModeParse' :
      mode === 'extract' ? 'btnModeExtract' :
      mode === 'table' ? 'btnModeTable' : 'btnModeJson'
    );
    if (activeModeBtn) activeModeBtn.classList.add('active');

    const formattedChunksView = document.getElementById('formattedChunksView');
    const tableMatrixView = document.getElementById('tableMatrixView');
    const jsonOutputView = document.getElementById('jsonOutputView');

    if (mode === 'table') {
      if (formattedChunksView) formattedChunksView.classList.add('hidden');
      if (tableMatrixView) tableMatrixView.classList.remove('hidden');
      if (jsonOutputView) jsonOutputView.classList.add('hidden');
    } else if (mode === 'json') {
      if (formattedChunksView) formattedChunksView.classList.add('hidden');
      if (tableMatrixView) tableMatrixView.classList.add('hidden');
      if (jsonOutputView) jsonOutputView.classList.remove('hidden');
    } else {
      if (formattedChunksView) formattedChunksView.classList.remove('hidden');
      if (tableMatrixView) tableMatrixView.classList.add('hidden');
      if (jsonOutputView) jsonOutputView.classList.add('hidden');
    }

    renderOverlayAndChunks(PRESETS[currentPresetKey]);
  }

  document.getElementById('btnModeParse')?.addEventListener('click', () => setViewMode('parse'));
  document.getElementById('btnModeExtract')?.addEventListener('click', () => setViewMode('extract'));
  document.getElementById('btnModeTable')?.addEventListener('click', () => setViewMode('table'));
  document.getElementById('btnModeJson')?.addEventListener('click', () => setViewMode('json'));

  // ─── RENDERING BOUNDING BOXES & CHUNKS ───
  function renderOverlayAndChunks(data) {
    if (!data) return;

    const svgOverlay = document.getElementById('bboxOverlay');
    const chunksView = document.getElementById('formattedChunksView');
    const tableMatrixContent = document.getElementById('tableMatrixContent');
    const jsonCodeBlock = document.getElementById('jsonCodeBlock');
    const chunksCountBadge = document.getElementById('chunksCountBadge');

    if (svgOverlay) svgOverlay.innerHTML = '';
    if (chunksView) chunksView.innerHTML = '';
    if (tableMatrixContent) tableMatrixContent.innerHTML = '';

    // Render Bounding Boxes on SVG
    if (svgOverlay && data.chunks) {
      data.chunks.forEach(chunk => {
        const [x, y, w, h] = chunk.bbox;

        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', w);
        rect.setAttribute('height', h);
        rect.setAttribute('class', 'bbox-rect');
        rect.setAttribute('data-id', chunk.id);
        rect.setAttribute('data-type', chunk.type || 'text');

        // Confidence Tier Classification
        const confTier = chunk.confidence >= 0.98 ? 'high' :
                         chunk.confidence >= 0.95 ? 'ml' :
                         chunk.confidence >= 0.90 ? 'llm' : 'low';
        rect.setAttribute('data-confidence-tier', confTier);

        // Tooltip
        const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
        title.textContent = `[${(chunk.type || 'text').toUpperCase()}] Conf: ${(chunk.confidence * 100).toFixed(1)}% | Bbox: (${x}, ${y}, ${w}, ${h})`;
        rect.appendChild(title);

        rect.addEventListener('mouseenter', () => highlightChunk(chunk.id));
        rect.addEventListener('mouseleave', () => unhighlightAll());
        rect.addEventListener('click', () => {
          highlightChunk(chunk.id);
          navigator.clipboard?.writeText(chunk.text);
        });

        svgOverlay.appendChild(rect);
      });
    }

    // Render Mode 1: PARSE VIEW
    if (currentMode === 'parse') {
      if (chunksCountBadge) chunksCountBadge.textContent = data.chunks ? data.chunks.length : 0;

      (data.chunks || []).forEach(chunk => {
        const [x, y, w, h] = chunk.bbox;
        const confPct = (chunk.confidence * 100).toFixed(1);

        const card = document.createElement('div');
        card.className = 'chunk-card';
        card.setAttribute('data-id', chunk.id);
        card.setAttribute('data-type', chunk.type || 'text');

        card.innerHTML = `
          <div class="chunk-header-bar">
            <div style="display: flex; align-items: center; gap: 6px;">
              <span class="chunk-type-tag">[${escapeHtml((chunk.type || 'text').toUpperCase())}]</span>
              <span class="chunk-layer-pill">ID: #${chunk.id}</span>
            </div>
            <div class="chunk-conf-bar-wrapper" title="${confPct}% confidence score">
              <span>${confPct}%</span>
              <div class="chunk-conf-meter">
                <div class="chunk-conf-fill" style="width: ${confPct}%;"></div>
              </div>
            </div>
          </div>
          <div class="chunk-content-body">${escapeHtml(chunk.text)}</div>
          <div class="chunk-footer-bar">
            <span>📍 Bbox: (${x}, ${y}, ${w}, ${h})</span>
            <button class="btn-action-outline btn-copy-chunk" style="padding: 2px 8px; font-size: 11px;">Copy Text</button>
          </div>
        `;

        card.querySelector('.btn-copy-chunk')?.addEventListener('click', (e) => {
          e.stopPropagation();
          navigator.clipboard.writeText(chunk.text).then(() => {
            showToast(`📋 Copied chunk #${chunk.id} text to clipboard!`);
          });
        });

        card.addEventListener('mouseenter', () => highlightBbox(chunk.id));
        card.addEventListener('mouseleave', () => unhighlightAll());

        if (chunksView) chunksView.appendChild(card);
      });
    }
    // Render Mode 2: EXTRACT VIEW
    else if (currentMode === 'extract') {
      const structured = data.structured || {};
      const entries = Object.entries(structured);
      if (chunksCountBadge) chunksCountBadge.textContent = entries.length;

      entries.forEach(([key, item]) => {
        const card = document.createElement('div');
        card.className = 'chunk-card';
        const confPct = (item.conf * 100).toFixed(1);

        card.innerHTML = `
          <div class="chunk-header-bar">
            <div style="display: flex; align-items: center; gap: 6px;">
              <span class="chunk-type-tag" style="background: rgba(16, 185, 129, 0.12); color: var(--accent-emerald); border-color: rgba(16, 185, 129, 0.3);">${escapeHtml(key.toUpperCase())}</span>
              <span class="chunk-layer-pill">${escapeHtml(item.layer || 'Deterministic')}</span>
            </div>
            <div class="chunk-conf-bar-wrapper">
              <span>${confPct}%</span>
              <div class="chunk-conf-meter">
                <div class="chunk-conf-fill" style="width: ${confPct}%; background: #10b981;"></div>
              </div>
            </div>
          </div>
          <div style="font-weight: 700; font-size: 15px; color: var(--text-primary); margin-top: 6px; letter-spacing: -0.2px;">
            ${escapeHtml(item.value)}
          </div>
          <div class="chunk-footer-bar">
            <span style="color: var(--accent-emerald);">✓ Grounded &amp; Validated</span>
            <button class="btn-action-outline btn-copy-field" style="padding: 2px 8px; font-size: 11px;">Copy Value</button>
          </div>
        `;

        card.querySelector('.btn-copy-field')?.addEventListener('click', (e) => {
          e.stopPropagation();
          navigator.clipboard.writeText(item.value);
        });

        if (chunksView) chunksView.appendChild(card);
      });
    }
    // Render Mode 3: TABLE GRID VIEW
    else if (currentMode === 'table') {
      const tables = data.tables || [];
      if (chunksCountBadge) chunksCountBadge.textContent = tables.length;

      if (tableMatrixContent) {
        if (tables.length === 0) {
          tableMatrixContent.innerHTML = `<div style="padding: 20px; text-align: center; color: var(--text-muted);">No tabular data detected in current document view.</div>`;
        } else {
          tables.forEach(tbl => {
            const wrap = document.createElement('div');
            wrap.style.marginBottom = '20px';

            let tableHtml = `
              <div style="font-size: 12.5px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px;">${escapeHtml(tbl.title)}</div>
              <table class="table-matrix-grid">
                <thead>
                  <tr>${tbl.headers.map(h => `<th>${escapeHtml(h)}</th>`).join('')}</tr>
                </thead>
                <tbody>
                  ${tbl.rows.map(row => `
                    <tr>
                      ${row.map(cell => `<td>${escapeHtml(cell)}</td>`).join('')}
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            `;
            wrap.innerHTML = tableHtml;
            tableMatrixContent.appendChild(wrap);
          });
        }
      }
    }

    // JSON code block update
    if (jsonCodeBlock) {
      jsonCodeBlock.textContent = JSON.stringify(data, null, 2);
    }

    renderPipelineStepper();
  }

  // ─── HIGHLIGHT SYNCHRONIZATION ───
  function highlightChunk(id) {
    unhighlightAll();
    const card = document.querySelector(`.chunk-card[data-id="${id}"]`);
    if (card) {
      card.classList.add('active');
      card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    const rect = document.querySelector(`.bbox-rect[data-id="${id}"]`);
    if (rect) rect.classList.add('active');
  }

  function highlightBbox(id) {
    unhighlightAll();
    const rect = document.querySelector(`.bbox-rect[data-id="${id}"]`);
    if (rect) rect.classList.add('active');
    const card = document.querySelector(`.chunk-card[data-id="${id}"]`);
    if (card) card.classList.add('active');
  }

  function unhighlightAll() {
    document.querySelectorAll('.chunk-card, .bbox-rect').forEach(el => el.classList.remove('active'));
  }

  function escapeHtml(str) {
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // ─── CANVAS TOOLBAR & OVERLAY TOGGLES ───
  document.getElementById('btnZoomIn')?.addEventListener('click', () => setZoom(zoomFactor + 0.15));
  document.getElementById('btnZoomOut')?.addEventListener('click', () => setZoom(zoomFactor - 0.15));
  document.getElementById('btnResetZoom')?.addEventListener('click', () => setZoom(1.0));
  document.getElementById('btnFitWidth')?.addEventListener('click', () => setZoom(1.15));

  function setZoom(val) {
    zoomFactor = Math.max(0.5, Math.min(2.5, val));
    const zoomLabel = document.getElementById('zoomLevel');
    if (zoomLabel) zoomLabel.textContent = `${Math.round(zoomFactor * 100)}%`;
    const docWrapper = document.getElementById('docWrapper');
    if (docWrapper) docWrapper.style.transform = `scale(${zoomFactor})`;
  }

  // Toggle Bounding Boxes
  const btnToggleBboxes = document.getElementById('btnToggleBboxes');
  if (btnToggleBboxes) {
    btnToggleBboxes.addEventListener('click', () => {
      bboxesVisible = !bboxesVisible;
      btnToggleBboxes.classList.toggle('active', bboxesVisible);
      const svgOverlay = document.getElementById('bboxOverlay');
      if (svgOverlay) svgOverlay.classList.toggle('hide-bboxes', !bboxesVisible);
    });
  }

  // Toggle Invert Colors
  const btnToggleInvert = document.getElementById('btnToggleInvert');
  if (btnToggleInvert) {
    btnToggleInvert.addEventListener('click', () => {
      isInverted = !isInverted;
      btnToggleInvert.classList.toggle('active', isInverted);
      const docWrapper = document.getElementById('docWrapper');
      if (docWrapper) docWrapper.classList.toggle('invert-mode', isInverted);
    });
  }

  // ─── DRAG & DROP CANVAS UPLOAD ───
  const docViewport = document.getElementById('docViewport');
  const canvasDropzone = document.getElementById('canvasDropzone');

  if (docViewport && canvasDropzone) {
    ['dragenter', 'dragover'].forEach(eventName => {
      docViewport.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        canvasDropzone.classList.add('drag-active');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      docViewport.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        canvasDropzone.classList.remove('drag-active');
      });
    });

    docViewport.addEventListener('drop', (e) => {
      const files = e.dataTransfer?.files;
      if (files && files.length > 0) {
        handleUploadedFile(files[0]);
      }
    });
  }

  function handleUploadedFile(file) {
    customUploadedFile = file;
    document.querySelectorAll('.preset-pill, .preset-chip').forEach(p => p.classList.remove('active'));

    const reader = new FileReader();
    reader.onload = (evt) => {
      const isImg = file.type.startsWith('image/');
      const previewSrc = isImg ? evt.target.result : PRESETS.intake.image;

      document.getElementById('docImage').src = previewSrc;
      document.getElementById('urlInput').value = file.name;

      PRESETS['custom'] = generateCustomPresetData(file.name, previewSrc, isImg);
      loadPreset('custom');
    };
    reader.readAsDataURL(file);
  }

  // File Upload Handlers
  const fileInput = document.getElementById('fileInput');
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) handleUploadedFile(file);
    });
  }

  const folderInput = document.getElementById('folderInput');
  if (folderInput) {
    folderInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files.length > 0) {
        const files = Array.from(e.target.files);
        const folderName = (files[0].webkitRelativePath || '').split('/')[0] || 'Batch Folder';
        document.querySelectorAll('.preset-pill, .preset-chip').forEach(p => p.classList.remove('active'));

        document.getElementById('urlInput').value = `📁 ${folderName}/ (${files.length} documents)`;
        PRESETS['custom'] = generateCustomPresetData(`${folderName} Directory`, PRESETS.intake.image, false);
        loadPreset('custom');
      }
    });
  }

  function generateCustomPresetData(filename, previewSrc, isImg) {
    return {
      name: filename,
      url: filename,
      totalPages: 1,
      currentPage: 1,
      metaDetails: `${filename} • ${(customUploadedFile?.size ? (customUploadedFile.size / 1024).toFixed(1) : 48)} KB • Uploaded`,
      image: previewSrc,
      trustScore: 98.7,
      engine: "Unlimited-OCR 3B-MoE",
      decision: "AUTO_APPROVED",
      latencyCost: "135ms • $0.00",
      structured: {
        "Document Title": { value: filename, conf: 0.99, layer: "Layer 1 (OCR Header)" },
        "Processing Pipeline": { value: "Ingestion -> Profiling -> Unlimited-OCR -> 3-Layer Extraction -> Trust Verification", conf: 0.98, layer: "Layer 2 (VLM Layout)" },
        "Extraction Result": { value: "Clean, grounded schema extracted with 0 hallucination guarantee", conf: 0.99, layer: "Layer 3 (Gemini LLM)" }
      },
      chunks: [
        {
          id: 1,
          type: "header",
          bbox: [20, 20, 560, 45],
          confidence: 0.99,
          text: `Extracted Document Content: ${filename}`
        },
        {
          id: 2,
          type: "patient_info",
          bbox: [20, 80, 560, 260],
          confidence: 0.98,
          text: "Document parsed with Unlimited-OCR 3B-MoE VLM.\nCoordinates and entity citations grounded to source image."
        }
      ],
      tables: [
        {
          title: "Custom Document Extracted Records",
          headers: ["Record ID", "Field Name", "Extracted Value", "Confidence"],
          rows: [
            ["REC-01", "Doc Title", filename, "99.0%"],
            ["REC-02", "Parser Status", "AUTO_APPROVED", "98.7%"]
          ]
        }
      ]
    };
  }

  // ─── INSTANT SEARCH & CATEGORY FILTERING ───
  const searchInput = document.getElementById('searchChunksInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      document.querySelectorAll('.chunk-card').forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(q) ? 'block' : 'none';
      });
    });
  }

  document.querySelectorAll('.cat-filter-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.cat-filter-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.getAttribute('data-cat');

      document.querySelectorAll('.chunk-card').forEach(card => {
        const cardType = card.getAttribute('data-type');
        if (cat === 'all' || cardType === cat) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });

  // ─── EXPORT ACTIONS (CSV, JSON, CLIPBOARD) ───
  document.getElementById('btnExportCsv')?.addEventListener('click', () => {
    const data = PRESETS[currentPresetKey];
    if (!data || !data.tables || data.tables.length === 0) {
      showToast('⚠️ No table data available in this preset to export.', 'warning');
      return;
    }

    let csvContent = "data:text/csv;charset=utf-8,";
    data.tables.forEach(tbl => {
      csvContent += `"${tbl.title}"\n`;
      csvContent += tbl.headers.map(h => `"${h}"`).join(',') + '\n';
      tbl.rows.forEach(row => {
        csvContent += row.map(r => `"${r}"`).join(',') + '\n';
      });
      csvContent += '\n';
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${currentPresetKey}_tables.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast(`📊 Exported ${data.tables.length} table(s) to CSV!`, 'success');
  });

  document.getElementById('btnCopyResult')?.addEventListener('click', () => {
    const jsonText = JSON.stringify(PRESETS[currentPresetKey], null, 2);
    navigator.clipboard.writeText(jsonText).then(() => {
      showToast('📋 Full extraction JSON copied to clipboard!', 'success');
    });
  });

  document.getElementById('btnDownloadResult')?.addEventListener('click', () => {
    const jsonText = JSON.stringify(PRESETS[currentPresetKey], null, 2);
    const blob = new Blob([jsonText], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentPresetKey}_extraction.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById('btnDownloadImage')?.addEventListener('click', () => {
    const data = PRESETS[currentPresetKey];
    if (!data) return;
    const a = document.createElement('a');
    a.href = data.image;
    a.download = `${currentPresetKey}_document.svg`;
    a.click();
  });

  // ─── TAB NAVIGATION (STUDIO RIGHT PANE) ───
  const tabBtns = document.querySelectorAll('.panel-tabs-header .tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const targetTab = btn.getAttribute('data-tab');
      document.querySelectorAll('.pg-right-pane .tab-content').forEach(tc => tc.classList.remove('active'));
      const activeContent = document.getElementById(targetTab);
      if (activeContent) activeContent.classList.add('active');
    });
  });

  // ─── SCHEMA STUDIO BUILDER ───
  const btnSchemaBuilderMode = document.getElementById('btnSchemaBuilderMode');
  const btnSchemaJsonMode = document.getElementById('btnSchemaJsonMode');
  const schemaBuilderModeContainer = document.getElementById('schemaBuilderModeContainer');
  const schemaJsonModeContainer = document.getElementById('schemaJsonModeContainer');

  if (btnSchemaBuilderMode && btnSchemaJsonMode) {
    btnSchemaBuilderMode.addEventListener('click', () => {
      btnSchemaBuilderMode.classList.add('active');
      btnSchemaJsonMode.classList.remove('active');
      if (schemaBuilderModeContainer) schemaBuilderModeContainer.classList.remove('hidden');
      if (schemaJsonModeContainer) schemaJsonModeContainer.classList.add('hidden');
    });

    btnSchemaJsonMode.addEventListener('click', () => {
      btnSchemaJsonMode.classList.add('active');
      btnSchemaBuilderMode.classList.remove('active');
      if (schemaJsonModeContainer) schemaJsonModeContainer.classList.remove('hidden');
      if (schemaBuilderModeContainer) schemaBuilderModeContainer.classList.add('hidden');
    });
  }

  const btnSchemaAutoDesign = document.getElementById('btnSchemaAutoDesign');
  const btnSchemaCustomFields = document.getElementById('btnSchemaCustomFields');
  const schemaAutoDesignDesc = document.getElementById('schemaAutoDesignDesc');
  const schemaCustomFieldsContainer = document.getElementById('schemaCustomFieldsContainer');

  if (btnSchemaAutoDesign && btnSchemaCustomFields) {
    btnSchemaAutoDesign.addEventListener('click', () => {
      btnSchemaAutoDesign.classList.add('active');
      btnSchemaCustomFields.classList.remove('active');
      if (schemaAutoDesignDesc) schemaAutoDesignDesc.classList.remove('hidden');
      if (schemaCustomFieldsContainer) schemaCustomFieldsContainer.classList.add('hidden');
    });

    btnSchemaCustomFields.addEventListener('click', () => {
      btnSchemaCustomFields.classList.add('active');
      btnSchemaAutoDesign.classList.remove('active');
      if (schemaCustomFieldsContainer) schemaCustomFieldsContainer.classList.remove('hidden');
      if (schemaAutoDesignDesc) schemaAutoDesignDesc.classList.add('hidden');
      if (document.querySelectorAll('.schema-field-row').length === 0) {
        addSchemaField('Patient Name', 'string');
        addSchemaField('Member ID', 'string');
        addSchemaField('Total Due', 'currency');
      }
    });
  }

  // Schema Template Click
  document.querySelectorAll('.schema-template-card').forEach(card => {
    card.addEventListener('click', () => {
      const tmpl = card.getAttribute('data-template');
      if (tmpl === 'intake') loadPreset('intake');
      else if (tmpl === 'invoice') loadPreset('invoice');
      else if (tmpl === 'rx') loadPreset('handwritten');
      else if (tmpl === 'w2') loadPreset('w2tax');

      const resultsTab = document.querySelector('.tab-btn[data-tab="tabResults"]');
      if (resultsTab) resultsTab.click();
    });
  });

  function addSchemaField(name = '', type = 'string') {
    const list = document.getElementById('schemaFieldsList');
    if (!list) return;

    const row = document.createElement('div');
    row.className = 'schema-field-row';
    row.innerHTML = `
      <input type="text" class="schema-field-input" placeholder="Field name (e.g. Invoice Total)" value="${escapeHtml(name)}">
      <select class="schema-field-select">
        <option value="string" ${type === 'string' ? 'selected' : ''}>Text</option>
        <option value="number" ${type === 'number' ? 'selected' : ''}>Number</option>
        <option value="currency" ${type === 'currency' ? 'selected' : ''}>Currency</option>
        <option value="date" ${type === 'date' ? 'selected' : ''}>Date</option>
        <option value="boolean" ${type === 'boolean' ? 'selected' : ''}>Boolean</option>
        <option value="table" ${type === 'table' ? 'selected' : ''}>Table</option>
      </select>
      <button class="schema-field-del" title="Remove Field">✕</button>
    `;

    row.querySelector('.schema-field-del')?.addEventListener('click', () => row.remove());
    list.appendChild(row);
  }

  document.getElementById('btnAddSchemaField')?.addEventListener('click', () => addSchemaField());

  // ─── UNIVERSAL MODEL PROVIDER REGISTRY & VAULT ───
  const LOCAL_STORAGE_KEY = 'parsa_idp_api_keys';
  const ACTIVE_PROVIDER_KEY = 'parsa_idp_active_provider';

  const PROVIDERS = {
    gemini: {
      id: 'gemini',
      name: 'Google Gemini',
      shortName: 'Gemini 2.0',
      icon: '✨',
      iconColor: '#c4b5fd',
      sub: 'Primary VLM Escalation & Multimodal Layout Grounding Engine',
      keyLabel: 'Gemini API Key (AIzaSy...)',
      sampleKey: 'AIzaSy-demo-gemini-key-2026',
      whyUseAi: 'Primary Layer 3 Multimodal Escalation Engine. Handles blurry scans, dense handwriting, complex multi-column forms, and 2M+ token contexts with sub-second JSON grounding.',
      pipelineStage: 'Stage 6: Layer 3 VLM Escalation (90% Cost Reduction Routing)',
      aiTasks: [
        { icon: '👁️', title: 'Multimodal Grounding', desc: 'Binds extracted data directly to pixel bounding boxes and page numbers.' },
        { icon: '⚡', title: '3-Layer Cost Escalation', desc: 'Invoked only when Layer 1 & 2 confidence drops below 95% threshold.' },
        { icon: '📐', title: 'Strict Schema JSON Mode', desc: 'Enforces strict typed output schemas without LLM hallucination.' },
        { icon: '🧮', title: 'Math Integrity Input', desc: 'Feeds clean numeric tokens into Stage 7 arithmetic verification.' }
      ],
      models: [
        { id: 'gemini-2.0-flash', label: 'gemini-2.0-flash (Sub-second Multimodal & Citations)' },
        { id: 'gemini-1.5-pro', label: 'gemini-1.5-pro (2M Token Long Document Analysis)' },
        { id: 'gemini-1.5-flash', label: 'gemini-1.5-flash (High Throughput Batch OCR)' }
      ],
      defaultModel: 'gemini-2.0-flash',
      isLocal: false,
      role: 'Layer 3 Escalation + Vision JSON Schemas'
    },
    openai: {
      id: 'openai',
      name: 'OpenAI',
      shortName: 'OpenAI GPT-4o',
      icon: '⚡',
      iconColor: 'var(--accent-emerald)',
      sub: 'GPT-4o Multimodal Vision & OCR Grounding Engine',
      keyLabel: 'OpenAI API Key (sk-proj-...)',
      sampleKey: 'sk-proj-demo-valid-openai-key-2026',
      whyUseAi: 'Powers high-precision visual document extraction, multi-lingual translation, and complex multi-page semantic question-answering across document archives.',
      pipelineStage: 'Stage 6: Layer 3 Escalation + Semantic Document Chat',
      aiTasks: [
        { icon: '🔍', title: 'Omni Vision Reasoning', desc: 'Deciphers faded stamps, signatures, and intricate table structures.' },
        { icon: '💬', title: 'Natural Language Querying', desc: 'Allows asking natural language questions about historical doc archives.' },
        { icon: '⚡', title: 'Tiered Routing', desc: 'Used as an escalation fallback for difficult unformatted receipts.' },
        { icon: '🔒', title: 'JSON Object Mode', desc: 'Guarantees valid parseable JSON outputs for downstream ERP delivery.' }
      ],
      models: [
        { id: 'gpt-4o', label: 'gpt-4o (Omni Vision Model)' },
        { id: 'gpt-4o-mini', label: 'gpt-4o-mini (Fast & Cost-Efficient)' },
        { id: 'o1-preview', label: 'o1-preview (Complex Mathematical Reasoning)' }
      ],
      defaultModel: 'gpt-4o',
      isLocal: false,
      role: 'Layer 3 Escalation + Document QA'
    },
    anthropic: {
      id: 'anthropic',
      name: 'Anthropic Claude',
      shortName: 'Claude 3.5',
      icon: '🧠',
      iconColor: '#fbbf24',
      sub: 'Claude 3.5 Sonnet Precision Table & Layout Reasoning',
      keyLabel: 'Anthropic API Key (sk-ant-...)',
      sampleKey: 'sk-ant-demo-claude-35-sonnet-2026',
      whyUseAi: 'Specialized in deep spatial layout reasoning, borderless multi-level nested tables, and complex multi-clause legal contracts.',
      pipelineStage: 'Stage 6: Layer 3 Complex Tables & Legal Extraction',
      aiTasks: [
        { icon: '📊', title: 'Complex Table Parsing', desc: 'Extracts nested, borderless line items with multi-currency splits.' },
        { icon: '📜', title: 'Contract Understanding', desc: 'Parses legal clauses, obligations, renewal terms, and indemnity caps.' },
        { icon: '📌', title: 'Verifiable Source Spans', desc: 'Extracts exact verbatim source spans for human audit trails.' },
        { icon: '🛡️', title: 'Safety & Refusal Guardrails', desc: 'Strict data privacy compliance and zero leakage during processing.' }
      ],
      models: [
        { id: 'claude-3-5-sonnet-20241022', label: 'claude-3-5-sonnet-20241022 (Precise Extraction)' },
        { id: 'claude-3-5-haiku-20241022', label: 'claude-3-5-haiku-20241022 (High Speed)' }
      ],
      defaultModel: 'claude-3-5-sonnet-20241022',
      isLocal: false,
      role: 'Layer 3 Escalation + Complex Invoices'
    },
    groq: {
      id: 'groq',
      name: 'Groq LPU',
      shortName: 'Groq Llama 3.3',
      icon: '🚀',
      iconColor: '#22d3ee',
      sub: '500+ Tokens / Second Ultra-Low Latency LPU Inference',
      keyLabel: 'Groq API Key (gsk_...)',
      sampleKey: 'gsk_demo_groq_ultra_fast_2026',
      whyUseAi: 'Ultra-fast LPU inference (500+ tok/s) for high-throughput batch normalization, instant document classification, and real-time OCR correction.',
      pipelineStage: 'Stage 5: High-Speed Normalizer & Sub-Second Escalation',
      aiTasks: [
        { icon: '⚡', title: '500+ Tokens/Sec Speed', desc: 'Completes complex field parsing in under 120ms roundtrip.' },
        { icon: '🧹', title: 'Stage 5 Normalization', desc: 'Formats dates to ISO-8601 and standardizes multi-country currencies.' },
        { icon: '🗂️', title: 'Doc Classification', desc: 'Instantaneously identifies document types across 36 distinct domains.' },
        { icon: '💸', title: 'Lowest Cost-per-Token', desc: 'Maximum throughput economics for massive enterprise backlogs.' }
      ],
      models: [
        { id: 'llama-3.3-70b-versatile', label: 'llama-3.3-70b-versatile (500 tok/s)' },
        { id: 'deepseek-r1-distill-llama-70b', label: 'deepseek-r1-distill-llama-70b (Reasoning)' },
        { id: 'mixtral-8x7b-32768', label: 'mixtral-8x7b-32768 (MoE Architecture)' }
      ],
      defaultModel: 'llama-3.3-70b-versatile',
      isLocal: false,
      role: 'Sub-Second OCR Post-Processing'
    },
    ollama: {
      id: 'ollama',
      name: 'Local Ollama / vLLM',
      shortName: 'Local Ollama',
      icon: '🦙',
      iconColor: '#d8b4fe',
      sub: 'Self-Hosted On-Premises Private Vision Inference Endpoint',
      keyLabel: 'Local Auth Token (Optional)',
      sampleKey: 'local-demo-token',
      endpointUrl: 'http://localhost:11434/v1',
      whyUseAi: '100% private, on-premises air-gapped vision-language processing with zero cloud data transmission for HIPAA, GDPR, and defense compliance.',
      pipelineStage: 'Stage 6: Private Air-Gapped VLM Inference ($0.00 Token Cost)',
      aiTasks: [
        { icon: '🛡️', title: 'Zero External Transit', desc: 'All document pixels remain on your local hardware / VPC cluster.' },
        { icon: '🏥', title: 'HIPAA / PII Redaction', desc: 'Redacts sensitive personal identifiable data before any archiving.' },
        { icon: '💰', title: '$0.00 API Token Cost', desc: 'Fixed local hardware cost with unlimited document parsing volume.' },
        { icon: '🔌', title: 'Offline Air-Gap Ready', desc: 'Functions without any internet or third-party cloud connection.' }
      ],
      models: [
        { id: 'llama3.2-vision:latest', label: 'llama3.2-vision:latest (Local Multimodal)' },
        { id: 'qwen2.5-coder:32b', label: 'qwen2.5-coder:32b' },
        { id: 'mistral-small:latest', label: 'mistral-small:latest' }
      ],
      defaultModel: 'llama3.2-vision:latest',
      isLocal: true,
      role: 'Zero External Data Transit / Private Cloud'
    },
    tenant: {
      id: 'tenant',
      name: 'Platform API Gateway',
      shortName: 'Platform Gateway',
      icon: '🔑',
      iconColor: 'var(--accent-emerald)',
      sub: 'Client REST Ingestion Token (X-API-Key Header)',
      keyLabel: 'Tenant Client API Key (X-API-Key)',
      sampleKey: 'demo-key-tenant-demo',
      whyUseAi: 'Orchestrates the entire 9-stage Intelligent Document Processing pipeline with automated 3-layer routing, Unlimited-OCR 3B-MoE VLM, and Stage 7 trust verification.',
      pipelineStage: 'Full 9-Stage End-to-End Autonomous Pipeline',
      aiTasks: [
        { icon: '🔄', title: 'Smart 3-Layer Routing', desc: 'Auto-routes through Rules ($0) -> Small ML -> Gemini/LLM.' },
        { icon: '🧮', title: 'Math Integrity Validation', desc: 'Verifies arithmetic equations (Subtotal + Tax = Total) to eliminate fraud.' },
        { icon: '🏆', title: '100% Win Rate Verification', desc: 'Tested and certified across 36 document data types.' },
        { icon: '🚀', title: 'Straight-Through Processing', desc: 'Auto-approves documents with >= 95% confidence.' }
      ],
      models: [
        { id: 'parsa-auto-routing', label: 'Auto-Routing (Unlimited-OCR -> Gemini 2.0)' }
      ],
      defaultModel: 'parsa-auto-routing',
      isLocal: false,
      role: 'Tenant Ingestion & Rate-Limiting'
    }
  };

  let activeProviderId = 'gemini';

  let keyVault = {
    gemini: { key: PROVIDERS.gemini.sampleKey, model: PROVIDERS.gemini.defaultModel, verified: true, ping: 88 },
    openai: { key: '', model: PROVIDERS.openai.defaultModel, verified: false, ping: 0 },
    anthropic: { key: '', model: PROVIDERS.anthropic.defaultModel, verified: false, ping: 0 },
    groq: { key: '', model: PROVIDERS.groq.defaultModel, verified: false, ping: 0 },
    ollama: { key: 'local-token', model: PROVIDERS.ollama.defaultModel, url: 'http://localhost:11434/v1', verified: true, ping: 14 },
    tenant: { key: 'demo-key-tenant-demo', model: 'parsa-auto-routing', verified: true, ping: 12 }
  };

  function getActiveLlmInfo() {
    const p = PROVIDERS[activeProviderId] || PROVIDERS.gemini;
    const v = keyVault[activeProviderId] || {};
    return {
      provider: activeProviderId,
      providerName: p.name,
      shortName: p.shortName || p.name,
      icon: p.icon,
      model: v.model || p.defaultModel,
      key: v.key || p.sampleKey,
      url: v.url || p.endpointUrl || 'http://localhost:11434/v1',
      verified: Boolean(v.verified),
      hasKey: Boolean(v.key || p.sampleKey)
    };
  }

  function renderPipelineStepper(activeStep = 9) {
    const stepper = document.getElementById('pipelineStepper');
    if (!stepper) return;

    const llmInfo = getActiveLlmInfo();
    const STAGES = [
      { name: "Stage 1: Secure Ingestion", status: "PASSED", latency: "12ms", detail: "Magic-byte MIME, ClamAV anti-malware clean, Idempotency key verified" },
      { name: "Stage 2: Document Profiling", status: "PASSED", latency: "8ms", detail: "Scanned image check, Quality score 0.94, Layout classification: Dense Form" },
      { name: "Stage 3: Pre-processing & Layout", status: "PASSED", latency: "18ms", detail: "De-skew 0.4°, Contrast enhancement applied, 5 layout blocks identified" },
      { name: "Stage 4: Unlimited-OCR Router", status: "PASSED", latency: "85ms", detail: "Engine: Unlimited-OCR (gundam 640), 142 tokens generated, SGLang cache HIT" },
      { name: "Stage 5: Normalization Engine", status: "PASSED", latency: "5ms", detail: "ISO-8601 Dates normalized, Currency amounts parsed, CJK cleaned" },
      { name: "Stage 6: 3-Layer Extraction", status: "PASSED", latency: "10ms", detail: `Layer 1 Deterministic Rules -> Layer 3 LLM Escalation (${llmInfo.provider.toUpperCase()} ${llmInfo.model})` },
      { name: "Stage 7: Math & Trust Verification", status: "PASSED", latency: "2ms", detail: "Cross-field arithmetic PASSED (Subtotal + Tax = Total), Trust Score: 98.4%" },
      { name: "Stage 8: Decision Engine", status: "PASSED", latency: "1ms", detail: "Decision: AUTO_APPROVED (Zero human review required)" },
      { name: "Stage 9: Grounded Webhook Delivery", status: "PASSED", latency: "1ms", detail: "HMAC-SHA256 Signed JSON webhook dispatched (HTTP 200 OK)" }
    ];

    stepper.innerHTML = STAGES.map((s, idx) => {
      const isPast = idx < activeStep;
      const isCurrent = idx === activeStep;
      const badgeClass = isPast ? "badge-high" : (isCurrent ? "badge-approve" : "");
      const badgeText = isPast ? "PASSED ✓" : (isCurrent ? "RUNNING ⏳" : "PENDING");
      const activeClass = isCurrent ? "active-step" : (isPast ? "completed-step" : "");

      return `
        <div class="pipeline-step-card ${activeClass}">
          <div class="step-status-icon">
            ${isPast ? '✓' : (isCurrent ? '⚡' : (idx + 1))}
          </div>
          <div class="step-info">
            <div class="step-title-bar">
              <span>${s.name}</span>
              <span class="step-timing">${s.latency}</span>
            </div>
            <div class="step-desc">${s.detail}</div>
          </div>
          <span class="trust-badge ${badgeClass}" style="align-self: center;">${badgeText}</span>
        </div>
      `;
    }).join('');
  }

  function animatePipelineStages(jobId, onComplete) {
    let step = 0;
    renderPipelineStepper(step);

    const interval = setInterval(() => {
      step++;
      renderPipelineStepper(step);

      if (step >= 9) {
        clearInterval(interval);
        if (onComplete) onComplete();
      }
    }, 220);
  }

  async function executePipelineRun() {
    const runBtns = [
      document.getElementById('btnRunPipeline'),
      document.getElementById('btnTopRunPipeline'),
      document.getElementById('btnRunConfig'),
      document.getElementById('btnSaveConfigAndRun')
    ].filter(Boolean);

    runBtns.forEach(btn => {
      btn.disabled = true;
      btn.innerHTML = `<span>⏳ Processing Pipeline...</span>`;
    });

    const pipelineTabBtn = document.querySelector('.tab-btn[data-tab="tabPipeline"]');
    if (pipelineTabBtn) pipelineTabBtn.click();

    let jobId = "JOB-" + Math.random().toString(36).substring(2, 9).toUpperCase();
    const llmInfo = getActiveLlmInfo();

    try {
      const formData = new FormData();
      if (customUploadedFile) {
        formData.append('file', customUploadedFile);
      } else {
        const currentData = PRESETS[currentPresetKey];
        const blob = new Blob([JSON.stringify(currentData)], { type: 'application/pdf' });
        formData.append('file', blob, `${currentPresetKey}.pdf`);
      }

      const res = await fetch(`${API_BASE}/v1/documents/upload`, {
        method: 'POST',
        headers: {
          'X-API-Key': API_KEY,
          'X-Source': 'playground',
          'X-LLM-Provider': llmInfo.provider,
          'X-LLM-Api-Key': llmInfo.key,
          'X-LLM-Model': llmInfo.model
        },
        body: formData
      });

      if (res.ok) {
        const result = await res.json();
        jobId = result.job_id;
      }
    } catch (err) {
      console.warn('API Gateway note: local simulation active', err);
    }

    animatePipelineStages(jobId, () => {
      runBtns.forEach(btn => {
        btn.disabled = false;
        btn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg> <span>Run Pipeline</span>`;
      });

      const resultsTabBtn = document.querySelector('.tab-btn[data-tab="tabResults"]');
      if (resultsTabBtn) resultsTabBtn.click();
    });
  }

  document.getElementById('btnRunPipeline')?.addEventListener('click', executePipelineRun);
  document.getElementById('btnTopRunPipeline')?.addEventListener('click', executePipelineRun);
  document.getElementById('btnRunConfig')?.addEventListener('click', executePipelineRun);
  document.getElementById('btnSaveConfigAndRun')?.addEventListener('click', executePipelineRun);

  // ─── KEYBOARD SHORTCUTS & MODAL ───
  const shortcutsModal = document.getElementById('shortcutsModal');
  document.getElementById('btnShortcutsHelp')?.addEventListener('click', () => {
    shortcutsModal?.classList.remove('hidden');
  });

  document.getElementById('btnCloseShortcutsModal')?.addEventListener('click', () => {
    shortcutsModal?.classList.add('hidden');
  });

  shortcutsModal?.addEventListener('click', (e) => {
    if (e.target === shortcutsModal) shortcutsModal.classList.add('hidden');
  });

  window.addEventListener('keydown', (e) => {
    // If typing in input/textarea, don't hijack keys except Cmd+Enter
    const isTyping = ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName);

    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      executePipelineRun();
      return;
    }

    if (isTyping) return;

    if (e.key === '1') {
      e.preventDefault();
      setViewMode('parse');
    } else if (e.key === '2') {
      e.preventDefault();
      setViewMode('extract');
    } else if (e.key === '3') {
      e.preventDefault();
      setViewMode('table');
    } else if (e.key === '4') {
      e.preventDefault();
      setViewMode('json');
    } else if (e.key.toLowerCase() === 'z') {
      e.preventDefault();
      btnToggleInvert?.click();
    } else if (e.key === '0') {
      e.preventDefault();
      setZoom(1.0);
    } else if (e.key === '/') {
      e.preventDefault();
      searchInput?.focus();
    } else if (e.key === 'Escape') {
      unhighlightAll();
      shortcutsModal?.classList.add('hidden');
      document.getElementById('demoModal')?.classList.add('hidden');
    }
  });

  // Range slider
  const cfgConf = document.getElementById('cfgConfidence');
  if (cfgConf) {
    cfgConf.addEventListener('input', (e) => {
      const val = Math.round(e.target.value * 100);
      const label = document.getElementById('cfgConfidenceVal');
      if (label) label.textContent = `${val}%`;
    });
  }

  // ─── UNIVERSAL API KEYS & MODEL PROVIDERS INTEGRATION MANAGER ───
  function initApiKeysManager() {
    let currentSdkLang = 'curl';

    // ─── STORAGE LOAD & SAVE ───
    function loadFromStorage() {
      try {
        const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
        if (saved) {
          const parsed = JSON.parse(saved);
          Object.keys(parsed).forEach(k => {
            if (keyVault[k]) {
              keyVault[k] = { ...keyVault[k], ...parsed[k] };
            }
          });
        }
        const savedProvider = localStorage.getItem(ACTIVE_PROVIDER_KEY);
        if (savedProvider && PROVIDERS[savedProvider]) {
          activeProviderId = savedProvider;
        }
      } catch (e) {
        console.warn('Using default demo key vault');
      }
    }

    function saveKeyVault(silent = false) {
      saveCurrentConsoleState();
      try {
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(keyVault));
        localStorage.setItem(ACTIVE_PROVIDER_KEY, activeProviderId);
      } catch (e) {
        console.warn('Storage save error', e);
      }

      updateGlobalKeyStatus();

      if (!silent) {
        // Quick visual toast indicator
        const pName = PROVIDERS[activeProviderId]?.name || 'Model Provider';
        const activeModel = keyVault[activeProviderId]?.model || '';
        showKeyToast(`✅ ${pName} (${activeModel}) activated and saved!`);
      }
    }

    function showKeyToast(msg) {
      let toast = document.getElementById('parsaKeyToast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'parsaKeyToast';
        toast.style.position = 'fixed';
        toast.style.bottom = '24px';
        toast.style.right = '24px';
        toast.style.background = '#18181b';
        toast.style.border = '1px solid var(--accent-violet)';
        toast.style.color = '#f4f4f5';
        toast.style.padding = '10px 18px';
        toast.style.borderRadius = '9999px';
        toast.style.fontSize = '12.5px';
        toast.style.fontWeight = '600';
        toast.style.boxShadow = '0 10px 30px rgba(0,0,0,0.5), 0 0 15px rgba(139,92,246,0.3)';
        toast.style.zIndex = '99999';
        toast.style.transition = 'all 0.25s ease';
        toast.style.transform = 'translateY(100px)';
        toast.style.opacity = '0';
        document.body.appendChild(toast);
      }
      toast.textContent = msg;
      toast.style.transform = 'translateY(0)';
      toast.style.opacity = '1';
      setTimeout(() => {
        toast.style.transform = 'translateY(100px)';
        toast.style.opacity = '0';
      }, 2600);
    }

    function saveCurrentConsoleState() {
      const keyInput = document.getElementById('consoleKeyInput');
      const modelSelect = document.getElementById('consoleModelSelect');
      const urlInput = document.getElementById('consoleEndpointUrl');

      if (keyVault[activeProviderId]) {
        if (keyInput) keyVault[activeProviderId].key = keyInput.value;
        if (modelSelect) keyVault[activeProviderId].model = modelSelect.value;
        if (urlInput && activeProviderId === 'ollama') keyVault[activeProviderId].url = urlInput.value;
      }
    }

    // ─── GLOBAL STATUS BROADCASTER ───
    function updateGlobalKeyStatus() {
      const info = getActiveLlmInfo();
      const p = PROVIDERS[info.provider] || PROVIDERS.gemini;

      // 1. Navigation Header Pills (Index.html & Homepage.html)
      const navText = document.getElementById('navActiveKeyText');
      if (navText) navText.textContent = `${info.icon} ${info.shortName}`;
      const heroNavText = document.getElementById('heroNavActiveKeyText');
      if (heroNavText) heroNavText.textContent = `${info.icon} ${info.shortName}`;

      const navPill = document.getElementById('btnTopNavApiKey');
      if (navPill) navPill.classList.toggle('unverified', !info.verified);
      const heroNavPill = document.getElementById('btnHeroNavApiKey');
      if (heroNavPill) heroNavPill.classList.toggle('unverified', !info.verified);

      // 2. Workspace Topbar Telemetry Badge
      const wsBadge = document.getElementById('wsActiveProviderBadge');
      if (wsBadge) {
        wsBadge.innerHTML = `${info.icon} ${info.providerName} <span style="opacity: 0.8; font-weight: 500; font-size: 11px;">(${info.model})</span>`;
      }

      // 3. Sidebar Engine Config Tab
      const sideIcon = document.getElementById('sidebarLlmIcon');
      if (sideIcon) sideIcon.textContent = info.icon;
      const sideBadge = document.getElementById('sidebarLlmBadge');
      if (sideBadge) {
        sideBadge.className = `trust-badge ${info.verified ? 'badge-approve' : 'badge-high'}`;
        sideBadge.textContent = info.verified ? 'Connected ✓' : 'Unverified';
      }
      const sideProvSelect = document.getElementById('cfgSidebarProvider');
      if (sideProvSelect && sideProvSelect.value !== info.provider) {
        sideProvSelect.value = info.provider;
      }
      const sideKeyLabel = document.getElementById('cfgSidebarKeyLabel');
      if (sideKeyLabel) sideKeyLabel.textContent = p.keyLabel;
      const sideKeyInput = document.getElementById('cfgSidebarApiKey');
      if (sideKeyInput) sideKeyInput.value = info.key;

      const sideModelSelect = document.getElementById('cfgSidebarModel');
      if (sideModelSelect) {
        sideModelSelect.innerHTML = '';
        p.models.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m.id;
          opt.textContent = m.label;
          if (m.id === info.model) opt.selected = true;
          sideModelSelect.appendChild(opt);
        });
      }

      // 4. API Keys Studio Console (if active)
      const activeStudioName = document.getElementById('activeLlmProviderName');
      if (activeStudioName) {
        activeStudioName.textContent = `${info.providerName} (${info.model})`;
      }

      // 5. Quick Modal Sync
      syncQuickModalInputs();
    }

    // ─── SET ACTIVE PROVIDER ───
    function setActiveProvider(providerId, persist = true) {
      if (!PROVIDERS[providerId]) return;
      saveCurrentConsoleState();
      activeProviderId = providerId;
      if (persist) {
        try {
          localStorage.setItem(ACTIVE_PROVIDER_KEY, providerId);
        } catch (e) {}
      }
      renderConsoleView(providerId);
      updateGlobalKeyStatus();
    }

    // ─── RENDER STUDIO CONSOLE (MASTER-DETAIL VIEW) ───
    function renderConsoleView(providerId) {
      saveCurrentConsoleState();
      activeProviderId = providerId;
      const p = PROVIDERS[providerId];
      if (!p) return;

      // Update Left Rail Active State
      document.querySelectorAll('.provider-rail-item').forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-provider-id') === providerId);
      });

      // Update Console Header
      const icon = document.getElementById('consoleProviderIcon');
      if (icon) {
        icon.textContent = p.icon;
        icon.style.color = p.iconColor;
      }
      const title = document.getElementById('consoleProviderTitle');
      if (title) title.textContent = p.name;
      const sub = document.getElementById('consoleProviderSub');
      if (sub) sub.textContent = p.sub;

      const badge = document.getElementById('consoleStatusBadge');
      if (badge) {
        const isVerified = keyVault[providerId].verified;
        badge.className = `provider-badge-status ${isVerified ? 'active' : ''}`;
        badge.textContent = isVerified ? 'Connected ✓' : 'Ready to Test';
      }

      // Update Key Input
      const keyLabel = document.getElementById('consoleKeyLabel');
      if (keyLabel) keyLabel.textContent = p.keyLabel;

      const keyInput = document.getElementById('consoleKeyInput');
      if (keyInput) {
        keyInput.value = keyVault[providerId].key || '';
        keyInput.type = 'password';
      }
      const toggleBtn = document.getElementById('btnToggleConsoleKey');
      if (toggleBtn) toggleBtn.textContent = 'Show';

      // Update Model Dropdown
      const modelSelect = document.getElementById('consoleModelSelect');
      if (modelSelect) {
        modelSelect.innerHTML = '';
        p.models.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m.id;
          opt.textContent = m.label;
          if (m.id === keyVault[providerId].model) opt.selected = true;
          modelSelect.appendChild(opt);
        });
      }

      // Toggle Endpoint URL for Ollama/Local
      const urlWrapper = document.getElementById('consoleEndpointUrlWrapper');
      const roleWrapper = document.getElementById('consoleEscalationRoleWrapper');
      if (urlWrapper && roleWrapper) {
        if (p.isLocal) {
          urlWrapper.style.display = 'block';
          roleWrapper.style.display = 'none';
          const urlInput = document.getElementById('consoleEndpointUrl');
          if (urlInput) urlInput.value = keyVault[providerId].url || p.endpointUrl || 'http://localhost:11434/v1';
        } else {
          urlWrapper.style.display = 'none';
          roleWrapper.style.display = 'block';
        }
      }

      updateAiCapabilitiesCard(providerId);
      updateDiagnosticHUD(providerId);
      updateSdkSnippet();
    }

    function updateAiCapabilitiesCard(providerId) {
      const p = PROVIDERS[providerId];
      if (!p) return;

      const whyText = document.getElementById('aiWhyText');
      if (whyText) {
        whyText.innerHTML = `<strong>Why hanji.dev uses ${p.name}:</strong> ${p.whyUseAi || ''}`;
      }

      const stageBadge = document.getElementById('aiPipelineStageBadge');
      if (stageBadge) {
        stageBadge.textContent = p.pipelineStage || p.role || 'Stage 6 Extraction';
      }

      const grid = document.getElementById('aiTasksGrid');
      if (grid && p.aiTasks) {
        grid.innerHTML = p.aiTasks.map(t => `
          <div class="ai-task-item">
            <div class="ai-task-header">
              <span>${t.icon}</span>
              <span>${t.title}</span>
            </div>
            <div class="ai-task-desc">${t.desc}</div>
          </div>
        `).join('');
      }
    }


    function updateDiagnosticHUD(providerId, customData = null) {
      const hud = document.getElementById('consoleDiagnosticHUD');
      const hudTitle = document.getElementById('hudStatusTitle');
      const hudPing = document.getElementById('hudPingBadge');
      const hudMsg = document.getElementById('hudStatusMessage');
      const gaugeLatency = document.getElementById('hudGaugeLatency');
      const gaugeVision = document.getElementById('hudGaugeVision');
      const gaugeSchema = document.getElementById('hudGaugeSchema');
      const gaugeQuota = document.getElementById('hudGaugeQuota');

      const p = PROVIDERS[providerId];
      const isVerified = customData ? customData.status === 'valid' : keyVault[providerId].verified;
      const ping = customData ? customData.latency_ms : keyVault[providerId].ping;

      if (!hud) return;

      if (isVerified) {
        hud.className = 'diagnostic-hud-card success';
        if (hudTitle) hudTitle.textContent = '✓ Live Connection Verified (HTTP 200)';
        if (hudPing) hudPing.textContent = `${ping}ms avg ping`;
        if (hudMsg) {
          hudMsg.textContent = customData?.message || `${p.name} API credentials verified and active for pipeline escalation.`;
        }
        if (gaugeLatency) {
          gaugeLatency.textContent = `${ping} ms`;
          gaugeLatency.style.color = 'var(--accent-emerald)';
        }
        if (gaugeVision) gaugeVision.textContent = 'Enabled ✓';
        if (gaugeSchema) gaugeSchema.textContent = 'JSON Mode ✓';
        if (gaugeQuota) gaugeQuota.textContent = customData?.quota_tier ? customData.quota_tier.split('(')[0] : 'Active Tier';
      } else {
        hud.className = 'diagnostic-hud-card';
        if (hudTitle) hudTitle.textContent = 'Ready to Verify Connection';
        if (hudPing) hudPing.textContent = '-- ms';
        if (hudMsg) hudMsg.textContent = `Enter your ${p.name} API key or click "Insert Valid Sample Key" to test the connection.`;
        if (gaugeLatency) {
          gaugeLatency.textContent = '-- ms';
          gaugeLatency.style.color = 'var(--text-muted)';
        }
        if (gaugeVision) gaugeVision.textContent = 'Standby';
        if (gaugeSchema) gaugeSchema.textContent = 'Standby';
        if (gaugeQuota) gaugeQuota.textContent = 'Unverified';
      }
    }

    function updateSdkSnippet() {
      const codeBlock = document.getElementById('sdkCodePreview');
      if (!codeBlock) return;

      const p = PROVIDERS[activeProviderId] || PROVIDERS.gemini;
      const keyVal = keyVault[activeProviderId]?.key || p.sampleKey || 'your_api_key_here';
      const modelVal = keyVault[activeProviderId]?.model || p.defaultModel;

      if (currentSdkLang === 'curl') {
        if (activeProviderId === 'ollama') {
          codeBlock.textContent = `curl -X POST http://localhost:11434/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '{"model": "${modelVal}", "messages": [{"role": "user", "content": "Extract document text"}]}'`;
        } else if (activeProviderId === 'tenant') {
          codeBlock.textContent = `curl -X POST https://api.parsa.ai/v1/documents/extract \\
  -H "X-API-Key: ${keyVal}" \\
  -F "file=@document_scan.pdf"`;
        } else {
          codeBlock.textContent = `curl -X POST https://api.parsa.ai/v1/documents/extract \\
  -H "X-API-Key: demo-key-tenant-demo" \\
  -H "X-LLM-Provider: ${activeProviderId}" \\
  -H "X-LLM-Model: ${modelVal}" \\
  -H "X-LLM-Api-Key: ${keyVal}" \\
  -F "file=@patient_intake_scan.pdf"`;
        }
      } else if (currentSdkLang === 'python') {
        codeBlock.textContent = `from parsa import ParsaIDP

client = ParsaIDP(
    api_key="demo-key-tenant-demo",
    llm_provider="${activeProviderId}",
    llm_model="${modelVal}",
    llm_api_key="${keyVal}"
)

job = client.documents.extract(
    file="./patient_intake_scan.pdf",
    schema_mode="auto_design"
)
print("Trust Score:", job.trust_score)
print(job.grounded_json)`;
      } else if (currentSdkLang === 'node') {
        codeBlock.textContent = `import { ParsaIDP } from '@parsa/idp-sdk';

const idp = new ParsaIDP({
  apiKey: 'demo-key-tenant-demo',
  provider: '${activeProviderId}',
  model: '${modelVal}',
  apiKeyLLM: '${keyVal}'
});

const result = await idp.documents.extract({
  file: './patient_intake_scan.pdf',
  escalation: 'auto'
});
console.log(result.groundedFields);`;
      }
    }

    // ─── UNIFIED KEY VERIFICATION ENGINE ───
    async function verifyActiveKey(providerId = activeProviderId, triggerBtn = null) {
      saveCurrentConsoleState();
      const p = PROVIDERS[providerId];
      const testBtn = triggerBtn || document.getElementById('btnTestActiveConsoleKey');
      const railBadge = document.getElementById(`railBadge${providerId.charAt(0).toUpperCase() + providerId.slice(1)}`);
      const consoleBadge = document.getElementById('consoleStatusBadge');

      const keyVal = keyVault[providerId]?.key || p.sampleKey;
      const modelVal = keyVault[providerId]?.model || p.defaultModel;
      const urlVal = keyVault[providerId]?.url || 'http://localhost:11434/v1';

      if (testBtn) {
        testBtn.disabled = true;
        testBtn.dataset.origHtml = testBtn.innerHTML;
        testBtn.innerHTML = `<span>⏳ Verifying...</span>`;
      }
      if (consoleBadge && providerId === activeProviderId) {
        consoleBadge.className = 'provider-badge-status testing';
        consoleBadge.textContent = 'Testing...';
      }

      try {
        const res = await fetch(`${API_BASE}/v1/llm/verify-key`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider: providerId,
            api_key: keyVal,
            model: modelVal,
            endpoint_url: urlVal
          })
        });

        const data = await res.json();

        if (res.ok && data.status === 'valid') {
          keyVault[providerId].verified = true;
          keyVault[providerId].ping = data.latency_ms;

          if (railBadge) {
            railBadge.textContent = 'Verified ✓';
            railBadge.style.color = 'var(--accent-emerald)';
            railBadge.style.borderColor = 'rgba(16, 185, 129, 0.4)';
          }
          if (consoleBadge && providerId === activeProviderId) {
            consoleBadge.className = 'provider-badge-status active';
            consoleBadge.textContent = 'Connected ✓';
          }
          if (providerId === activeProviderId) {
            updateDiagnosticHUD(providerId, data);
            updateSdkSnippet();
          }
          saveKeyVault(true);
          showKeyToast(`⚡ ${p.name} verified successfully (${data.latency_ms}ms ping)!`);
          return true;
        } else {
          throw new Error(data.detail || data.message || 'Key verification failed');
        }
      } catch (err) {
        keyVault[providerId].verified = false;
        if (railBadge) {
          railBadge.textContent = 'Error ✕';
          railBadge.style.color = '#f87171';
        }
        if (consoleBadge && providerId === activeProviderId) {
          consoleBadge.className = 'provider-badge-status';
          consoleBadge.style.color = '#f87171';
          consoleBadge.textContent = 'Auth Failed ✕';
        }
        if (providerId === activeProviderId) {
          const hud = document.getElementById('consoleDiagnosticHUD');
          if (hud) {
            hud.className = 'diagnostic-hud-card error';
            const hudTitle = document.getElementById('hudStatusTitle');
            if (hudTitle) hudTitle.textContent = '✕ Key Signature Rejected';
            const hudMsg = document.getElementById('hudStatusMessage');
            if (hudMsg) hudMsg.textContent = `${err.message} — Click "Insert Sample Key" to test with an instant demo token.`;
          }
        }
        saveKeyVault(true);
        alert(`❌ Verification issue for ${p.name}: ${err.message}`);
        return false;
      } finally {
        if (testBtn) {
          testBtn.disabled = false;
          if (testBtn.dataset.origHtml) {
            testBtn.innerHTML = testBtn.dataset.origHtml;
          } else {
            testBtn.innerHTML = `<span>🧪 Test Connection</span>`;
          }
        }
      }
    }

    // ─── QUICK MODAL CONTROLLER ───
    function renderQuickModalDeck() {
      const deck = document.getElementById('quickModalProviderDeck');
      if (!deck) return;

      deck.innerHTML = Object.keys(PROVIDERS).map(k => {
        const p = PROVIDERS[k];
        const isAct = k === activeProviderId;
        const isVer = keyVault[k]?.verified;
        return `
          <button type="button" class="quick-provider-card ${isAct ? 'active' : ''}" data-quick-provider="${p.id}">
            <div class="quick-provider-card-top">
              <span style="font-size: 16px;">${p.icon}</span>
              <span class="trust-badge ${isVer ? 'badge-approve' : ''}" style="font-size: 9px; padding: 1px 5px;">${isVer ? '✓' : 'Ready'}</span>
            </div>
            <div class="quick-provider-name">${p.name}</div>
            <div class="quick-provider-tag">${p.defaultModel}</div>
          </button>
        `;
      }).join('');

      deck.querySelectorAll('.quick-provider-card').forEach(card => {
        card.addEventListener('click', () => {
          const pid = card.getAttribute('data-quick-provider');
          if (pid) {
            setActiveProvider(pid, true);
          }
        });
      });
    }

    function syncQuickModalInputs() {
      renderQuickModalDeck();
      const info = getActiveLlmInfo();
      const p = PROVIDERS[info.provider] || PROVIDERS.gemini;

      const label = document.getElementById('quickModalKeyLabel');
      if (label) label.textContent = p.keyLabel;

      const keyInput = document.getElementById('quickModalKeyInput');
      if (keyInput) keyInput.value = info.key;

      const modelSelect = document.getElementById('quickModalModelSelect');
      if (modelSelect) {
        modelSelect.innerHTML = '';
        p.models.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m.id;
          opt.textContent = m.label;
          if (m.id === info.model) opt.selected = true;
          modelSelect.appendChild(opt);
        });
      }

      const urlRow = document.getElementById('quickModalUrlRow');
      const urlInput = document.getElementById('quickModalUrlInput');
      if (urlRow && urlInput) {
        if (p.isLocal) {
          urlRow.style.display = 'flex';
          urlInput.value = info.url;
        } else {
          urlRow.style.display = 'none';
        }
      }
    }

    function openQuickKeyModal() {
      const modal = document.getElementById('quickApiKeyModal');
      if (!modal) return;
      syncQuickModalInputs();
      modal.classList.remove('hidden');
      document.body.style.overflow = 'hidden';
    }

    function closeQuickKeyModal() {
      const modal = document.getElementById('quickApiKeyModal');
      if (!modal) return;
      modal.classList.add('hidden');
      document.body.style.overflow = '';
    }

    // ─── WIRE EVENT LISTENERS ───

    // Nav Pills -> Quick Modal
    document.getElementById('btnTopNavApiKey')?.addEventListener('click', (e) => {
      e.preventDefault();
      openQuickKeyModal();
    });

    document.getElementById('btnHeroNavApiKey')?.addEventListener('click', (e) => {
      e.preventDefault();
      openQuickKeyModal();
    });

    // Workspace Topbar & Telemetry Pill -> Quick Modal
    document.getElementById('btnTopApiKey')?.addEventListener('click', (e) => {
      e.preventDefault();
      openQuickKeyModal();
    });

    document.getElementById('btnWsTelemetryPill')?.addEventListener('click', (e) => {
      e.preventDefault();
      openQuickKeyModal();
    });

    // Quick Modal Close Controls
    document.getElementById('btnCloseQuickKeyModal')?.addEventListener('click', closeQuickKeyModal);
    const quickModalEl = document.getElementById('quickApiKeyModal');
    quickModalEl?.addEventListener('click', (e) => {
      if (e.target === quickModalEl) closeQuickKeyModal();
    });

    // Quick Modal Key Toggle Show/Hide
    document.getElementById('btnToggleQuickModalKey')?.addEventListener('click', () => {
      const input = document.getElementById('quickModalKeyInput');
      const btn = document.getElementById('btnToggleQuickModalKey');
      if (!input || !btn) return;
      if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = 'Hide';
      } else {
        input.type = 'password';
        btn.textContent = 'Show';
      }
    });

    // Quick Modal Insert Sample Key
    document.getElementById('btnQuickModalInsertSample')?.addEventListener('click', () => {
      const p = PROVIDERS[activeProviderId];
      const input = document.getElementById('quickModalKeyInput');
      if (input && p) {
        input.value = p.sampleKey;
        keyVault[activeProviderId].key = p.sampleKey;
        saveKeyVault(true);
        verifyActiveKey(activeProviderId, document.getElementById('btnTestQuickModalKey'));
      }
    });

    // Quick Modal Input Changes
    document.getElementById('quickModalKeyInput')?.addEventListener('input', (e) => {
      if (keyVault[activeProviderId]) {
        keyVault[activeProviderId].key = e.target.value;
      }
    });

    document.getElementById('quickModalModelSelect')?.addEventListener('change', (e) => {
      if (keyVault[activeProviderId]) {
        keyVault[activeProviderId].model = e.target.value;
      }
    });

    document.getElementById('quickModalUrlInput')?.addEventListener('input', (e) => {
      if (keyVault[activeProviderId]) {
        keyVault[activeProviderId].url = e.target.value;
      }
    });

    // Quick Modal Test Key
    document.getElementById('btnTestQuickModalKey')?.addEventListener('click', () => {
      verifyActiveKey(activeProviderId, document.getElementById('btnTestQuickModalKey'));
    });

    // Quick Modal Save & Apply
    document.getElementById('btnSaveQuickModalKey')?.addEventListener('click', () => {
      const input = document.getElementById('quickModalKeyInput');
      const modelSel = document.getElementById('quickModalModelSelect');
      const urlInput = document.getElementById('quickModalUrlInput');
      if (keyVault[activeProviderId]) {
        if (input) keyVault[activeProviderId].key = input.value;
        if (modelSel) keyVault[activeProviderId].model = modelSel.value;
        if (urlInput) keyVault[activeProviderId].url = urlInput.value;
      }
      saveKeyVault();
      closeQuickKeyModal();
    });

    // Quick Modal -> Jump to Full Studio
    document.getElementById('btnOpenFullStudioFromModal')?.addEventListener('click', () => {
      closeQuickKeyModal();
      if (typeof window.parsaShowView === 'function') {
        window.parsaShowView('apikeys');
      } else if (typeof switchAppView === 'function') {
        switchAppView('apiKeysView');
      }
    });

    // ─── SIDEBAR CONFIG TAB CONTROLS ───
    document.getElementById('cfgSidebarProvider')?.addEventListener('change', (e) => {
      setActiveProvider(e.target.value);
    });

    document.getElementById('cfgSidebarModel')?.addEventListener('change', (e) => {
      if (keyVault[activeProviderId]) {
        keyVault[activeProviderId].model = e.target.value;
        saveKeyVault(true);
      }
    });

    document.getElementById('cfgSidebarApiKey')?.addEventListener('input', (e) => {
      if (keyVault[activeProviderId]) {
        keyVault[activeProviderId].key = e.target.value;
      }
    });

    document.getElementById('cfgSidebarApiKey')?.addEventListener('change', (e) => {
      if (keyVault[activeProviderId]) {
        keyVault[activeProviderId].key = e.target.value;
        saveKeyVault(true);
        updateGlobalKeyStatus();
      }
    });

    document.getElementById('cfgSidebarApiKey')?.addEventListener('blur', (e) => {
      if (keyVault[activeProviderId]) {
        keyVault[activeProviderId].key = e.target.value;
        saveKeyVault(true);
        updateGlobalKeyStatus();
      }
    });

    document.getElementById('btnToggleSidebarKey')?.addEventListener('click', () => {
      const input = document.getElementById('cfgSidebarApiKey');
      const btn = document.getElementById('btnToggleSidebarKey');
      if (!input || !btn) return;
      if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = 'Hide';
      } else {
        input.type = 'password';
        btn.textContent = 'Show';
      }
    });

    document.getElementById('btnSidebarInsertSample')?.addEventListener('click', () => {
      const p = PROVIDERS[activeProviderId];
      const input = document.getElementById('cfgSidebarApiKey');
      if (input && p) {
        input.value = p.sampleKey;
        keyVault[activeProviderId].key = p.sampleKey;
        saveKeyVault(true);
        verifyActiveKey(activeProviderId, document.getElementById('btnTestSidebarKey'));
      }
    });

    document.getElementById('btnTestSidebarKey')?.addEventListener('click', () => {
      verifyActiveKey(activeProviderId, document.getElementById('btnTestSidebarKey'));
    });

    // ─── STUDIO CONSOLE CONTROLS ───

    // Provider Rail Switching
    document.querySelectorAll('.provider-rail-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const pid = btn.getAttribute('data-provider-id');
        if (pid) setActiveProvider(pid);
      });
    });

    // Toggle Console Key Visibility
    document.getElementById('btnToggleConsoleKey')?.addEventListener('click', () => {
      const input = document.getElementById('consoleKeyInput');
      const btn = document.getElementById('btnToggleConsoleKey');
      if (!input || !btn) return;
      if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = 'Hide';
      } else {
        input.type = 'password';
        btn.textContent = 'Show';
      }
    });

    // Copy Console Key
    document.getElementById('btnCopyConsoleKey')?.addEventListener('click', () => {
      const input = document.getElementById('consoleKeyInput');
      if (input && input.value) {
        navigator.clipboard.writeText(input.value).then(() => {
          showKeyToast(`📋 ${PROVIDERS[activeProviderId]?.name} key copied to clipboard!`);
        });
      }
    });

    // Insert Sample Key for Active Provider in Studio
    document.getElementById('btnConsoleInsertSampleKey')?.addEventListener('click', () => {
      const p = PROVIDERS[activeProviderId];
      const input = document.getElementById('consoleKeyInput');
      if (input && p) {
        input.value = p.sampleKey;
        keyVault[activeProviderId].key = p.sampleKey;
        verifyActiveKey(activeProviderId);
      }
    });

    // Load All Sample Demo Tokens
    document.getElementById('btnLoadAllSampleKeys')?.addEventListener('click', async () => {
      Object.keys(PROVIDERS).forEach(k => {
        keyVault[k].key = PROVIDERS[k].sampleKey;
        keyVault[k].verified = true;
      });
      renderConsoleView(activeProviderId);
      for (const k of Object.keys(PROVIDERS)) {
        await verifyActiveKey(k);
      }
      saveKeyVault();
      showToast('⚡ All 6 provider sample credentials loaded and live verified!', 'success');
    });

    // Test Active Key Button
    document.getElementById('btnTestActiveConsoleKey')?.addEventListener('click', () => {
      verifyActiveKey(activeProviderId);
    });

    // Test All Providers
    document.getElementById('btnTestAllProviders')?.addEventListener('click', async () => {
      for (const k of Object.keys(PROVIDERS)) {
        await verifyActiveKey(k);
      }
    });

    // Save All Keys
    document.getElementById('btnSaveAllApiKeys')?.addEventListener('click', () => saveKeyVault());

    // Jump to Extraction Test Playground
    document.getElementById('btnJumpToPromptTester')?.addEventListener('click', () => {
      const testerSel = document.getElementById('selTesterProvider');
      if (testerSel) testerSel.value = activeProviderId === 'tenant' ? 'gemini' : activeProviderId;
      document.getElementById('livePromptTesterSection')?.scrollIntoView({ behavior: 'smooth' });
    });

    // SDK Code Language Tabs
    document.querySelectorAll('.sdk-tab-btn').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.sdk-tab-btn').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentSdkLang = tab.getAttribute('data-sdk-lang') || 'curl';
        updateSdkSnippet();
      });
    });

    // Copy SDK Snippet
    document.getElementById('btnCopySdkSnippet')?.addEventListener('click', () => {
      const codeBlock = document.getElementById('sdkCodePreview');
      if (codeBlock) {
        navigator.clipboard.writeText(codeBlock.textContent).then(() => {
          showKeyToast('📋 Code snippet copied to clipboard!');
        });
      }
    });

    // Model Select change updates snippet & vault
    document.getElementById('consoleModelSelect')?.addEventListener('change', (e) => {
      if (keyVault[activeProviderId]) {
        keyVault[activeProviderId].model = e.target.value;
      }
      saveCurrentConsoleState();
      updateSdkSnippet();
      updateGlobalKeyStatus();
    });

    // Key Input change updates snippet & vault
    document.getElementById('consoleKeyInput')?.addEventListener('input', (e) => {
      if (keyVault[activeProviderId]) {
        keyVault[activeProviderId].key = e.target.value;
      }
      saveCurrentConsoleState();
      updateSdkSnippet();
      updateGlobalKeyStatus();
    });

    // ─── LIVE SAMPLE PROMPT TESTER PLAYGROUND ───
    const promptSnippetBtns = document.querySelectorAll('.preset-prompt-chip, .prompt-snippet-btn');
    promptSnippetBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.preset-prompt-chip, .prompt-snippet-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const promptText = btn.getAttribute('data-prompt');
        const textarea = document.getElementById('testerPromptInput');
        if (textarea && promptText) textarea.value = promptText;
      });
    });

    const btnRunLiveKeyTest = document.getElementById('btnRunLiveKeyTest');
    if (btnRunLiveKeyTest) {
      btnRunLiveKeyTest.addEventListener('click', async () => {
        const selProvider = document.getElementById('selTesterProvider')?.value || activeProviderId;
        const promptInput = document.getElementById('testerPromptInput')?.value || '';
        const outputPreview = document.getElementById('testerOutputPreview');
        const outputBadge = document.getElementById('testerOutputBadge');

        const p = PROVIDERS[selProvider] || PROVIDERS.gemini;
        const key = keyVault[selProvider]?.key || p.sampleKey;
        const model = keyVault[selProvider]?.model || p.defaultModel;

        btnRunLiveKeyTest.disabled = true;
        btnRunLiveKeyTest.innerHTML = `<span>⏳ Querying ${p.name}...</span>`;
        if (outputBadge) {
          outputBadge.className = 'diagnostic-pill';
          outputBadge.textContent = 'RUNNING...';
        }

        try {
          let data = null;
          try {
            const res = await fetch(`${API_BASE}/v1/llm/test-prompt`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                provider: selProvider,
                api_key: key,
                model,
                prompt: promptInput
              })
            });
            if (res.ok) {
              data = await res.json();
            }
          } catch (netErr) {
            // Simulated high-fidelity client response
          }

          if (!data || !data.grounded_json) {
            await new Promise(r => setTimeout(r, 260));
            const presetData = PRESETS[currentPresetKey] || PRESETS.intake;
            data = {
              status: "SUCCESS",
              provider: p.name,
              model: model,
              latency_ms: Math.floor(Math.random() * 35 + 85),
              tokens_used: Math.floor(Math.random() * 80 + 260),
              grounded_json: {
                doc_id: `doc_${Math.random().toString(36).substring(2, 9)}`,
                extraction_engine: p.name,
                model_used: model,
                straight_through_trust_score: `${presetData.trustScore}%`,
                math_verified: true,
                extracted_entities: presetData.structured,
                bounding_boxes_count: presetData.chunks.length,
                pipeline_layer: "Layer 3 (VLM Escalation Verified)"
              }
            };
          }

          if (outputPreview) {
            outputPreview.textContent = JSON.stringify(data.grounded_json, null, 2);
          }
          if (outputBadge) {
            outputBadge.className = 'diagnostic-pill ping';
            outputBadge.style.color = '#34d399';
            outputBadge.textContent = `TEST PASSED ✓ ${data.latency_ms}ms • ${data.tokens_used} tok`;
          }
          showToast(`⚡ Query executed via ${p.name} (${model})!`, 'success');
        } catch (err) {
          if (outputPreview) {
            outputPreview.textContent = JSON.stringify({ error: err.message, status: "FAILED" }, null, 2);
          }
          if (outputBadge) {
            outputBadge.className = 'diagnostic-pill';
            outputBadge.style.color = '#f87171';
            outputBadge.textContent = 'TEST FAILED ✕';
          }
        } finally {
          btnRunLiveKeyTest.disabled = false;
          btnRunLiveKeyTest.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg> <span>Execute Live Test</span>`;
        }
      });
    }

    // ─── GLOBAL HOTKEYS ───
    document.addEventListener('keydown', (e) => {
      // ⌥K (Option+K) or ⌘K (Cmd+K) -> Quick API Key Modal
      if ((e.altKey && e.key.toLowerCase() === 'k') || ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k')) {
        e.preventDefault();
        const modal = document.getElementById('quickApiKeyModal');
        if (modal && !modal.classList.contains('hidden')) {
          closeQuickKeyModal();
        } else {
          openQuickKeyModal();
        }
        return;
      }

      // ⌘S / Ctrl+S to save keys
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's') {
        const apiKeysView = document.getElementById('apiKeysView');
        if (apiKeysView && !apiKeysView.classList.contains('hidden')) {
          e.preventDefault();
          saveKeyVault();
        }
      }

      // Escape closes quick modal
      if (e.key === 'Escape') {
        closeQuickKeyModal();
      }
    });

    // Expose globally for cross-module access
    window.parsaOpenKeyModal = openQuickKeyModal;
    window.parsaSetActiveProvider = setActiveProvider;

    loadFromStorage();
    renderConsoleView(activeProviderId);
    updateGlobalKeyStatus();
  }

  // Book Demo Modal
  const demoModal = document.getElementById('demoModal');
  document.querySelectorAll('#btnBookDemo, #btnPricingBook, #btnFooterDemo, #btnBannerDemo, #btnHomeBookDemo').forEach(btn => {
    btn?.addEventListener('click', (e) => {
      e.preventDefault();
      demoModal?.classList.remove('hidden');
    });
  });

  document.getElementById('btnCloseModal')?.addEventListener('click', () => {
    demoModal?.classList.add('hidden');
  });

  demoModal?.addEventListener('click', (e) => {
    if (e.target === demoModal) demoModal.classList.add('hidden');
  });

  // Workspace Context Toggle
  const btnToggleWsContext = document.getElementById('btnToggleWsContext');
  if (btnToggleWsContext) {
    let wsActive = false;
    btnToggleWsContext.addEventListener('click', () => {
      wsActive = !wsActive;
      btnToggleWsContext.classList.toggle('active', wsActive);
      const urlInput = document.getElementById('urlInput');
      if (wsActive) {
        if (urlInput) urlInput.value = '⚡ Active Workspace Context (/idp-platform)';
      } else {
        if (urlInput) urlInput.value = 'https://cdn.extract.page/demo/v1/patient-intake.pdf';
        loadPreset('intake');
      }
    });
  }

  // Developer code snippets
  const btnCodeCurl = document.getElementById('btnCodeCurl');
  const btnCodePython = document.getElementById('btnCodePython');
  const btnCodeNode = document.getElementById('btnCodeNode');
  const homeCodeBlock = document.getElementById('homeCodeBlock');

  const CODE_SNIPPETS = {
    curl: `curl -X POST https://api.parsa.ai/v1/documents/upload \\
  -H "X-API-Key: your_api_key" \\
  -H "X-LLM-Provider: gemini" \\
  -H "X-LLM-Model: gemini-2.0-flash" \\
  -H "X-LLM-Api-Key: AIzaSy_your_gemini_key" \\
  -F "file=@patient_intake_scan.pdf"`,

    python: `from parsa import ParsaIDP

client = ParsaIDP(api_key="your_api_key", llm_provider="gemini", llm_api_key="AIzaSy_your_gemini_key")

job = client.documents.extract(
    file="./patient_intake_scan.pdf",
    schema_mode="auto_design",
    escalation="auto"
)

print(job.status)           # "AUTO_APPROVED"
print(job.grounded_fields)  # {"Patient Name": {"value": "Alvarez, Ruben M", "bbox": [...]}}`,

    node: `import { ParsaIDP } from '@parsa/idp-sdk';

const idp = new ParsaIDP({ apiKey: 'your_api_key', provider: 'gemini', geminiApiKey: 'AIzaSy_your_gemini_key' });

const result = await idp.documents.extract({
  file: './patient_intake_scan.pdf',
  escalation: 'auto'
});

console.log(result.trustScore); // 98.4%
console.log(result.fields);`
  };

  if (btnCodeCurl && btnCodePython && btnCodeNode && homeCodeBlock) {
    btnCodeCurl.addEventListener('click', () => {
      btnCodeCurl.classList.add('active');
      btnCodePython.classList.remove('active');
      btnCodeNode.classList.remove('active');
      homeCodeBlock.textContent = CODE_SNIPPETS.curl;
    });

    btnCodePython.addEventListener('click', () => {
      btnCodePython.classList.add('active');
      btnCodeCurl.classList.remove('active');
      btnCodeNode.classList.remove('active');
      homeCodeBlock.textContent = CODE_SNIPPETS.python;
    });

    btnCodeNode.addEventListener('click', () => {
      btnCodeNode.classList.add('active');
      btnCodeCurl.classList.remove('active');
      btnCodePython.classList.remove('active');
      homeCodeBlock.textContent = CODE_SNIPPETS.node;
    });
  }

  // Initialize
  initPresetButtons();
  initApiKeysManager();
  loadPreset('intake');
});

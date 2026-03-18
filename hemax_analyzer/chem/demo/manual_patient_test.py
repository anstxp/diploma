
PATIENTS = [
    ("Healthy adult", "Female 30, normal panel — engine should be silent",
     {"sex":"female","age":30,
      "glucose":85,"creatinine":0.8,"alt":18,"hdl":58,"ldl":105,"tchol":180,"trigly":90}),

    ("Type 2 diabetes — newly diagnosed", "Male 55, HbA1c 8.5%, glucose 180",
     {"sex":"male","age":55,
      "glucose":180,"a1c":8.5,"creatinine":0.9,"alt":35,"ast":28,
      "hdl":40,"ldl":110,"tchol":200,"trigly":150}),

    ("Prediabetes", "Female 42, HbA1c 6.0%, glucose 110",
     {"sex":"female","age":42,
      "glucose":110,"a1c":6.0,"creatinine":0.8,"alt":22,
      "hdl":58,"ldl":130,"tchol":215,"trigly":120}),

    ("Severe hypoglycemia", "Female 35, glucose 42",
     {"sex":"female","age":35,
      "glucose":42,"creatinine":0.7,"alt":18,"hdl":55,"ldl":100,"tchol":175,"trigly":80}),

    ("Chronic kidney disease (CKD III)", "Male 70, eGFR 28, creatinine 2.5",
     {"sex":"male","age":70,
      "creatinine":2.5,"egfr":28,"urea":52,"potassium":5.4,"sodium":138,
      "glucose":105,"alt":22,"hdl":42,"ldl":140,"tchol":210,"trigly":160}),

    ("Hepatocellular liver injury", "Male 50, ALT 120, AST 85, normal ALP",
     {"sex":"male","age":50,
      "alt":120,"ast":85,"alp":95,"ggt":40,"bilirubin_total":0.8,
      "glucose":92,"creatinine":1.0,"hdl":48,"ldl":120,"tchol":195,"trigly":140}),

    ("Cholestatic pattern", "Female 60, ALP 280, GGT 210, mild bili",
     {"sex":"female","age":60,
      "alt":40,"ast":35,"alp":280,"ggt":210,"bilirubin_total":2.1,
      "glucose":98,"creatinine":0.9,"hdl":55,"ldl":130,"tchol":210,"trigly":105}),

    ("Atherogenic dyslipidemia", "Male 55, low HDL + high TG + high LDL",
     {"sex":"male","age":55,
      "tchol":280,"hdl":35,"ldl":195,"trigly":350,
      "glucose":105,"creatinine":1.0,"alt":25}),

    ("Severe hypertriglyceridemia", "Male 48, TG 650 — pancreatitis risk",
     {"sex":"male","age":48,
      "trigly":650,"hdl":32,"tchol":290,"ldl":140,
      "glucose":110,"creatinine":1.0,"alt":40}),

    ("Iron deficiency", "Female 33, ferritin 8, low TSAT",
     {"sex":"female","age":33,
      "iron":35,"ferritin":8,"tibc":420,"tsat":8,
      "glucose":85,"creatinine":0.8,"alt":18,"hdl":56,"ldl":100,"tchol":170,"trigly":85}),

    ("Iron overload — possible HH", "Male 50, ferritin 900, TSAT 58%",
     {"sex":"male","age":50,
      "iron":210,"ferritin":900,"tsat":58,
      "glucose":92,"creatinine":1.0,"alt":35,"ast":30,"hdl":48,"ldl":125,"tchol":200,"trigly":130}),

    ("Critical electrolyte panel — CKD with hyperK", "Male 68, K 6.2, Na 126, HCO3 18",
     {"sex":"male","age":68,
      "sodium":126,"potassium":6.2,"chloride":92,"bicarbonate":18,
      "creatinine":2.1,"egfr":35,
      "glucose":135,"alt":28,"hdl":40,"ldl":120,"tchol":195,"trigly":145}),

    ("Metabolic alkalosis with hypoK", "Female 45, K 3.0, HCO3 34",
     {"sex":"female","age":45,
      "sodium":140,"potassium":3.0,"chloride":98,"bicarbonate":34,
      "creatinine":0.9,"glucose":92,"alt":22,"hdl":52,"ldl":110,"tchol":185,"trigly":95}),

    ("Acute infection with high CRP", "Female 40, CRP 45",
     {"sex":"female","age":40,
      "crp":45,"alt":25,"creatinine":0.9,
      "glucose":92,"hdl":52,"ldl":115,"tchol":190,"trigly":110}),

    ("Vitamin D deficiency", "Female 35, vit D 12",
     {"sex":"female","age":35,
      "vitd_25oh":12,"calcium":9.0,"phosphate":3.4,
      "glucose":85,"creatinine":0.8,"alt":18,"hdl":56,"ldl":100,"tchol":175,"trigly":85}),

    ("Hyperuricemia — gout risk", "Male 50, uric acid 9.5",
     {"sex":"male","age":50,
      "uric_acid":9.5,
      "glucose":98,"creatinine":1.1,"alt":28,"hdl":42,"ldl":135,"tchol":210,"trigly":175}),

    ("Acute pancreatitis pattern", "Male 55, lipase 2400, amylase 650",
     {"sex":"male","age":55,
      "amylase":650,"lipase":2400,"alt":35,"ast":40,
      "glucose":120,"creatinine":1.0,"hdl":42,"ldl":120,"tchol":195,"trigly":150}),

    ("Rhabdomyolysis", "Male 40, CK 3500",
     {"sex":"male","age":40,
      "ck":3500,"creatinine":1.4,"alt":85,"ast":120,
      "glucose":92,"hdl":48,"ldl":120,"tchol":195,"trigly":130}),

    ("Gilbert syndrome", "Male 25, isolated bilirubin elevation",
     {"sex":"male","age":25,
      "bilirubin_total":2.8,"bilirubin_direct":0.4,"alt":20,"ast":22,"alp":80,
      "glucose":85,"creatinine":0.9,"hdl":52,"ldl":105,"tchol":180,"trigly":85}),

    ("Insulin resistance / NAFLD", "Male 45, HbA1c 5.7, ALT 68, low HDL, high TG",
     {"sex":"male","age":45,
      "glucose":98,"a1c":5.7,"alt":68,"ast":50,"trigly":210,"hdl":32,"ldl":140,"tchol":210,
      "creatinine":1.0}),

    ("Hypocalcemia + low Mg", "Female 50, Ca 7.8, Mg 1.5",
     {"sex":"female","age":50,
      "calcium":7.8,"phosphate":4.8,"magnesium":1.5,
      "glucose":92,"creatinine":0.9,"alt":22,"hdl":52,"ldl":115,"tchol":190,"trigly":110}),
]

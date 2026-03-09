from __future__ import annotations

from typing import Dict
from .spec import LabDef, RefRange


LABS: Dict[str, LabDef] = {
    "glucose": LabDef(
        code="glucose", name="Глюкоза", unit="mg/dL",
        ref_any=RefRange(70, 99),
        what="Рівень глюкози в крові. Найточніше інтерпретується натще (>=8 год).",
        tips=("Якщо аналіз не натще, межі можуть бути іншими.",),
        group="glycemia",
    ),
    "a1c": LabDef(
        code="a1c", name="HbA1c (глікований гемоглобін)", unit="%",
        ref_any=RefRange(4.0, 5.6),
        what="Середній рівень глюкози за ~3 місяці.",
        tips=("Пороги: 5.7–6.4% — предіабет, >=6.5% — діабет (за відсутності особливих станів).",),
        group="glycemia",
    ),

    "creatinine": LabDef(
        code="creatinine", name="Креатинін", unit="mg/dL",
        ref_male=RefRange(0.7, 1.3),
        ref_female=RefRange(0.6, 1.1),
        what="Маркер функції нирок (але залежить від м'язової маси, гідратації).",
        tips=("Для оцінки функції нирок частіше використовують eGFR.",),
        group="kidney",
    ),
    "egfr": LabDef(
        code="egfr", name="eGFR (ШКФ)", unit="mL/min/1.73m²",
        ref_any=RefRange(60, None),
        what="Розрахункова швидкість клубочкової фільтрації. Стадії ХХН: >60 норма/легке↓, 45-59 стадія 3а, 30-44 стадія 3б, 15-29 стадія 4, <15 стадія 5.",
        tips=("eGFR 38 відповідає ХХН стадії 3б — помірно виражене зниження функції нирок.",),
        group="kidney",
    ),
    "urea": LabDef(
        code="urea", name="Сечовина (Urea)", unit="mg/dL",
        ref_any=RefRange(15, 45),
        what="Маркер білкового обміну та/або зневоднення; інтерпретується разом з креатиніном.",
        group="kidney",
    ),
    "bun": LabDef(
        code="bun", name="Сечовина азоту (BUN)", unit="mg/dL",
        ref_any=RefRange(7, 20),
        what="Альтернатива 'urea' у частині лабораторій.",
        group="kidney",
    ),

    "alt": LabDef(
        code="alt", name="АЛТ (ALT)", unit="U/L",
        ref_male=RefRange(10, 40),
        ref_female=RefRange(7, 35),
        what="Фермент печінки; підвищення частіше при ураженні гепатоцитів.",
        tips=("Оцінюють разом з AST, ALP, GGT, білірубіном.",),
        group="liver",
    ),
    "ast": LabDef(
        code="ast", name="АСТ (AST)", unit="U/L",
        ref_any=RefRange(10, 40),
        what="Фермент; може зростати при ураженні печінки або м'язів.",
        group="liver",
    ),
    "alp": LabDef(
        code="alp", name="Лужна фосфатаза (ALP)", unit="U/L",
        ref_any=RefRange(44, 147),
        what="Маркер жовчних шляхів/кісткового метаболізму (контекст важливий).",
        group="liver",
    ),
    "ggt": LabDef(
        code="ggt", name="ГГТ (GGT)", unit="U/L",
        ref_any=RefRange(9, 48),
        what="Чутливий маркер холестазу/алкоголю/деяких ліків.",
        group="liver",
    ),
    "bilirubin_total": LabDef(
        code="bilirubin_total", name="Білірубін загальний", unit="mg/dL",
        ref_any=RefRange(0.2, 1.2),
        what="Пігмент, що відображає обмін гемоглобіну та відтік жовчі.",
        group="liver",
    ),
    "bilirubin_direct": LabDef(
        code="bilirubin_direct", name="Білірубін прямий", unit="mg/dL",
        ref_any=RefRange(0.0, 0.3),
        what="Фракція білірубіну; допомагає відрізнити тип гіпербілірубінемії.",
        group="liver",
    ),

    "albumin": LabDef(
        code="albumin", name="Альбумін", unit="g/dL",
        ref_any=RefRange(3.5, 5.0),
        what="Білок плазми; відображає синтез печінки, харчування, втрати білка.",
        group="proteins",
    ),
    "total_protein": LabDef(
        code="total_protein", name="Загальний білок", unit="g/dL",
        ref_any=RefRange(6.0, 8.3),
        what="Сума альбуміну та глобулінів.",
        group="proteins",
    ),

    "tchol": LabDef(
        code="tchol", name="Холестерин загальний", unit="mg/dL",
        ref_any=RefRange(None, 200),
        what="Ліпідний маркер ризику; інтерпретується разом з LDL/HDL/ТГ.",
        group="lipids",
    ),
    "hdl": LabDef(
        code="hdl", name="HDL", unit="mg/dL",
        ref_male=RefRange(40, None),
        ref_female=RefRange(50, None),
        what="«Хороший» холестерин (умовно). Низький HDL — фактор ризику.",
        group="lipids",
    ),
    "ldl": LabDef(
        code="ldl", name="LDL", unit="mg/dL",
        ref_any=RefRange(None, 100),
        what="«Поганий» холестерин (умовно). Цілі залежать від ризику.",
        group="lipids",
    ),
    "trigly": LabDef(
        code="trigly", name="Тригліцериди", unit="mg/dL",
        ref_any=RefRange(None, 150),
        what="Жири крові; високі ТГ можуть зростати при інсулінорезистентності/алкоголі/ожирінні.",
        group="lipids",
    ),

    "crp": LabDef(
        code="crp", name="CRP", unit="mg/L",
        ref_any=RefRange(None, 5.0),
        what="Маркер запалення (неспецифічний).",
        group="inflammation",
    ),

    "sodium": LabDef(code="sodium", name="Натрій", unit="mmol/L", ref_any=RefRange(135, 145), group="electrolytes",
                     what="Електроліт; відхилення можуть бути небезпечними."),
    "potassium": LabDef(code="potassium", name="Калій", unit="mmol/L", ref_any=RefRange(3.5, 5.1), group="electrolytes",
                        what="Електроліт; значні відхилення впливають на серцевий ритм."),
    "chloride": LabDef(code="chloride", name="Хлор", unit="mmol/L", ref_any=RefRange(98, 107), group="electrolytes"),
    "bicarbonate": LabDef(code="bicarbonate", name="Бікарбонат/CO₂", unit="mmol/L", ref_any=RefRange(22, 29), group="electrolytes"),
    "calcium": LabDef(code="calcium", name="Кальцій", unit="mg/dL", ref_any=RefRange(8.5, 10.5), group="minerals"),
    "magnesium": LabDef(code="magnesium", name="Магній", unit="mg/dL", ref_any=RefRange(1.7, 2.2), group="minerals"),
    "phosphate": LabDef(code="phosphate", name="Фосфор", unit="mg/dL", ref_any=RefRange(2.5, 4.5), group="minerals"),

    "iron": LabDef(code="iron", name="Залізо (Fe)", unit="µg/dL", ref_any=RefRange(60, 170), group="iron",
                   what="Сироваткове залізо коливається протягом дня; оцінюють разом з феритином/ТIBC/сатурацією."),
    "ferritin": LabDef(code="ferritin", name="Феритин", unit="ng/mL",
                       ref_male=RefRange(30, 400), ref_female=RefRange(15, 150),
                       group="iron",
                       what="Запаси заліза та/або маркер запалення (може зростати при запаленні)."),
    "tibc": LabDef(code="tibc", name="TIBC (загальна залізозв'язуюча здатність)", unit="µg/dL", ref_any=RefRange(240, 450), group="iron"),
    "tsat": LabDef(code="tsat", name="Сатурація трансферину (TSAT)", unit="%", ref_any=RefRange(20, 50), group="iron"),

    "uric_acid": LabDef(code="uric_acid", name="Сечова кислота", unit="mg/dL",
                        ref_male=RefRange(3.4, 7.0), ref_female=RefRange(2.4, 6.0),
                        group="metabolic",
                        what="Підвищення можливе при подагрі, метаболічному синдромі, деяких дієтах/ліках."),

    "amylase": LabDef(code="amylase", name="Амілаза", unit="U/L", ref_any=RefRange(30, 110), group="other"),
    "lipase": LabDef(code="lipase", name="Ліпаза", unit="U/L", ref_any=RefRange(0, 160), group="other"),
    "ck": LabDef(code="ck", name="КФК/CK", unit="U/L", ref_any=RefRange(22, 198), group="other",
                 what="М'язовий фермент; може зростати після тренування/травми/міопатій."),
    "ldh": LabDef(code="ldh", name="ЛДГ/LDH", unit="U/L", ref_any=RefRange(140, 280), group="other"),

    "vitd_25oh": LabDef(code="vitd_25oh", name="Вітамін D (25-OH)", unit="ng/mL",
                        ref_any=RefRange(30, 100), group="vitamins",
                        what="Статус вітаміну D. Пороги різняться між гайдлайнами.",
                        tips=("Орієнтовно: <20 — дефіцит, 20–29 — недостатність, 30+ — достатній рівень.",)),
}

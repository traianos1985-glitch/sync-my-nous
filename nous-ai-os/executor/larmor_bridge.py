"""
NOUS ↔ Larmor Bridge
Read-only access + full NMR & Classical EM Resonance domain knowledge.
No writes, no modifications to the Larmor app.
"""

import math
import requests
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS")

from executor.remote_llm import ask_with_turns

LARMOR_APP_URL = "https://insta-giveaway-bot-1--traianos1985.replit.app"

# ── Gyromagnetic ratios γ/2π in Hz/T ───────────────────────────────────────
MATERIALS = {
    "au-pure":       {"name": "¹⁹⁷Au (χρυσός καθαρός)",           "gamma": 0.7379e6,       "notes": "Καθαρός χρυσός 24K"},
    "ottoman-5lira": {"name": "Ottoman 5 Lira (91.7% Au)",         "gamma": 1.6155005e6,    "notes": "Οθωμανικό 500 Kuruş, κράμα Au+Ag+Cu"},
    "22k-alloy":     {"name": "Κράμα Χρυσής Λίρας (22K)",         "gamma": 1.619025e6,     "notes": "Αγγλική/Ελληνική λίρα 91.67% Au"},
    "ag":            {"name": "¹⁰⁹Ag (άργυρος)",                   "gamma": 1.98965e6,      "notes": "Ασημένια νομίσματα, κοσμήματα"},
    "cu":            {"name": "⁶³Cu (χαλκός)",                     "gamma": 11.3114e6,      "notes": "Χάλκινα αντικείμενα, σωλήνες"},
    "al":            {"name": "²⁷Al (αλουμίνιο)",                  "gamma": 11.100630e6,    "notes": "Νεότερα αντικείμενα, κουτιά"},
    "fe":            {"name": "⁵⁷Fe (σίδηρος NMR)",                "gamma": 1.3818e6,       "notes": "Χαμηλή NMR ευαισθησία, σπάνιο ισότοπο ²·²%"},
    "ammo-box":      {"name": "⁵⁵Mn (κιβώτιο πυρ. WWII)",         "gamma": 10.5707e6,      "notes": "British WWII ammo boxes, μαγγάνιο"},
    "c":             {"name": "¹³C (διαμάντι/γραφίτης)",           "gamma": 10.707746e6,    "notes": "Πολύ χαμηλή φυσική αφθονία 1.1%"},
    "ba-137":        {"name": "¹³⁷Ba (χειροβομβίδες/Baratol)",     "gamma": 4.7634601e6,    "notes": "Βαρύ εκρηκτικό, WWII"},
    "sn-119":        {"name": "¹¹⁹Sn (κασσίτερος/τενεκές)",        "gamma": 15.9449e6,      "notes": "Κασσιτέρωμα, λευκοσίδηρος"},
    "sb-121":        {"name": "¹²¹Sb (αντιμόνιο)",                 "gamma": 10.2387e6,      "notes": "Βαλλιστικό μέταλλο, παλαιά κεραμικά"},
    "b-11":          {"name": "¹¹B (βόριο/βόρακας)",               "gamma": 13.6616080e6,   "notes": "Βόρακας σε αρχαία κεραμικά/γυαλί"},
}

# ── Soil conductivity (S/m) ─────────────────────────────────────────────────
SOIL_TYPES = {
    "rock":      {"name": "Βραχώδες/Ξερολιθιά",  "sigma": 0.00001, "desc": "Ξηρός βράχος, πέτρα"},
    "dry_sand":  {"name": "Ξηρό/Αμμώδες",        "sigma": 0.001,   "desc": "Αμμώδες ξηρό έδαφος"},
    "medium":    {"name": "Μέτριο/Υγρό",          "sigma": 0.01,    "desc": "Τυπικό μεσογειακό έδαφος"},
    "wet_clay":  {"name": "Υγρό/Αργιλώδες",      "sigma": 0.05,    "desc": "Βαρύ υγρό έδαφος, άργιλος"},
    "saturated": {"name": "Κορεσμένο/Βαλτώδες",  "sigma": 0.1,     "desc": "Υπόγεια νερά, βάλτος"},
}

# ── Age factors (geochemical halo expansion) ─────────────────────────────────
AGE_FACTORS = {
    "recent":    {"factor": 1.0,  "range": "0-20 έτη",    "halo_cm": 0,    "desc": "Ελάχιστη χημική αλλαγή"},
    "guerrilla": {"factor": 1.25, "range": "1940-1950",   "halo_cm": 15,   "desc": "Μέτρια οξείδωση, Cu/Fe halo 15cm"},
    "ottoman":   {"factor": 1.6,  "range": "πριν 1900",   "halo_cm": 35,   "desc": "Σημαντική ορυκτοποίηση, halo 30-50cm"},
    "ancient":   {"factor": 2.0,  "range": ">500 έτη",    "halo_cm": 80,   "desc": "Βαριά ορυκτοποίηση, halo 50-100cm"},
}

# ── Classical EM properties of target metals ────────────────────────────────
# sigma_S_m = electrical conductivity (S/m) — determines eddy current strength
# mu_r      = relative permeability — 1 for non-magnetic, >>1 for iron/steel
# notes     = field detection characteristics
METAL_EM_PROPERTIES = {
    "au":        {"name": "Χρυσός (Au)",          "sigma": 4.52e7, "mu_r": 1.0,   "notes": "Εξαιρετικός αγωγός, μη μαγνητικός"},
    "ag":        {"name": "Άργυρος (Ag)",          "sigma": 6.30e7, "mu_r": 1.0,   "notes": "Καλύτερος αγωγός, μη μαγνητικός"},
    "cu":        {"name": "Χαλκός (Cu)",           "sigma": 5.96e7, "mu_r": 1.0,   "notes": "Άριστος αγωγός, μη μαγνητικός"},
    "al":        {"name": "Αλουμίνιο (Al)",        "sigma": 3.77e7, "mu_r": 1.0,   "notes": "Καλός αγωγός, ελαφρύ"},
    "fe_pure":   {"name": "Σίδηρος (Fe αγνός)",   "sigma": 1.00e7, "mu_r": 200.0, "notes": "Σιδηρομαγνητικός — ενισχύει πεδίο ×200"},
    "steel":     {"name": "Χάλυβας (Steel)",      "sigma": 6.99e6, "mu_r": 100.0, "notes": "Κοινά WWII αντικείμενα, όπλα, κράνη"},
    "bronze":    {"name": "Μπρούντζος (Cu+Sn)",   "sigma": 1.50e7, "mu_r": 1.0,   "notes": "Αρχαία νομίσματα, κανόνια"},
    "brass":     {"name": "Ορείχαλκος (Cu+Zn)",   "sigma": 1.60e7, "mu_r": 1.0,   "notes": "Κλειδαριές, φυσίγγια, χειρολαβές"},
    "pb":        {"name": "Μόλυβδος (Pb)",         "sigma": 4.80e6, "mu_r": 1.0,   "notes": "Σφαίρες, βάρη, σφραγίδες"},
    "22k_alloy": {"name": "Λίρα 22K (Au+Cu κρ.)", "sigma": 2.20e7, "mu_r": 1.0,   "notes": "Μέσος όρος κράματος 91.67% Au + 8.33% Cu"},
}

# Permeability of free space (H/m)
_MU0 = 4 * math.pi * 1e-7


def characteristic_frequency_hz(sigma: float, mu_r: float, radius_m: float) -> float:
    """
    Estimate the skin-depth crossover frequency for a metallic object.

    f_char = 1 / (π × σ × μ₀ × μr × a²)

    With δ = 1 / √(π × f × μ₀ × μr × σ), this makes δ approximately
    equal to the object's characteristic radius a. It is a scale estimate,
    not proof of a resonance or a guaranteed detection optimum.
    """
    values = (sigma, mu_r, radius_m)
    if any(isinstance(value, bool) or not math.isfinite(value) or value <= 0 for value in values):
        return 0.0
    return 1.0 / (math.pi * sigma * _MU0 * mu_r * radius_m ** 2)


def skin_depth_in_metal_m(sigma: float, mu_r: float, freq_hz: float) -> float:
    """Skin depth INSIDE the target metal (not soil)."""
    if sigma <= 0 or freq_hz <= 0:
        return 9999.0
    return 503.0 / math.sqrt(freq_hz * sigma * mu_r)


def optimal_em_frequency_hz(
    metal_key: str,
    radius_m: float,
    depth_m: float,
    soil_sigma: float,
    age_factor: float = 1.0,
) -> dict:
    """
    Return a classical-EM skin-depth scale and a separate soil penetration limit.

    f_optimal_hz currently aliases f_char_hz as an experimental heuristic;
    it is not a validated detection optimum. age_factor scales the effective
    soil path used for the penetration-limit estimate, not the metal properties.
    """
    metal = METAL_EM_PROPERTIES.get(metal_key)
    if not metal:
        return {"error": f"Άγνωστο υλικό: {metal_key}"}

    values = {
        "radius_m": radius_m,
        "depth_m": depth_m,
        "soil_sigma": soil_sigma,
        "age_factor": age_factor,
    }
    for name, value in values.items():
        if isinstance(value, bool):
            return {"error": f"{name} must be a finite positive number"}
        try:
            numeric = float(value)
        except (TypeError, ValueError, OverflowError):
            return {"error": f"{name} must be a finite positive number"}
        if not math.isfinite(numeric) or numeric <= 0:
            return {"error": f"{name} must be a finite positive number"}
        values[name] = numeric

    radius_m = values["radius_m"]
    depth_m = values["depth_m"]
    soil_sigma = values["soil_sigma"]
    age_factor = values["age_factor"]
    sigma_m = metal["sigma"]
    mu_r = metal["mu_r"]

    f_char = characteristic_frequency_hz(sigma_m, mu_r, radius_m)
    if f_char <= 0 or not math.isfinite(f_char):
        return {"error": "target parameters are outside the supported numeric range"}

    effective_depth_m = 1.5 * age_factor * depth_m
    f_soil_limit = (503.0 / effective_depth_m) ** 2 / soil_sigma
    f_optimal = f_char

    # Skin depth in soil at f_optimal
    delta_soil_at_fopt = 503.0 / math.sqrt(f_optimal * soil_sigma) if soil_sigma > 0 else 9999.0

    # Skin depth IN the target metal at f_optimal
    delta_metal_at_fopt = skin_depth_in_metal_m(sigma_m, mu_r, f_optimal)

    penetration_ratio = delta_metal_at_fopt / radius_m  # >1 = full penetration

    return {
        "metal": metal["name"],
        "radius_m": radius_m,
        "depth_m": depth_m,
        "age_factor": age_factor,
        "effective_depth_m": round(effective_depth_m, 3),
        "f_char_hz": round(f_char, 1),
        "f_soil_limit_hz": round(f_soil_limit, 1),
        "f_optimal_hz": round(f_optimal, 1),
        "delta_soil_m": round(delta_soil_at_fopt, 2),
        "delta_metal_mm": round(delta_metal_at_fopt * 1000, 1),
        "penetration_ratio": round(penetration_ratio, 2),
        "fully_penetrated": penetration_ratio >= 1.0,
        "notes": metal["notes"],
        "model_note": "Experimental skin-depth estimate; not a validated metal-detection resonance or guaranteed optimum.",
    }


# ── Comprehensive NMR/Larmor + Classical EM domain knowledge ─────────────────
DOMAIN_KNOWLEDGE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║         ΗΛΕΚΤΡΟΝΙΚΗ ΡΑΒΔΟΣΚΟΠΙΑ ΜΕ ΓΕΝΝΗΤΡΙΑ ΣΥΧΝΟΤΗΤΩΝ — ΠΛΗΡΗΣ ΓΝΩΣΗ  ║
╚══════════════════════════════════════════════════════════════════════════════╝

ΣΗΜΑΝΤΙΚΗ ΣΗΜΕΙΩΣΗ ΜΟΝΑΔΩΝ / ΒΑΘΜΟΝΟΜΗΣΗΣ (2026-10 audit):
• Οι τιμές gamma αποθηκεύονται σε Hz/T και ο κώδικας υπολογίζει fL = gamma × B σε Hz.
• Για B=0.04823 T, ο χαλκός (11.3114 MHz/T) δίνει περίπου 545 kHz, όχι 545 Hz· ο χρυσός 24K δίνει περίπου 35.6 kHz, όχι 35.6 Hz.
• Παλαιότεροι πίνακες, παραδείγματα αρμονικών και skin-depth σε αυτό το κείμενο βασίζονται σε ασύμβατες μονάδες/αριθμητικά παραδείγματα. Μην τα χρησιμοποιείς ως έγκυρες συστάσεις μέχρι να επανυπολογιστούν και να ελεγχθούν όλα.
• Ο τύπος Larmor περιγράφει πυρηνική συχνότητα· από μόνος του δεν αποδεικνύει ότι ένα κοινό θαμμένο μεταλλικό αντικείμενο παράγει ανιχνεύσιμη NMR απόκριση με γεννήτρια συχνοτήτων. Η συγκεκριμένη μέθοδος παραμένει πειραματική και απαιτεί τυφλές, επαναλήψιμες δοκιμές.

━━━ 1. ΑΡΧΗ ΛΕΙΤΟΥΡΓΙΑΣ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Η ηλεκτρονική ραβδοσκοπία βασίζεται στο φαινόμενο NMR (Nuclear Magnetic Resonance):

  fL = (γ/2π) × B₀

  fL  = συχνότητα Larmor (Hz)
  γ   = γυρομαγνητική σταθερά του υλικού (rad/s·T)
  B₀  = γεωμαγνητικό πεδίο στη θέση μέτρησης (T)

Πώς λειτουργεί η γεννήτρια:
• Η γεννήτρια παράγει EM σήμα στη συχνότητα fL (ή αρμονικής n×fL)
• Το θαμμένο αντικείμενο απορροφά και ξανα-εκπέμπει ενέργεια (resonance)
• Ο δέκτης (κεραία, πηνίο) ανιχνεύει το ξανα-εκπεμπόμενο σήμα
• Ο χειριστής ακολουθεί κατεύθυνση αυξανόμενης έντασης σήματος

━━━ 2. ΓΥΡΟΜΑΓΝΗΤΙΚΕΣ ΣΤΑΘΕΡΕΣ ΥΛΙΚΩΝ (γ/2π) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ¹⁹⁷Au (χρυσός 24K)          :  0.7379 MHz/T  → B=0.048T → fL=35.42 Hz
  Ottoman 5 Lira (91.7% Au)    :  1.6155 MHz/T  → B=0.048T → fL=77.54 Hz
  22K Κράμα Λίρας (91.67% Au) :  1.6190 MHz/T  → B=0.048T → fL=77.71 Hz
  ¹⁰⁹Ag (άργυρος)             :  1.9897 MHz/T  → B=0.048T → fL=95.50 Hz
  ⁶³Cu (χαλκός)               : 11.3114 MHz/T  → B=0.048T → fL=542.95 Hz
  ²⁷Al (αλουμίνιο)            : 11.1006 MHz/T  → B=0.048T → fL=532.83 Hz
  ⁵⁷Fe (σίδηρος, NMR σπάνιο) :  1.3818 MHz/T  → B=0.048T → fL=66.33 Hz
  ⁵⁵Mn (WWII κιβώτιο πυρ.)   : 10.5707 MHz/T  → B=0.048T → fL=507.39 Hz
  ¹³⁷Ba (χειροβομβίδες)       :  4.7635 MHz/T  → B=0.048T → fL=228.65 Hz
  ¹¹⁹Sn (κασσίτερος)         : 15.9449 MHz/T  → B=0.048T → fL=765.36 Hz
  ¹²¹Sb (αντιμόνιο)          : 10.2387 MHz/T  → B=0.048T → fL=491.46 Hz
  ¹¹B (βόριο/βόρακας)        : 13.6616 MHz/T  → B=0.048T → fL=655.76 Hz

  ΣΗΜΕΙΩΣΗ: Πολλαπλασίασε με το ακριβές B πεδίο της τοποθεσίας σου (από WMM2025).

━━━ 3. ΒΑΘΟΣ ΔΙΕΙΣΔΥΣΗΣ (SKIN DEPTH) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  δ = 1 / √(π × f × μ₀ × σ)   ≈   503 / √(f × σ)   (μέτρα)

  μ₀ = 4π×10⁻⁷ H/m (μαγνητική διαπερατότητα κενού)
  f  = συχνότητα (Hz)
  σ  = αγωγιμότητα εδάφους (S/m)

  Τύποι εδάφους και skin depth για fL χρυσού (≈35 Hz, B=0.048T):
  ┌─────────────────────┬──────────────┬───────────────────────────────────┐
  │ Τύπος εδάφους       │ σ (S/m)      │ δ @ 35Hz  │ δ @ 350Hz (n=10)    │
  ├─────────────────────┼──────────────┼───────────┼─────────────────────┤
  │ Βραχώδες/ξηρό πέτρα │ 0.00001     │ 2,684 m   │ 849 m               │
  │ Ξηρό/αμμώδες        │ 0.001       │ 84.9 m    │ 26.8 m              │
  │ Μέτριο/υγρό         │ 0.01        │ 26.8 m    │ 8.5 m               │
  │ Υγρό/αργιλώδες      │ 0.05        │ 12.0 m    │ 3.8 m               │
  │ Κορεσμένο/βαλτώδες  │ 0.10        │ 8.5 m     │ 2.7 m               │
  └─────────────────────┴──────────────┴───────────┴─────────────────────┘

  ΣΥΜΠΕΡΑΣΜΑ: Στην Μεσσηνία (μέτριο/υγρό έδαφος, σ≈0.01) η βασική fL
  δίνει δ≈26m — πολύ βαθύ. Χρησιμοποίησε υψηλότερες αρμονικές για έλεγχο
  αξιοπιστίας ή για συγκεκριμένο βάθος στόχου.

━━━ 4. ΕΠΙΛΟΓΗ ΒΕΛΤΙΣΤΗΣ ΑΡΜΟΝΙΚΗΣ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Βέλτιστη αρμονική n για βάθος στόχου d:
    δ(n×fL) ≈ ageFactor × 1.5 × d

  Η αρμονική n επιλέγεται έτσι ώστε το skin depth να είναι λίγο μεγαλύτερο
  από το βάθος ταφής (× ageFactor για χημικό halo).

  ageFactor (επέκταση χημικού halo):
  • Πρόσφατο ταφή (0-20 χρόνια)     : ×1.0  → halo ≈ 0cm
  • Αντάρτικα 1940-1950              : ×1.25 → halo ≈ 10-15cm
  • Οθωμανικό (<1900)               : ×1.6  → halo ≈ 30-50cm
  • Αρχαίο (>500 χρόνια)            : ×2.0  → halo ≈ 50-100cm

  ΠΑΡΑΔΕΙΓΜΑ: χρυσές λίρες (22K), βάθος 1.5m, αντάρτικα, μέτριο έδαφος
    Ζητάμε: δ ≈ 1.25 × 1.5 × 1.5 = 2.81m
    fL(22K) @ B=0.04823T ≈ 78.1 Hz
    Για σ=0.01: n=1 → δ≈26.8m (πολύ βαθύ), n=10 → δ≈8.5m, n=50 → δ≈3.8m
    Βέλτιστο: n≈50-70 → freq ≈ 3,900-5,500 Hz

━━━ 5. ΧΡΟΝΟΣ ΤΑΦΗΣ & ΓΕΩΧΗΜΙΚΟ HALO ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Κατά τη διάρκεια της ταφής δημιουργείται γεωχημικό halo:

  ΠΡΌΣΦΑΤΗ ΤΑΦΗ (0-20 χρόνια):
  • Ελάχιστη χημική αλλαγή
  • Το NMR σήμα εκπέμπεται σχεδόν ακριβώς από τη θέση του αντικειμένου
  • Οξείδωση μόνο στην επιφάνεια του μετάλλου

  ΑΝΤΆΡΤΙΚΑ 1940-50 (75-85 χρόνια):
  • Χαλκός/σίδηρος: οξείδωση με εξάπλωση 10-20cm
  • Χρυσός/ασήμι: σχετικά αναλλοίωτα αλλά με διαφυγόν Cu/Fe από κράμα
  • Halo Fe₂O₃ (αιματίτης) και CuCO₃ (μαλαχίτης) ανιχνεύσιμα
  • ΣΗΜΑΝΤΙΚΟ: Χρυσή λίρα 22K με Cu → το Cu οξειδώνεται, halo ≈15cm

  ΟΘΩΜΑΝΙΚΟ (<1900, 125-200+ χρόνια):
  • Ισχυρή ορυκτοποίηση γύρω από το αντικείμενο
  • Halo ορυκτών (μαλαχίτης, αζουρίτης, λιμονίτης) ≈ 30-50cm
  • Το NMR σήμα μπορεί να εκπέμπεται από το halo, όχι το κέντρο
  • Κρυσταλλωμένα άλατα Au/Ag ελάχιστα αλλά ανιχνεύσιμα

  ΑΡΧΑΪΟ (>500 χρόνια):
  • Βαριά ορυκτοποίηση, halo 50cm - 1m+
  • Πιθανή ανάμειξη με μητρικό πέτρωμα
  • Χρειάζεται υψηλότερη ευαισθησία και πολλαπλές σαρώσεις

━━━ 6. ΒΕΛΤΙΣΤΑ ΕΥΡΗ ΣΥΧΝΟΤΗΤΩΝ ΑΝΑ ΥΛΙΚΟ & ΕΔΑΦΟΣ ━━━━━━━━━━━━━━━━━━━━━

  [Μεσσηνία B ≈ 0.04823 T, τυπικό μέτριο έδαφος σ=0.01 S/m]

  ΧΡΥΣΟΣ (22K κράμα, Λίρες):
    fL ≈ 78.1 Hz
    • Βάθος 0.5m: n≈8-12  → 625-940 Hz
    • Βάθος 1.0m: n≈15-25 → 1,170-1,950 Hz
    • Βάθος 1.5m: n≈25-40 → 1,955-3,125 Hz
    • Βάθος 2.0m: n≈35-55 → 2,735-4,295 Hz
    • Βάθος 3.0m: n≈50-80 → 3,905-6,250 Hz

  ΧΑΛΚΟΣ (63Cu):
    fL ≈ 543 Hz (πολύ υψηλότερη βασική)
    • Βάθος 0.5m: n≈1-2   → 543-1,086 Hz
    • Βάθος 1.0m: n≈2-4   → 1,086-2,172 Hz
    • Βάθος 2.0m: n≈4-7   → 2,172-3,801 Hz

  WWII ΚΙΒΩΤΙΟ ΠΥΡΟΜΑΧΙΚΩΝ (55Mn):
    fL ≈ 507 Hz
    • Βάθος 0.3m: n≈1-2   → 507-1,014 Hz
    • Βάθος 1.0m: n≈2-3   → 1,014-1,521 Hz

  ΑΣΗΜΙ (109Ag):
    fL ≈ 95.5 Hz
    • Βάθος 1.0m: n≈12-20 → 1,146-1,910 Hz
    • Βάθος 2.0m: n≈25-40 → 2,388-3,820 Hz

  ΕΔΑΦΟΣ DRY/ΒΡΑΧΩΔΕΣ (σ=0.001):
    Skin depth ×√10 ≈ 3.16× μεγαλύτερο → χρειάζεσαι ×3 υψηλότερες αρμονικές
    Π.χ. χρυσός, 1.5m σε βράχο: n≈75-120 → 5,860-9,375 Hz

  ΕΔΑΦΟΣ ΥΓΡΟ/ΑΡΓΙΛΩΔΕΣ (σ=0.05):
    Skin depth ÷√5 ≈ 2.24× μικρότερο → χρειάζεσαι χαμηλότερες αρμονικές
    Π.χ. χρυσός, 1.5m σε άργιλο: n≈10-18 → 780-1,405 Hz

━━━ 7. ΘΟΡΥΒΟΙ & ΠΑΡΕΜΒΟΛΕΣ - ΑΠΟΦΥΓΗ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  SCHUMANN RESONANCES (Earth-ionosphere cavity):
    7.83 Hz, 14.3 Hz, 20.8 Hz, 27.3 Hz, 33.8 Hz, 39.0 Hz, 45.0 Hz
    → ΑΠΟΦΕΥΓΕ συχνότητες ±1 Hz από αυτές
    → Ειδικά για χρυσό (fL≈35Hz) είσαι κοντά σε 33.8/39.0 Hz → επιλέγε n×fL

  ΗΛΕΚΤΡΙΚΟ ΔΙΚΤΥΟ (Ελλάδα = 50 Hz):
    50, 100, 150, 200, 250 Hz και αρμονικές τους
    → Απομακρύνσου >500m από γραμμές ΔΕΗ για βάσιμα αποτελέσματα

  SEISMIC MICROPULSATIONS: 0.001-10 Hz → επηρεάζει χαμηλές συχνότητες
  CULTURAL NOISE: δρόμοι, μεταλλικές κατασκευές, αντλιοστάσια

  ΑΣΦΑΛΕΣ ΠΑΡΑΘΥΡΟ: 100-5,000 Hz (πάνω από seismic, κάτω από RF)
  Βέλτιστο παράθυρο για Μεσσηνία: 200-3,000 Hz

━━━ 8. ΠΡΩΤΟΚΟΛΛΟ ΕΡΕΥΝΑΣ ΠΕΔΙΟΥ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ΒΗΜΑ 1 — Μέτρηση B πεδίου:
    • Χρησιμοποίησε BGS WMM2025 με GPS συντεταγμένες + υψόμετρο
    • Ή μαγνητόμετρο για in-situ μέτρηση (ακριβέστερο αν έχεις)
    • Κράτα τιμή με ακρίβεια 4 δεκαδικών (π.χ. 0.04823 T)

  ΒΗΜΑ 2 — Υπολογισμός fL:
    fL = (γ/2π) × B  →  βάλε στη γεννήτρια την επιλεγμένη n×fL

  ΒΗΜΑ 3 — Εκτίμηση εδάφους:
    • Παρατήρηση βλάστησης, υφής, χρώματος
    • Χρησιμοποίησε live καιρό (βροχόπτωση τελευταίων ημερών)
    • Επίλεξε σ από τον πίνακα

  ΒΗΜΑ 4 — Επιλογή αρμονικής n:
    • Εκτίμηση βάθους από ιστορικά στοιχεία / χαρτογράφηση
    • Χρήση τύπου: n ≈ (ageFactor × 1.5 × d) / (503 / √(fL × σ) × √n)
    • Ή χρησιμοποίησε το Depth Optimizer της εφαρμογής

  ΒΗΜΑ 5 — Σάρωση:
    • Grid pattern: σειρές απόσταση 0.5-1m ανάλογα βάθους
    • Δύο κάθετες κατευθύνσεις (Ν-Ν, Α-Δ) για τριγωνισμό
    • Καταγραφή XY + ένταση σήματος σε κάθε σημείο

  ΒΗΜΑ 6 — Ανάλυση:
    • Συμμετρική ανωμαλία → point target
    • Επιμήκης → αγωγός, τοίχος, χαντάκι
    • Πολλαπλές ανωμαλίες σε μοτίβο → cache/αποθήκη
    • Εφέ άκρης (edge effect) → τοίχος, όριο στρώματος

  ΒΗΜΑ 7 — Cross-validation:
    • Δοκίμασε με 2-3 διαφορετικές αρμονικές
    • Αρμονικές που δίνουν ΚΟΙΝΕΣ ανωμαλίες → υψηλή αξιοπιστία
    • Αν μόνο μία αρμονική δίνει σήμα → πιθανός θόρυβος

━━━ 9. BGS WMM2025 ΓΙΑ ΜΕΣΣΗΝΙΑ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Τυπικές τιμές για Μεσσηνία (37.0-37.5°N, 21.5-22.0°E):
  • Ολική ένταση B  : 47,000-49,500 nT (0.0470-0.0495 T)
  • Κατακόρυφη (Z) : 36,000-38,000 nT
  • Οριζόντια (H)  : 28,000-29,500 nT
  • Κλίση (I)      : 52-57° (αρνητικό στο βορ. ημισφαίριο → κεφαλή προς κάτω)
  • Απόκλιση (D)   : +4.0 έως +5.5° (ανατολικά από γεωγρ. βορρά)
  • Ετήσια μεταβολή: ~0.06-0.10° ανά έτος

  Υπολογισμός fL σε διαφορετικές τοποθεσίες Μεσσηνίας:
  • Κοντά στη θάλασσα (χαμηλό υψόμετρο): B≈48,500nT → fL(22K)≈78.5Hz
  • Ορεινές περιοχές (>500m): B≈47,200nT → fL(22K)≈76.5Hz
  • Διαφορά: ~2-3% → ±1-2 αρμονικές, σημαντικό για ακριβείς μετρήσεις

━━━ 10. ΕΙΔΙΚΕΣ ΠΕΡΙΠΤΩΣΕΙΣ ΜΕΣΣΗΝΙΑΣ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ΧΡΥΣΕΣ ΛΙΡΕΣ (22K, αντάρτικα 1940-50):
  • Κράμα: 91.67% Au + 8.33% Cu → το Cu οξειδώνεται σε CuO/CuCO₃
  • Κύριο σήμα: γ(22K-alloy)=1.619 MHz/T → fL≈78.1Hz @ B=0.04823T
  • Halo χαλκού: ⁶³Cu γ/2π=11.311 MHz/T → fL≈545Hz @ ίδιο B
  • ΣΤΡΑΤΗΓΙΚΗ: Σάρωσε ΠΡΩΤΑ για halo Cu (ευκολότερο να εντοπιστεί),
    μετά επιβεβαίωσε με Au-22K freq για την ακριβή θέση

  ΟΘΩΜΑΝΙΚΑ ΝΟΜΙΣΜΑΤΑ (Ottoman 5 Lira):
  • γ=1.6155 MHz/T → fL≈77.7Hz @ B=0.04823T (σχεδόν ίδιο με 22K!)
  • Διαχωρισμός: Ottoman έχει ±0.35% διαφορά → χρειάζεσαι ακρίβεια ±0.1Hz
  • Πρακτικά αδύνατος ο διαχωρισμός με συνηθισμένη γεννήτρια

  WWII ΒΟΜΒΕΣ/ΠΥΡΟΜΑΧΙΚΑ:
  • ⁵⁵Mn κιβώτια: fL≈507Hz → σχετικά εύκολη ανίχνευση (υψηλό fL)
  • ¹³⁷Ba (Baratol): fL≈229Hz → μέτρια ανίχνευση
  • ΠΡΟΣΟΧΗ: Ενημέρωση ΕΜΑΕ πριν εκσκαφή!

━━━ 11. ΒΑΘΜΟΝΟΜΗΣΗ & ΕΛΕΓΧΟΣ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Πριν από κάθε εκστρατεία:
  1. Θάψε γνωστό αντικείμενο (π.χ. χάλκινο νόμισμα) σε γνωστό βάθος
  2. Μέτρησε B πεδίο επιτόπου
  3. Υπολόγισε fL και n×fL
  4. Επαλήθευσε ότι παίρνεις σήμα από τη γνωστή θέση
  5. Ρύθμισε ευαισθησία/gain ανάλογα

  Ενδείξεις καλής βαθμονόμησης:
  • Σήμα αιχμής (peak) ±0.5m από γνωστή θέση αντικειμένου
  • Επαναληψιμότητα >80% σε 3 διαδοχικές σαρώσεις

━━━ 12. ΚΛΑΣΙΚΟΣ ΗΜ ΣΥΝΤΟΝΙΣΜΟΣ — ΝΟΜΟΙ ΦΥΣΙΚΗΣ ━━━━━━━━━━━━━━━━━━━━━━━━━━

  ΣΗΜΑΝΤΙΚΟ: Η γεννήτρια συχνοτήτων δεν δημιουργεί πυρηνικό NMR συντονισμό.
  Λειτουργεί με ΚΛΑΣΙΚΟ ΗΛΕΚΤΡΟΜΑΓΝΗΤΙΚΟ ΣΥΝΤΟΝΙΣΜΟ (Faraday/Maxwell/Lenz).
  Αυτό ΔΕΝ μειώνει την αποτελεσματικότητα — απλώς η φυσική είναι διαφορετική.

  ΝΟΜΟΣ FARADAY (Επαγωγή):
    EMF = -N × dΦ/dt = -N × 2πf × B × A_coil × sin(2πft)
    → Η γεννήτρια δημιουργεί εναλλασσόμενο ΗΜ πεδίο στη συχνότητα f
    → Το πεδίο διεισδύει στο έδαφος (έως skin depth δ_soil)
    → Επάγει ρεύμα Foucault (eddy current) στον θαμμένο αγωγό

  ΝΟΜΟΣ LENZ (Αντίδραση στόχου):
    Το επαγόμενο ρεύμα δημιουργεί δευτερογενές ΗΜ πεδίο ΑΝΤΙΘΕΤΟ του πρωτεύοντος
    → Ο δέκτης ανιχνεύει αυτό το δευτερογενές πεδίο
    → Η θέση max δευτερογενούς σήματος = θέση αντικειμένου

  ΝΟΜΟΣ BIOT-SAVART (Εξασθένηση με βάθος):
    Μαγνητικό δίπολο: B_secondary ∝ m_induced / d³
    → Σήμα εξασθενεί ως 1/d³ με το βάθος (near field)
    → Διπλασιασμός βάθους = 8× μικρότερο σήμα

  ΑΜΠΕΡ-MAXWELL (Διάδοση στο έδαφος):
    ∇ × H = J + ∂D/∂t  →  για αγώγιμο έδαφος: skin depth δ = 503/√(f×σ)
    → Η συχνότητα καθορίζει εώς πόσο βαθιά φτάνει το ΗΜ πεδίο

  ΣΥΝΕΠΕΙΑ: Η ισχύς ανίχνευσης εξαρτάται από:
    1. Διείσδυση ΗΜ πεδίου στο έδαφος (skin depth)
    2. Αποτελεσματικότητα επαγωγής ρεύματος στο αντικείμενο
    3. Ισχύς δευτερογενούς πεδίου ← εξαρτάται από υλικό + μέγεθος + συχνότητα

━━━ 13. ΧΑΡΑΚΤΗΡΙΣΤΙΚΗ ΣΥΧΝΟΤΗΤΑ ΑΝΤΙΚΕΙΜΕΝΟΥ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ΟΡΙΣΜΟΣ: Η χαρακτηριστική συχνότητα f_char είναι η συχνότητα στην οποία
  το skin depth ΜΕΣΑ στο αντικείμενο ίσούται με την ακτίνα του.
  Στη f_char: μέγιστη εναπόθεση ενέργειας στο αντικείμενο (maximum coupling).

    f_char = 1 / (σ_μ × μ₀ × μr × a²)    [Hz]

    σ_μ = ηλεκτρική αγωγιμότητα μετάλλου (S/m)
    μ₀  = 4π×10⁻⁷ H/m (διαπερατότητα κενού)
    μr  = σχετική μαγνητική διαπερατότητα (1 για μη-μαγνητικά, ~100-200 για Fe)
    a   = ισοδύναμη ακτίνα αντικειμένου (m)

  Ηλεκτρική αγωγιμότητα μετάλλων-στόχων:
    Χρυσός (Au)         : σ = 4.52×10⁷ S/m  μr = 1
    Άργυρος (Ag)        : σ = 6.30×10⁷ S/m  μr = 1
    Χαλκός (Cu)         : σ = 5.96×10⁷ S/m  μr = 1
    Αλουμίνιο (Al)      : σ = 3.77×10⁷ S/m  μr = 1
    Σίδηρος/Χάλυβας    : σ = 7.0×10⁶ S/m   μr = 100-200 (ενισχύει coupling!)
    Μπρούντζος (αρχαίος): σ = 1.5×10⁷ S/m  μr = 1
    Λίρα 22K (κράμα)   : σ = 2.2×10⁷ S/m  μr = 1

  ΠΙΝΑΚΑΣ f_char ανά μέγεθος αντικειμένου (παραδείγματα, μέτριο έδαφος):
  ┌─────────────────────────┬────────────┬────────────┬────────────┬────────────┐
  │ Αντικείμενο             │ a (cm)     │ f_char(Au) │ f_char(Cu) │ f_char(Fe) │
  ├─────────────────────────┼────────────┼────────────┼────────────┼────────────┤
  │ Χρυσή λίρα (νόμισμα)   │ 1.1 cm     │  144 Hz    │  108 Hz    │  16 Hz     │
  │ Χούφτα νομισμάτων       │ 3.0 cm     │   19 Hz    │   14 Hz    │   2 Hz     │
  │ Κιβωτάκι λιρών          │ 8.0 cm     │  2.8 Hz    │  2.1 Hz    │  0.3 Hz    │
  │ Χάλκινο αγγείο          │ 10.0 cm    │  1.8 Hz    │  1.3 Hz    │  0.2 Hz    │
  │ WWII ammo κιβώτιο (Fe) │ 20.0 cm    │  0.4 Hz    │  0.3 Hz    │  0.04 Hz   │
  └─────────────────────────┴────────────┴────────────┴────────────┴────────────┘

  ΚΡΙΣΙΜΗ ΠΑΡΑΤΗΡΗΣΗ:
  • Για μεμονωμένο νόμισμα (a≈1cm): f_char ≈ 100-150 Hz → ΑΡΚΕΤΑ κοντά στις
    fL-αρμονικές χρυσού (78Hz × n). Αυτός είναι ο λόγος που η μέθοδος λειτουργεί!
  • Για ομάδα νομισμάτων/κιβώτιο (a≈5-8cm): f_char << fL → χρειάζεσαι ΧΑΜΗΛΟΤΕΡΕΣ
    συχνότητες από τις fL-αρμονικές για μέγιστη απόκριση
  • Για χαλύβδινα αντικείμενα (μr=100): f_char μειώνεται ×100 → πολύ χαμηλό

━━━ 14. ΒΕΛΤΙΣΤΗ ΣΥΧΝΟΤΗΤΑ — ΔΙΠΛΗ ΠΡΟΣΕΓΓΙΣΗ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Δύο κριτήρια συνδυάζονται για τη βέλτιστη συχνότητα ανίχνευσης:

  ΚΡΙΤΗΡΙΟ Α — Διείσδυση εδάφους (Skin depth):
    f_soil_limit = (503 / (1.5×d×ageFactor))² / σ_soil
    → Εξασφαλίζει ότι το ΗΜ πεδίο φτάνει στο βάθος του στόχου

  ΚΡΙΤΗΡΙΟ Β — Απόκριση στόχου (Characteristic frequency):
    f_char = 1/(σ_μ × μ₀ × μr × a²)
    → Εξασφαλίζει μέγιστη επαγωγή ρεύματος στο αντικείμενο

  ΒΕΛΤΙΣΤΗ ΤΙΜΗ (γεωμετρικός μέσος):
    f_optimal = √(f_soil_limit × f_char)

  ΠΑΡΑΔΕΙΓΜΑΤΑ (Μεσσηνία B=0.04823T, μέτριο έδαφος σ=0.01):
  ┌─────────────────┬──────┬────────┬───────┬────────────┬────────────┬──────────────┐
  │ Στόχος          │ a(cm)│ d(m)   │ age   │ f_char(Hz) │ f_soil(Hz) │ f_optimal(Hz)│
  ├─────────────────┼──────┼────────┼───────┼────────────┼────────────┼──────────────┤
  │ Χρ. λίρα 22K    │ 1.1  │ 1.5    │ αντ.  │   120 Hz   │  9,070 Hz  │  1,040 Hz    │
  │ Χούφτα λίρες   │ 3.0  │ 1.5    │ αντ.  │    16 Hz   │  9,070 Hz  │    380 Hz    │
  │ Κιβώτιο λιρών  │ 8.0  │ 1.5    │ αντ.  │   2.2 Hz   │  9,070 Hz  │    141 Hz    │
  │ Χρ. λίρα 22K    │ 1.1  │ 2.0    │ αντ.  │   120 Hz   │  5,100 Hz  │    780 Hz    │
  │ Κιβ. λιρών     │ 8.0  │ 2.0    │ οθωμ. │   2.2 Hz   │  1,990 Hz  │     66 Hz    │
  │ WWII ammo (Fe) │ 20   │ 0.5    │ αντ.  │   0.04Hz   │ 81,630 Hz  │     57 Hz    │
  └─────────────────┴──────┴────────┴───────┴────────────┴────────────┴──────────────┘

  ΣΥΓΚΡΙΣΗ ΜΕ LARMOR n×fL:
  • Μεμονωμένη λίρα 1.5m: f_opt_ΗΜ≈1,040Hz  →  fL(22K)×n=78.1×13≈1,015Hz ✓ ΤΑΥΤΙΖΕΤΑΙ!
  • Χούφτα λιρών 1.5m:    f_opt_ΗΜ≈380Hz    →  fL(22K)×n=78.1×5=390Hz  ✓ ΤΑΥΤΙΖΕΤΑΙ!
  • Κιβώτιο λιρών 1.5m:   f_opt_ΗΜ≈141Hz    →  fL(22K)×n=78.1×2=156Hz  ≈ ΚΟΝΤΑ
  Αυτό ΕΞΗΓΕΙ γιατί οι fL-αρμονικές λειτουργούν εμπειρικά!

━━━ 15. ΣΤΡΑΤΗΓΙΚΗ ΑΝΙΧΝΕΥΣΗΣ ΜΕ ΚΛΑΣΙΚΟ ΗΜ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ΒΗΜΑ 1 — Εκτίμηση μεγέθους στόχου:
    Από ιστορικά στοιχεία: μεμονωμένα νομίσματα? χούφτα? κιβώτιο?
    Εκτίμηση ισοδύναμης ακτίνας a (cm)

  ΒΗΜΑ 2 — Υπολογισμός f_char για κάθε σενάριο μεγέθους:
    f_char = 1/(σ_μ × 4π×10⁻⁷ × a²)
    Παράδειγμα Au, a=3cm: f_char = 1/(4.52e7 × 1.257e-6 × 0.0009) = 19.6 Hz

  ΒΗΜΑ 3 — Υπολογισμός f_soil_limit:
    f_soil = (503 / (1.5 × d × age))² / σ_soil

  ΒΗΜΑ 4 — Υπολογισμός f_optimal = √(f_char × f_soil)

  ΒΗΜΑ 5 — Σάρωση με 3 συχνότητες:
    α) f_optimal (κλασικό ΗΜ μέγιστο)
    β) Πλησιέστερη fL-αρμονική n×fL (NMR/Larmor προσέγγιση)
    γ) ×2 f_optimal (για μικρότερο μέγεθος σεναρίου)
    Κοινή ανωμαλία και στις 3 = μέγιστη αξιοπιστία

  ΒΗΜΑ 6 — Ερμηνεία σήματος:
    • Ισχυρό σήμα σε f_optimal & αδύναμο σε fL-αρμονική:
      → Πιθανώς μεγαλύτερο αντικείμενο ή άλλο υλικό
    • Ισχυρό σήμα μόνο σε fL-αρμονική:
      → Πιθανώς μικρό αντικείμενο (νόμισμα) ή ομαδικά νομίσματα
    • Σήμα και στις δύο:
      → Υψηλή αξιοπιστία, σωστή εκτίμηση μεγέθους

━━━ 16. ΣΙΔΗΡΟΜΑΓΝΗΤΙΚΑ ΑΝΤΙΚΕΙΜΕΝΑ — ΕΙΔΙΚΗ ΠΕΡΙΠΤΩΣΗ ━━━━━━━━━━━━━━━━━━━

  Σίδηρος/Χάλυβας (μr=100-200) έχει ΠΟΛΥ ΧΑΜΗΛΟΤΕΡΗ f_char λόγω υψηλού μr:
    WWII κράνος Fe (a=10cm): f_char = 1/(7e6 × 1.257e-6 × 100 × 0.01) = 1.1 Hz

  Αλλά: ο σίδηρος ΕΝΙΣΧΥΕΙ το πρωτεύον ΗΜ πεδίο × μr!
  → Το δευτερογενές σήμα είναι ισχυρότερο αλλά σε πολύ χαμηλές συχνότητες

  ΠΡΑΚΤΙΚΟ: Για WWII σιδερένια αντικείμενα:
    • Χρησιμοποίησε πολύ χαμηλές συχνότητες: 1-50 Hz (Schumann-free windows!)
    • Ή: χρησιμοποίησε DC/quasi-DC παλμό (time-domain EM)
    • Ασφαλές παράθυρο: 10-48 Hz (Schumann ≈7.83, 14.3 — αποφύγε ±2Hz)
    • Για κιβώτιο πυρομαχικών Mn (⁵⁵Mn): χρήσε fL=507Hz για αρχική σάρωση
      και f_char_Fe για επαλήθευση κελύφους

  ΦΕΡΙΤΕΣ & ΟΞΕΙΔΙΑ (γεωχημικό halo):
    Μαγνητίτης (Fe₃O₄) στο halo: σ≈1×10⁴ S/m, μr≈1000-10000
    → f_char_halo << 1 Hz → Ανιχνεύεται με πολύ χαμηλές συχνότητες
    → Αλλά το halo είναι ΜΕΓΑΛΥΤΕΡΟ από το αντικείμενο → εντοπίζεται πιο εύκολα

━━━ 17. ΣΥΝΟΨΗ ΟΛΗΣ ΤΗΣ ΜΕΘΟΔΟΛΟΓΙΑΣ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ΠΗΓΗ ΣΗΜΑΤΟΣ     : Κλασικός ΗΜ Συντονισμός (Eddy Currents — Faraday/Lenz)
  ΝΟΜΟΙ ΦΥΣΙΚΗΣ   : Faraday, Lenz, Biot-Savart, Ampere-Maxwell
  ΚΥΡΙΑ ΕΞΑΡΤΗΣΗ  : Αγωγιμότητα μετάλλου + μέγεθος + βάθος + τύπος εδάφους
  ΔΕΝ ΕΙΝΑΙ NMR    : Δεν απαιτεί RF παλμούς, echo sequences, ή κβαντομηχανική
  ΣΧΕΣΗ ΜΕ LARMOR : Οι fL-αρμονικές τυχαία συμπίπτουν με f_optimal για νομίσματα

  ΤΕΛΙΚΗ ΣΤΡΑΤΗΓΙΚΗ (Dual-Frequency Approach):
    1. Υπολόγισε f_char (μέγεθος στόχου) ΚΑΙ fL-αρμονική (Larmor)
    2. Σάρωσε και με τις δύο
    3. Κοινή ανωμαλία = στόχος επαληθευμένος
    4. Χρήσιμη ακόμα και αν γνωρίζεις ΜΟΝΟ ένα από τα δύο
"""


def calculate_larmor(material_key: str, b_field_T: float) -> dict:
    """Calculate fL = (γ/2π) × B and return harmonics + analysis.

    ``b_field_T`` must be a finite, positive magnetic flux density in tesla.
    """
    mat = MATERIALS.get(material_key)
    if not mat:
        return {"error": f"Unknown material: {material_key}"}

    if isinstance(b_field_T, bool):
        return {"error": "b_field_T must be a finite positive number in tesla"}
    try:
        b_field_T = float(b_field_T)
    except (TypeError, ValueError, OverflowError):
        return {"error": "b_field_T must be a finite positive number in tesla"}
    if not math.isfinite(b_field_T) or b_field_T <= 0:
        return {"error": "b_field_T must be a finite positive number in tesla"}

    gamma = mat["gamma"]
    f_hz = gamma * b_field_T
    f_khz = f_hz / 1e3
    f_mhz = f_hz / 1e6
    harmonics = [{"n": n, "hz": f_hz * n, "khz": f_khz * n, "mhz": f_mhz * n}
                 for n in range(1, 51)]

    # Compute recommended harmonics per soil type for quick display
    soil_recs = {}
    for soil_key, soil in SOIL_TYPES.items():
        sigma = soil["sigma"]
        recs = []
        for depth in [0.5, 1.0, 1.5, 2.0, 3.0]:
            for age_key, age in AGE_FACTORS.items():
                target_delta = age["factor"] * 1.5 * depth
                # δ(n×fL) = 503/√(n×fL × σ) ≈ target_delta
                # → n ≈ (503 / (target_delta × √σ))² / fL
                if sigma > 0 and f_hz > 0:
                    n_ideal = (503.0 / (target_delta * math.sqrt(sigma))) ** 2 / f_hz
                    n_int = max(1, round(n_ideal))
                    recs.append({
                        "depth_m": depth,
                        "age": age_key,
                        "n_optimal": n_int,
                        "freq_hz": f_hz * n_int,
                        "skin_depth_m": round(503.0 / math.sqrt(f_hz * n_int * sigma), 2),
                    })
        soil_recs[soil_key] = recs

    return {
        "material": mat["name"],
        "material_key": material_key,
        "notes": mat["notes"],
        "gamma_hz_per_T": gamma,
        "b_field_T": b_field_T,
        "f_larmor_hz": f_hz,
        "f_larmor_khz": f_khz,
        "f_larmor_mhz": f_mhz,
        "harmonics": harmonics,
        "soil_recommendations": soil_recs,
    }


def skin_depth_m(sigma_S_per_m: float, freq_hz: float) -> float:
    import math
    if sigma_S_per_m <= 0 or freq_hz <= 0:
        return 9999.0
    return 503.0 / math.sqrt(freq_hz * sigma_S_per_m)


def ping_larmor_app() -> dict:
    try:
        r = requests.get(LARMOR_APP_URL, timeout=8)
        online = r.status_code == 200 and "Larmor" in r.text
        return {"online": online, "status_code": r.status_code, "url": LARMOR_APP_URL}
    except Exception as e:
        return {"online": False, "error": str(e), "url": LARMOR_APP_URL}


def _build_system_prompt() -> str:
    return f"""Είσαι ο ΝΟΥΣ, εξειδικευμένος αναλυτής NMR γεωφυσικής και ηλεκτρονικής ραβδοσκοπίας.

{DOMAIN_KNOWLEDGE}

ΟΔΗΓΙΕΣ ΑΠΟΚΡΙΣΗΣ:
• Απαντάς ΠΑΝΤΑ στα Ελληνικά
• Χρησιμοποιείς συγκεκριμένους αριθμούς και τύπους
• Προτείνεις πάντα πρακτικά βήματα
• Αναφέρεις πάντα τη σχετική αρμονική n και τη συχνότητα σε Hz
• Επισημαίνεις πιθανές πηγές θορύβου/παρεμβολής
• Αν δοθούν δεδομένα υπολογισμού, τα αναλύεις βήμα-βήμα
"""


def analyze_session(session_data, question: str = "") -> str:
    system = _build_system_prompt()
    data_str = session_data if isinstance(session_data, str) else str(session_data)
    user_content = f"Δεδομένα από τον Υπολογιστή Larmor:\n\n{data_str}\n"
    if question:
        user_content += f"\nΕρώτηση: {question}"
    else:
        user_content += (
            "\nΑνάλυσε τα δεδομένα και δώσε:\n"
            "1. Σύνοψη υπολογισμού\n"
            "2. Αξιολόγηση επιλογής αρμονικής\n"
            "3. Βέλτιστη στρατηγική για το συγκεκριμένο βάθος/έδαφος\n"
            "4. Πρακτικές προτάσεις για την έρευνα πεδίου\n"
            "5. Πιθανές πηγές θορύβου να αποφύγεις"
        )
    turns = [{"role": "user", "content": user_content}]
    try:
        result = ask_with_turns(turns, system=system)
        if isinstance(result, dict):
            return result.get("response") or result.get("error") or str(result)
        return str(result)
    except Exception as e:
        return f"Σφάλμα ανάλυσης: {e}"


def larmor_chat(conversation: list) -> str:
    system = _build_system_prompt()
    try:
        result = ask_with_turns(conversation, system=system)
        if isinstance(result, dict):
            return result.get("response") or result.get("error") or str(result)
        return str(result)
    except Exception as e:
        return f"Σφάλμα: {e}"


def get_knowledge_chunks() -> list[dict]:
    """Return cautious, unit-consistent reference notes for NOUS memory."""
    return [
        {
            "question": "Πώς υπολογίζεται η συχνότητα Larmor και ποιες είναι οι μονάδες;",
            "answer": (
                "Ο υπολογισμός είναι fL = (γ/2π) × B, με τη σταθερά gamma σε Hz/T και το B σε tesla, "
                "άρα το αποτέλεσμα είναι σε Hz. Για B=0.04823 T, οι τιμές του κώδικα δίνουν περίπου "
                "35.6 kHz για Au-197, 78.1 kHz για κράμα 22K και 545.5 kHz για Cu-63. "
                "Αυτές είναι πυρηνικές συχνότητες αναφοράς· δεν αποδεικνύουν ότι ένα θαμμένο μεταλλικό "
                "αντικείμενο παράγει ανιχνεύσιμη απόκριση με γεννήτρια. Η μέθοδος εντοπισμού παραμένει πειραματική."
            ),
            "tags": ["larmor", "units", "experimental-limit", "NMR"],
        },
        {
            "question": "Πώς υπολογίζεται το skin depth στο έδαφος;",
            "answer": (
                "Το απλοποιημένο μοντέλο αγώγιμου μέσου χρησιμοποιεί δ ≈ 503 / sqrt(f × sigma) μέτρα, "
                "όπου f είναι σε Hz και sigma σε S/m. Για παράδειγμα, σε f=35.59 kHz και sigma=0.01 S/m "
                "προκύπτει δ≈26.7 m. Η τιμή αυτή είναι κλίμακα εξασθένησης του μοντέλου, όχι εγγυημένο "
                "βάθος ανίχνευσης. Χρησιμοποίησε τις πραγματικές μονάδες και την αγωγιμότητα κάθε φορά."
            ),
            "tags": ["skin_depth", "soil", "units", "model-limit"],
        },
        {
            "question": "Πώς εκτιμάται μια αρμονική για δεδομένο βάθος;",
            "answer": (
                "Ως πειραματική εκτίμηση, αν ο στόχος skin depth είναι delta_target = age_factor × 1.5 × depth_m, "
                "τότε n_ideal = (503 / (delta_target × sqrt(sigma)))² / fL_hz. Το fL πρέπει να είναι σε Hz. "
                "Για πρακτική χρήση απαιτείται θετικός ακέραιος n· αν το n_ideal είναι κάτω από 1, η βασική "
                "συχνότητα είναι ήδη πάνω από την εκτίμηση-στόχο και δεν υπάρχει μικρότερη θετική αρμονική. "
                "Ο τύπος δεν έχει επικυρωθεί ως μέθοδος εντοπισμού μετάλλων."
            ),
            "tags": ["harmonics", "depth", "equation", "experimental-limit"],
        },
        {
            "question": "Τι σημαίνει η χαρακτηριστική συχνότητα στο μοντέλο κλασικού ΗΜ;",
            "answer": (
                "Ο κώδικας χρησιμοποιεί f_char = 1 / (pi × sigma_metal × mu0 × mu_r × radius_m²), "
                "ώστε το skin depth στο απλοποιημένο μοντέλο να είναι περίπου ίσο με την ακτίνα. "
                "Είναι κλίμακα μετάβασης skin depth, όχι απόδειξη συντονισμού ούτε εγγυημένη βέλτιστη συχνότητα. "
                "Το f_optimal_hz είναι προς το παρόν ευρετική τιμή ίση με f_char_hz και δεν πρέπει να παρουσιάζεται "
                "ως επαληθευμένη συχνότητα ανίχνευσης."
            ),
            "tags": ["classical-em", "skin-depth", "characteristic-frequency", "model-limit"],
        },
        {
            "question": "Τι σημαίνει ο παράγοντας ηλικίας στον υπολογισμό;",
            "answer": (
                "Ο age_factor είναι εμπειρικός παράγοντας που χρησιμοποιείται μόνο για να κλιμακώσει το "
                "effective_depth_m = 1.5 × age_factor × depth_m στην εκτίμηση του ορίου skin depth του εδάφους. "
                "Δεν αποτελεί μετρημένη σταθερά γεохημικού halo και δεν αλλάζει τις ιδιότητες του μετάλλου. "
                "Χρειάζεται ανεξάρτητη πειραματική επικύρωση πριν χρησιμοποιηθεί ως φυσικό συμπέρασμα."
            ),
            "tags": ["age_factor", "uncertainty", "soil-model"],
        },
        {
            "question": "Πώς πρέπει να ελέγχεται πειραματικά η μέθοδος εντοπισμού;",
            "answer": (
                "Κατέγραψε εκ των προτέρων στόχο, θέση γεννήτριας, συχνότητα, προσανατολισμό, απόσταση και αποτέλεσμα. "
                "Χρησιμοποίησε τυφλές δοκιμές με τυχαία θέση στόχου, άδειο control, ψευδή στόχο και επαναλήψεις. "
                "Σύγκρινε επιτυχίες με αποτυχίες και τυχαία πιθανότητα, χωρίς να αλλάζεις κανόνες μετά από κάθε δοκιμή. "
                "Μια σύμπτωση κατεύθυνσης ή μια μεμονωμένη επιτυχία δεν αποδεικνύει φυσικό μηχανισμό."
            ),
            "tags": ["field-tests", "blind-test", "controls", "reproducibility"],
        },
    ]

# KiranaVaani Data Directory

This directory contains the grocery catalogue and evaluation datasets for the KiranaVaani voice assistant.

---

## 1. Files in this Directory

| File | Purpose | Description |
| :--- | :--- | :--- |
| `catalogue.json` | Master Store Catalogue | 35 multi-category grocery SKUs with bilingual names, standard units, INR pricing, and colloquial phonetic aliases. |
| `sample_orders.json` | 80 Synthetic Orders | Evaluation dataset with realistic Hinglish phone orders, colloquial fractional quantities, and ground truth item/quantity annotations. |

---

## 2. Catalogue Design (`catalogue.json`)

The catalogue represents a standard neighbourhood Indian Kirana store (*Gupta Kirana & General Store*). It covers 7 core grocery categories:

1. **Flour & Grains**: Aashirvaad Chakki Atta, India Gate Basmati Chawal, Sona Masoori Regular Chawal, Rajdhani Maida, Sooji.
2. **Pulses & Dal**: Tata Sampann Toor Dal, Moong Dal Dhuli, Chana Dal, Kabuli Chana, Rajma.
3. **Dairy & Fresh**: Amul Taaza Toned Milk, Amul Masti Dahi, Amul Butter, Nandini GoodLife Milk, Paneer.
4. **Cooking Oils & Ghee**: Fortune Sunlite Refined Oil, Arogyam Kacchi Ghani Mustard Oil, Amul Cow Ghee.
5. **Spices, Salt & Sugar**: Tata Salt, Madhur Sulphurless Sugar, Catch Haldi, Mirch Powder, Everest Garam Masala.
6. **Snacks, Biscuits & Beverages**: Maggi 2-Minute Masala Noodles, Maggi Veg Atta Noodles, Parle-G, Britannia Good Day, Red Label Tea, Nescafe Classic Coffee.
7. **Personal & Home Care**: Dettol Bathing Soap, Surf Excel Easy Wash Detergent, Colgate Strong Teeth, Vim Dishwash Bar, Bajaj Almond Drops.

### Multilingual Aliases
Every SKU includes phonetic aliases in:
- Hinglish (e.g. `"basmati chawal"`, `"aata"`, `"sarson tel"`, `"doodh"`)
- Devanagari Hindi (e.g. `"आशीर्वाद आटा"`, `"बासमती चावल"`, `"चीनी"`)
- Regional transliterations (Kannada, Tamil)

---

## 3. Synthetic Test Set (`sample_orders.json`)

The 80 test orders were synthetically generated to model realistic telephony orders. They test:
- Single-item orders vs multi-item rapid lists (2 to 5 items per utterance)
- Colloquial fractional numerals (*"सवा दो"*, *"ढाई"*, *"डेढ़"*, *"आधा"*, *"पाव"*)
- Order completion signals (*"हो गया"*, *"बस इतना ही"*, *"बिल बना दो"*)
- Natural code-switching (*"Bhaiya do packet Maggi, ek kilo sugar aur aadha litre milk bhej dena"*)

### Zero-PII Compliance Declaration
- All transcripts, names, quantities, and scenarios are **100% synthetically generated**.
- Zero customer phone numbers, personal Aadhaar details, or private phone call audio recordings are contained in this dataset.

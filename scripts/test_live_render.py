import urllib.request
import json
import base64
import sys
import re

if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
    print("Usage: python scripts/test_live_render.py [BASE_URL]")
    print("Default BASE_URL: https://kiranavaani.onrender.com")
    print("Example: python scripts/test_live_render.py http://127.0.0.1:8000")
    sys.exit(0)

BASE = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'https://kiranavaani.onrender.com'

def test_endpoint(name, path, method='GET', data=None):
    url = f'{BASE}{path}'
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
        body = json.dumps(data).encode('utf-8')
    else:
        body = None
    try:
        with urllib.request.urlopen(req, data=body, timeout=30) as resp:
            status = resp.status
            content = resp.read()
            parsed = None
            try:
                parsed = json.loads(content.decode('utf-8'))
            except Exception:
                parsed = f'{len(content)} bytes ({resp.headers.get("content-type", "")})'
            print(f'[PASS] {name} ({method} {path}) -> HTTP {status}')
            return True, parsed
    except Exception as e:
        print(f'[FAIL] {name} ({method} {path}) -> Error: {e}')
        return False, str(e)

def main():
    print('=======================================================')
    print(f' TESTING LIVE KIRANAVAANI HOST ({BASE})')
    print('=======================================================')

    results = []

    # 1. Health
    ok, res = test_endpoint('Health Check', '/health')
    results.append(('Health Check (/health)', ok))
    if ok and isinstance(res, dict):
        print(f"       Service: {res.get('service')}, Version: {res.get('version')}")
        print(f"       Live Gnani Configured: {res.get('live_api_configured')}")
        print(f"       Catalog SKU count: {res.get('catalogue_sku_count')}")

    # 2. API Health
    ok, _ = test_endpoint('API Health', '/api/health')
    results.append(('API Health (/api/health)', ok))

    # 3. Web UI Root
    ok, res = test_endpoint('Web UI Root HTML', '/')
    results.append(('Web UI Root (/)', ok))

    # 4. Frontend Assets (JS & CSS detected dynamically from HTML)
    js_match = re.search(r'src="(/assets/index-[^"]+\.js)"', str(res) if ok else '')
    css_match = re.search(r'href="(/assets/index-[^"]+\.css)"', str(res) if ok else '')
    js_path = js_match.group(1) if js_match else '/assets/index-DmYl8wSj.js'
    css_path = css_match.group(1) if css_match else '/assets/index-C6prTL3Q.css'

    ok, res = test_endpoint('Frontend JS Bundle', js_path)
    results.append(('Frontend JS Bundle', ok))

    ok, res = test_endpoint('Frontend CSS Bundle', css_path)
    results.append(('Frontend CSS Bundle', ok))

    # 5. Catalogue
    ok, res = test_endpoint('Catalogue', '/catalogue')
    results.append(('Catalogue (/catalogue)', ok))
    if ok and isinstance(res, dict):
        print(f"       Store: {res.get('store_name')}, Total SKUs: {res.get('total_skus')}")
        if res.get('skus'):
            sample = res['skus'][0]
            print(f"       Sample SKU: {sample.get('sku_id')} - {sample.get('name_en')} ({sample.get('name_hi')}) - Rs {sample.get('price_inr')}")

    # 6. Swagger Docs
    ok, _ = test_endpoint('Swagger Docs', '/docs')
    results.append(('Swagger Docs (/docs)', ok))

    # 7. OpenAPI JSON
    ok, res = test_endpoint('OpenAPI Specification', '/openapi.json')
    results.append(('OpenAPI Spec (/openapi.json)', ok))
    if ok and isinstance(res, dict):
        paths = list(res.get('paths', {}).keys())
        print(f"       Total paths registered in OpenAPI: {len(paths)}")

    # 8. Parse Order
    ok, res = test_endpoint('Parse Order', '/parse-order', method='POST', data={
        'transcript': 'Bhaiya 2 kilo basmati chawal, aadha litre doodh aur 1 packet Maggi likh lo',
        'keyterms_enabled': True
    })
    results.append(('Parse Order (/parse-order)', ok))
    if ok and isinstance(res, dict):
        print(f"       Items parsed: {len(res.get('items', []))}")
        for item in res.get('items', []):
            print(f"         - Product: '{item.get('product')}', qty: {item.get('quantity')} {item.get('unit')}")

    # 9. Match Products
    ok, res = test_endpoint('Match Products', '/match-products', method='POST', data={
        'items': [
            {'product': 'basmati rice', 'quantity': 2.0, 'unit': 'kg'},
            {'product': 'Maggi Masala', 'quantity': 1.0, 'unit': 'packet'}
        ],
        'keyterms_enabled': True
    })
    results.append(('Match Products (/match-products)', ok))
    if ok and isinstance(res, dict):
        matched = res.get('matched_items', [])
        print(f"       Matched items: {len(matched)}")
        for m in matched:
            sku = m.get('matched_sku') or {}
            print(f"         - {m.get('status')}: {sku.get('name_en')} (Confidence: {m.get('confidence')})")

    # 10. Ambiguity Clarification Gate
    ok, res = test_endpoint('Ambiguity Clarification Gate', '/match-products', method='POST', data={
        'items': [
            {'product': 'chawal', 'quantity': 2.0, 'unit': 'kg'}
        ],
        'keyterms_enabled': True
    })
    results.append(('Clarification Gate Trigger', ok))
    if ok and isinstance(res, dict):
        clarifications = res.get('clarifications_needed', [])
        print(f"       Clarifications needed: {len(clarifications)}")
        for c in clarifications:
            print(f"         - Hindi: {c.get('question_hi')}")
            print(f"         - English: {c.get('question_en')}")

    # 11. Cart Builder
    ok, res = test_endpoint('Cart Builder', '/cart', method='POST', data={
        'items': [
            {'sku_id': 'SKU-001', 'quantity': 2.0, 'unit': 'kg'},
            {'sku_id': 'SKU-002', 'quantity': 1.0, 'unit': 'kg'}
        ]
    })
    results.append(('Cart Builder (/cart)', ok))
    if ok and isinstance(res, dict):
        print(f"       Items count: {res.get('item_count')}")
        print(f"       Subtotal: Rs {res.get('subtotal_inr')}")
        print(f"       Total: Rs {res.get('total_inr')}")
        print(f"       Summary (Hi): {res.get('spoken_summary_hi')}")

    # 12. Timbre TTS Voice Synthesis
    ok, res = test_endpoint('Speech Synthesis (Timbre TTS)', '/synthesize', method='POST', data={
        'text': 'Aapka order note kar liya gaya hai',
        'voice': 'Nalini',
        'language': 'hi-IN'
    })
    results.append(('TTS Synthesis (/synthesize)', ok))
    if ok and isinstance(res, dict):
        b64 = res.get('audio_base64', '')
        print(f"       TTS Status: Audio payload = {len(b64)} chars, Format: {res.get('audio_format')}, is_mock={res.get('is_mock')}")

    # 13. End-to-end Process Order
    ok, res = test_endpoint('End-to-End Process Order', '/process-order', method='POST', data={
        'transcript': 'bhaiya do packet maggi aur ek kilo cheeni bhej dena',
        'keyterms_enabled': True,
        'synthesize_voice': True
    })
    results.append(('E2E Process Order (/process-order)', ok))
    if ok and isinstance(res, dict):
        print(f"       E2E Transcript: '{res.get('transcript')}'")
        print(f"       E2E Voice Audio Generated: {'Yes (' + str(len(res.get('voice_audio_base64', ''))) + ' bytes)' if res.get('voice_audio_base64') else 'No'}")
        print(f"       E2E Spoken Reply: {res.get('spoken_reply_hi')}")

    # 14. Audio Transcription with real base64 WAV audio file
    audio_path = 'audio_samples/clip_1_brand_keyterms_clean_16khz.wav'
    try:
        with open(audio_path, 'rb') as f:
            audio_b64 = base64.b64encode(f.read()).decode('utf-8')
        ok, res = test_endpoint('STT Audio Transcribe (/transcribe)', '/transcribe', method='POST', data={
            'audio_base64': audio_b64,
            'keyterms_enabled': True
        })
        results.append(('STT Audio Transcribe (/transcribe)', ok))
        if ok and isinstance(res, dict):
            print(f"       Transcript: '{res.get('transcript')}'")
            print(f"       Confidence: {res.get('confidence')}, Model: {res.get('model')}, is_mock={res.get('is_mock')}")
    except Exception as e:
        print(f"       Skipping audio upload test: {e}")

    print('=======================================================')
    print(' FINAL SUMMARY OF ALL LIVE HEALTH & INTEGRATION CHECKS')
    print('=======================================================')
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        status_sym = 'PASS' if ok else 'FAIL'
        print(f'[{status_sym}] {name}')
    print(f'\nTotal: {passed}/{total} checks passed ({int(passed/total*100)}% operational)')

if __name__ == '__main__':
    main()

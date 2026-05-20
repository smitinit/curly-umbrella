import io
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from supabase import create_client, Client

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import build_resume_pdf, load_resume_data

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
BUCKET_NAME  = os.environ.get("BUCKET_NAME", "test")

_supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in stem).strip("_")
    return cleaned or "resume"


def upload_bytes_to_supabase(data: bytes, folder: str, filename: str) -> str:
    """Upload raw bytes to Supabase Storage and return the public URL."""
    storage_path = f"{folder}/{filename}"
    _supabase.storage.from_(BUCKET_NAME).upload(
        path=storage_path,
        file=data,
        file_options={"content-type": "application/pdf", "upsert": "true"},
    )
    return _supabase.storage.from_(BUCKET_NAME).get_public_url(storage_path)


PAGE_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ATS Resume Builder</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    html, body {
      width: 100%; height: 100%;
      font-family: Inter, "Segoe UI", system-ui, sans-serif;
      background: #111;
      color: #eee;
      overflow: hidden;
    }

    #bar {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 16px;
      background: #1a1a1a;
      border-bottom: 1px solid #2a2a2a;
      height: 52px;
    }

    #file-input { display: none; }

    #pick-btn {
      padding: 6px 14px;
      border: 1px solid #444;
      border-radius: 6px;
      background: #222;
      color: #ddd;
      font-size: 13px;
      cursor: pointer;
      white-space: nowrap;
    }
    #pick-btn:hover { background: #2a2a2a; border-color: #666; }

    #file-label {
      font-size: 13px;
      color: #777;
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    #status {
      font-size: 12px;
      color: #666;
      white-space: nowrap;
    }

    #main {
      display: flex;
      width: 100vw;
      height: calc(100vh - 52px);
    }

    .pane {
      flex: 1;
      display: flex;
      flex-direction: column;
      border-right: 1px solid #2a2a2a;
      min-width: 0;
    }
    .pane:last-child { border-right: none; }

    .pane iframe {
      flex: 1;
      width: 100%;
      border: none;
      display: block;
      background: #fff;
    }

    .pane-url {
      padding: 6px 10px;
      font-size: 11px;
      font-family: "SF Mono", "Fira Code", monospace;
      background: #141414;
      border-top: 1px solid #222;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      height: 28px;
    }
    .pane-url a {
      color: #555;
      text-decoration: none;
    }
    .pane-url a:hover {
      color: #999;
      text-decoration: underline;
    }

    .placeholder {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      color: #444;
    }
  </style>
</head>
<body>

<div id="bar">
  <input type="file" id="file-input" accept="application/pdf">
  <button id="pick-btn" onclick="document.getElementById('file-input').click()">Choose PDF</button>
  <span id="file-label">No file chosen</span>
  <span id="status"></span>
</div>

<div id="main">
  <div class="pane" id="pane-original">
    <div class="placeholder" id="placeholder-original">Upload a PDF</div>
    <div class="pane-url" id="url-original"></div>
  </div>
  <div class="pane" id="pane-generated">
    <div class="placeholder" id="placeholder-generated">ATS version will appear here</div>
    <div class="pane-url" id="url-generated"></div>
  </div>
</div>

<script>
  const fileInput = document.getElementById('file-input');
  const fileLabel = document.getElementById('file-label');
  const statusEl  = document.getElementById('status');

  const paneOrig  = document.getElementById('pane-original');
  const paneGen   = document.getElementById('pane-generated');
  const phOrig    = document.getElementById('placeholder-original');
  const phGen     = document.getElementById('placeholder-generated');
  const urlOrig   = document.getElementById('url-original');
  const urlGen    = document.getElementById('url-generated');

  let blobUrl = null;

  fileInput.addEventListener('change', async () => {
    const file = fileInput.files[0];
    if (!file) return;
    fileLabel.textContent = file.name;

    // show original instantly via blob while upload+generation runs
    if (blobUrl) URL.revokeObjectURL(blobUrl);
    blobUrl = URL.createObjectURL(file);
    showIframe(paneOrig, phOrig, blobUrl);
    urlOrig.textContent = '…uploading';

    clearPane(paneGen, phGen, 'Generating…');
    urlGen.textContent = '';
    statusEl.textContent = 'Generating…';

    const fd = new FormData();
    fd.append('resume_pdf', file);

    try {
      const res  = await fetch('/generate', { method: 'POST', body: fd });
      const data = await res.json();

      if (data.error) {
        clearPane(paneGen, phGen, '✗ ' + data.error);
        statusEl.textContent = '✗ ' + data.error;
        urlOrig.textContent = '';
        return;
      }

      // replace blob with the permanent Supabase URL
      showIframe(paneOrig, phOrig, data.original_url);
      setUrl(urlOrig, data.original_url);

      showIframe(paneGen, phGen, data.generated_url);
      setUrl(urlGen, data.generated_url);
      statusEl.textContent = '';
    } catch (e) {
      clearPane(paneGen, phGen, '✗ Network error');
      statusEl.textContent = '✗ Network error';
    }
  });

  function showIframe(pane, placeholder, src) {
    const old = pane.querySelector('iframe');
    if (old) old.remove();
    placeholder.style.display = 'none';
    const iframe = document.createElement('iframe');
    iframe.src = src;
    pane.insertBefore(iframe, pane.lastElementChild);
  }

  function setUrl(el, url) {
    el.innerHTML = '';
    const a = document.createElement('a');
    a.href = url;
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.textContent = url;
    el.appendChild(a);
  }

  function clearPane(pane, placeholder, msg) {
    const old = pane.querySelector('iframe');
    if (old) old.remove();
    placeholder.textContent = msg;
    placeholder.style.display = '';
  }
</script>
</body>
</html>
"""


@app.get("/")
def index():
    return PAGE_HTML


@app.post("/generate")
def generate():
    uploaded_file = request.files.get("resume_pdf")
    if not uploaded_file or not uploaded_file.filename:
        return jsonify({"error": "No file provided"}), 400

    filename = uploaded_file.filename
    if not filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    original_bytes = uploaded_file.read()
    if not original_bytes:
        return jsonify({"error": "Uploaded file was empty"}), 400

    job_id = uuid.uuid4().hex
    stem   = safe_stem(filename)

    import tempfile
    tmp_in_fd,  tmp_in_path  = tempfile.mkstemp(suffix=".pdf")
    tmp_out_fd, tmp_out_path = tempfile.mkstemp(suffix=".pdf")
    tmp_json_path = tmp_in_path + ".json"
    os.close(tmp_in_fd)
    os.close(tmp_out_fd)

    with open(tmp_in_path, "wb") as f:
        f.write(original_bytes)

    try:
        data, _ = load_resume_data(tmp_in_path, tmp_json_path)
        build_resume_pdf(data, tmp_out_path)

        with open(tmp_out_path, "rb") as f:
            generated_bytes = f.read()

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for p in [tmp_in_path, tmp_json_path, tmp_out_path]:
            try:
                os.unlink(p)
            except Exception:
                pass

    try:
        original_url  = upload_bytes_to_supabase(original_bytes,  "original",  f"{job_id}_{stem}.pdf")
        generated_url = upload_bytes_to_supabase(generated_bytes, "generated", f"{job_id}_{stem}_ats.pdf")
    except Exception as e:
        return jsonify({"error": f"Supabase upload failed: {e}"}), 500

    return jsonify({
        "job_id":        job_id,
        "original_url":  original_url,
        "generated_url": generated_url,
    })


def main() -> None:
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "8501")), debug=True)


if __name__ == "__main__":
    main()
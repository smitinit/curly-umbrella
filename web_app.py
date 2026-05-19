import base64
import hashlib
import os
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
import urllib.error
from pathlib import Path
from urllib.parse import urlparse, quote

import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import build_resume_pdf, load_resume_data


load_dotenv()

st.set_page_config(page_title="ATS Resume Builder", layout="wide")


if "processed_file_hash" not in st.session_state:
    st.session_state.processed_file_hash = ""
if "original_pdf_url" not in st.session_state:
    st.session_state.original_pdf_url = ""
if "generated_pdf_url" not in st.session_state:
    st.session_state.generated_pdf_url = ""
if "generated_pdf_bytes" not in st.session_state:
    st.session_state.generated_pdf_bytes = b""


def pdf_embed_html(pdf_bytes: bytes, height: int = 900) -> str:
    encoded = base64.b64encode(pdf_bytes).decode("utf-8")
    return f"""
    <div style="width:100%; height:{height}px; overflow:auto; background:transparent; padding:0; box-sizing:border-box;">
        <div id="pdf-root" style="display:flex; flex-direction:column; gap:8px; align-items:center;"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
        (async () => {{
            const encoded = "{encoded}";
            const binary = atob(encoded);
            const length = binary.length;
            const bytes = new Uint8Array(length);
            for (let index = 0; index < length; index++) {{
                bytes[index] = binary.charCodeAt(index);
            }}

            pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
            const pdf = await pdfjsLib.getDocument({{ data: bytes }}).promise;
            const root = document.getElementById("pdf-root");

            for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {{
                const page = await pdf.getPage(pageNumber);
                const viewport = page.getViewport({{ scale: 1.35 }});
                const canvas = document.createElement("canvas");
                const context = canvas.getContext("2d");
                canvas.width = viewport.width;
                canvas.height = viewport.height;
                canvas.style.maxWidth = "100%";
                canvas.style.height = "auto";
                canvas.style.margin = "0 auto";
                root.appendChild(canvas);
                await page.render({{ canvasContext: context, viewport }}).promise;
            }}
        }})();
    </script>
    """


def get_storage_settings() -> tuple[str, str, str]:
    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    bucket_name = os.getenv("BUCKET_NAME", "").strip()

    missing = [
        name
        for name, value in [
            ("SUPABASE_URL", supabase_url),
            ("SUPABASE_SERVICE_ROLE_KEY", service_role_key),
            ("BUCKET_NAME", bucket_name),
        ]
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return supabase_url, service_role_key, bucket_name


def build_public_base_url(supabase_url: str) -> str:
    host = urlparse(supabase_url).netloc
    project_ref = host.split(".supabase.co")[0]
    return f"https://{project_ref}.supabase.co/storage/v1/object/public"


def upload_pdf_to_supabase(supabase_url: str, service_role_key: str, bucket_name: str, key: str, pdf_bytes: bytes) -> None:
    upload_url = f"{supabase_url.rstrip('/')}/storage/v1/object/{bucket_name}/{quote(key, safe='/')}"
    request = urllib.request.Request(
        upload_url,
        data=pdf_bytes,
        method="POST",
        headers={
            "Authorization": f"Bearer {service_role_key}",
            "apikey": service_role_key,
            "Content-Type": "application/pdf",
            "x-upsert": "true",
        },
    )

    try:
        with urllib.request.urlopen(request) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase upload failed ({exc.code}): {body}") from exc


def upload_pdf(client: object, bucket_name: str, key: str, pdf_bytes: bytes) -> None:
    # legacy S3 helper removed; kept for reference but no-op to avoid breaking callers
    # This function is intentionally a no-op since we use Supabase Storage API now.
    return None


def fetch_url_bytes(url: str) -> bytes:
    with urllib.request.urlopen(url) as response:
        return response.read()


def safe_stem(filename: str) -> str:
    stem = Path(filename).stem
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in stem).strip("_")
    return cleaned or "resume"


# Minimal UI: header and custom uploader card styles removed per user request.

uploaded_file = st.file_uploader("Upload resume PDF", type=["pdf"], accept_multiple_files=False)

if uploaded_file:
    uploaded_bytes = uploaded_file.getvalue()
    current_hash = hashlib.sha256(uploaded_bytes).hexdigest()

    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.subheader("Uploaded Resume")
        st.components.v1.html(pdf_embed_html(uploaded_bytes), height=920, scrolling=True)
        st.download_button(
            "Download original PDF",
            data=uploaded_bytes,
            file_name=uploaded_file.name,
            mime="application/pdf",
            use_container_width=True,
        )

    if st.session_state.processed_file_hash != current_hash:
        try:
            supabase_url, service_role_key, bucket_name = get_storage_settings()
            public_base_url = build_public_base_url(supabase_url)
            file_stem = safe_stem(uploaded_file.name)
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            original_key = f"original/{file_stem}_{timestamp}.pdf"
            generated_key = f"generated/{file_stem}_{timestamp}_ats.pdf"

            with st.status("Uploading and generating ATS resume...", expanded=True) as status:
                status.write("Uploading the original PDF to Supabase Storage...")
                upload_pdf_to_supabase(supabase_url, service_role_key, bucket_name, original_key, uploaded_bytes)
                original_url = f"{public_base_url}/{bucket_name}/{original_key}"
                status.write(f"Original PDF uploaded: {original_url}")

                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_dir_path = Path(temp_dir)
                    input_pdf_path = temp_dir_path / uploaded_file.name
                    input_pdf_path.write_bytes(uploaded_bytes)

                    status.write("Extracting text and generating the ATS-friendly PDF...")
                    data, _ = load_resume_data(str(input_pdf_path), str(temp_dir_path / "input.json"))
                    output_pdf_path = temp_dir_path / f"{file_stem}_ats.pdf"
                    build_resume_pdf(data, str(output_pdf_path))

                    generated_pdf_bytes = output_pdf_path.read_bytes()
                    status.write("Uploading the ATS PDF to Supabase Storage...")
                    upload_pdf_to_supabase(supabase_url, service_role_key, bucket_name, generated_key, generated_pdf_bytes)

                generated_url = f"{public_base_url}/{bucket_name}/{generated_key}"
                status.write("Fetching uploaded PDFs for browser preview...")
                original_preview_bytes = fetch_url_bytes(original_url)
                generated_preview_bytes = fetch_url_bytes(generated_url)

                st.session_state.processed_file_hash = current_hash
                st.session_state.original_pdf_url = original_url
                st.session_state.generated_pdf_url = generated_url
                st.session_state.generated_pdf_bytes = generated_preview_bytes

                status.update(label="Resume generation complete", state="complete")

            st.success("Resume generated and uploaded successfully.")
        except Exception as exc:
            st.error(str(exc))
            st.stop()

    with right_col:
        st.subheader("ATS-Friendly Resume")
        if st.session_state.processed_file_hash == current_hash and st.session_state.generated_pdf_url:
            st.components.v1.html(pdf_embed_html(st.session_state.generated_pdf_bytes), height=920, scrolling=True)
            st.download_button(
                "Download ATS PDF",
                data=st.session_state.generated_pdf_bytes,
                file_name=f"{safe_stem(uploaded_file.name)}_ats.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
            st.markdown(f"[Open original PDF]({st.session_state.original_pdf_url})")
            st.markdown(f"[Open ATS PDF]({st.session_state.generated_pdf_url})")
        else:
            st.info("Processing the resume. The ATS version will appear here when it is ready.")
else:
    left_col, right_col = st.columns(2, gap="large")
    with left_col:
        st.subheader("Uploaded Resume")
        st.info("Upload a PDF to preview it here.")
    with right_col:
        st.subheader("ATS-Friendly Resume")
        st.info("Your generated ATS PDF will appear here after processing.")
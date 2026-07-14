import logging
from app.graph.state import ResearchState

logger = logging.getLogger(__name__)

def compress_node(state: ResearchState) -> dict:
    findings = state.get("findings", [])
    logger.info(f"Compress Node: Cleaning and deduplicating {len(findings)} raw findings")

    seen_urls = set()
    unique_findings = []
    
    for f in findings:
        # Check both "link" and "url" fields (SearXNG often uses "link")
        url = f.get("link") or f.get("url") or ""
        title = f.get("title", "").strip().lower()
        
        # Deduplicate by URL
        if url:
            if url in seen_urls:
                continue
            seen_urls.add(url)
            
        unique_findings.append(f)

    # Compile the unique findings into a clean context string
    compressed_lines = []
    for idx, f in enumerate(unique_findings):
        title = f.get("title", "No Title").strip()
        content = f.get("content") or f.get("snippet") or ""
        content = content.strip()
        url = f.get("link") or f.get("url") or ""
        
        if not content:
            continue
            
        compressed_lines.append(
            f"Kaynak [{idx + 1}]: {title}\n"
            f"Bağlantı: {url}\n"
            f"Bilgi: {content}\n"
        )

    compressed_findings = "\n".join(compressed_lines)
    logger.info(f"Compress Node: Compressed into {len(unique_findings)} unique sources ({len(compressed_findings)} chars)")

    return {
        "status": "compressing",
        "compressed_findings": compressed_findings
    }

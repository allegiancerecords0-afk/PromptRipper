import os
import json
import sys
from PIL import Image

def extract_info(filepath):
    """Extract positive prompt (from any node's 'preview' input) + sampler info from the embedded JSON."""
    try:
        with Image.open(filepath) as img:
            prompt_str = img.info.get("prompt")
            if not prompt_str:
                return None
            
            data = json.loads(prompt_str)
            
            preview = None
            steps = None
            sampler = None
            scheduler = None
            
            for node in data.values():
                if not isinstance(node, dict):
                    continue
                
                inputs = node.get("inputs", {})
                
                # Positive prompt from "preview"
                p = inputs.get("preview")
                if isinstance(p, str) and p.strip():
                    preview = p.strip()
                
                # Sampler info (first occurrence)
                if steps is None and "steps" in inputs:
                    steps = inputs.get("steps")
                if sampler is None and "sampler_name" in inputs:
                    sampler = inputs.get("sampler_name")
                if scheduler is None and "scheduler" in inputs:
                    scheduler = inputs.get("scheduler")
            
            if preview is None:
                return None
                
            return {
                "prompt": preview,
                "steps": steps,
                "sampler": sampler,
                "scheduler": scheduler
            }
    except Exception:
        pass
    return None


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "."
    
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a folder.")
        sys.exit(1)
    
    seen = set()
    unique_entries = []
    
    print(f"Scanning {folder} for ComfyUI images...\n")
    
    for filename in sorted(os.listdir(folder)):
        if not filename.lower().endswith((".png", ".webp")):
            continue
            
        filepath = os.path.join(folder, filename)
        info = extract_info(filepath)
        
        if info and info["prompt"] and info["prompt"] not in seen:
            seen.add(info["prompt"])
            info["filename"] = filename                    # ← added here
            unique_entries.append(info)
            steps_str = info.get("steps") or "N/A"
            sampler_str = info.get("sampler") or "N/A"
            print(f"✓ Extracted from {filename} → Steps: {steps_str} | Sampler: {sampler_str}")
        elif info:
            print(f"→ Duplicate prompt skipped: {filename}")
    
    # === FINAL OUTPUT FORMAT (exactly as requested) ===
    output_file = "unique_positive_prompts.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for i, info in enumerate(unique_entries, 1):
            f.write(f"{i}. {info['filename']}\n")          # ← filename right after the number
            f.write(f"Steps: {info.get('steps') or 'N/A'}\n")
            f.write(f"Sampler: {info.get('sampler') or 'N/A'}\n")
            f.write(f"Scheduler: {info.get('scheduler') or 'N/A'}\n")
            f.write("\n")                                  # line break after settings
            f.write(f"Prompt: {info['prompt']}\n")
            f.write("\n")                                  # blank line between entries
    
    print(f"\nDone! Found {len(unique_entries)} unique entries.")
    print(f"Saved to: {os.path.abspath(output_file)}")


if __name__ == "__main__":
    main()
"""
STEP 2: Prepare YouTube Data for Fine-Tuning
Converts raw manual text transcripts from folder into training format
"""

import json
import os
from pathlib import Path
import re

def clean_text(text):
    """Clean transcript text from manual UI copy-paste"""
    # Remove timestamps like 0:00 and hidden screen-reader text like '1 minute, 2 seconds'
    text = re.sub(r'\d{1,2}:\d{2}(?::\d{2})?\d*(?:\s*minute[s]?,?)?(?:\s*\d*\s*second[s]?)?', '', text)
    # Remove extra whitespace and newlines
    text = ' '.join(text.split())
    # Remove brackets and parentheses content usually denoting music/sound
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    return text.strip()

def create_training_samples(raw_data_dict, min_chunk_length=200, max_chunk_length=1500):
    """
    Convert transcripts into training samples.
    Chunks are generated specifically so long 20-minute transcripts aren't lost.
    """
    print("\n" + "="*60)
    print("PREPARING TRAINING DATA")
    print("="*60 + "\n")
    
    training_samples = []
    
    for filename, raw_transcript in raw_data_dict.items():
        transcript = clean_text(raw_transcript)
        
        # Split transcript into meaningful chunks
        sentences = transcript.split('. ')
        
        current_chunk = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence: continue
            if not sentence.endswith('.'):
                sentence += "."
                
            # If a single sentence is incredibly long (e.g., no punctuation in file)
            # we must force a split so we don't lose the data
            if len(sentence) > max_chunk_length:
                # Add existing chunk if any
                if len(current_chunk) >= min_chunk_length:
                    training_samples.append({
                        "instruction": "You are an expert advisor. Answer questions based on the following content.",
                        "input": current_chunk.strip(),
                        "output": "I have understood this content and can answer questions about it.",
                        "source": filename
                    })
                current_chunk = ""
                
                # Force chunk the long sentence arbitrarily by space
                words = sentence.split(' ')
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 <= max_chunk_length:
                        temp_chunk += " " + word
                    else:
                        if len(temp_chunk) >= min_chunk_length:
                            training_samples.append({
                                "instruction": "You are an expert advisor. Answer questions based on the following content.",
                                "input": temp_chunk.strip(),
                                "output": "I have understood this content and can answer questions about it.",
                                "source": filename
                            })
                        temp_chunk = word
                current_chunk = temp_chunk
                continue
                
            if len(current_chunk) + len(sentence) <= max_chunk_length:
                current_chunk += " " + sentence
            else:
                if len(current_chunk) >= min_chunk_length:
                    # Create training sample format
                    training_samples.append({
                        "instruction": "You are an expert advisor. Answer questions based on the following content.",
                        "input": current_chunk.strip(),
                        "output": "I have understood this content and can answer questions about it.",
                        "source": filename
                    })
                current_chunk = sentence
        
        # Don't lose the last chunk
        if len(current_chunk) >= min_chunk_length:
            training_samples.append({
                "instruction": "You are an expert advisor. Answer questions based on the following content.",
                "input": current_chunk.strip(),
                "output": "I have understood this content and can answer questions about it.",
                "source": filename
            })
    
    print(f"Created {len(training_samples)} training chunks\n")
    return training_samples

def save_training_data(samples, output_file='training_data.json'):
    """Save training samples to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(samples)} training samples to {output_file}")

def analyze_data(samples):
    """Analyze the prepared data"""
    print("\n" + "="*60)
    print("DATA ANALYSIS")
    print("="*60)
    
    if not samples:
        print("❌ No samples found")
        return
    
    lengths = [len(s['input'].split()) for s in samples]
    
    print(f"Total chunks: {len(samples)}")
    print(f"Average words per chunk: {sum(lengths) // len(lengths)}")
    print(f"Min words: {min(lengths)}")
    print(f"Max words: {max(lengths)}")
    print(f"Total training words: {sum(lengths):,}")
    
    # Quality check
    good_samples = sum(1 for s in samples if 100 < len(s['input'].split()) < 500)
    print(f"\nChunks in ideal range (100-500 words): {good_samples}")
    print(f"Quality score: {(good_samples/len(samples)*100):.1f}%")
    
    print("\n" + "="*60)
    print("First chunk sample:")
    print("="*60)
    if samples:
        s = samples[0]
        print(f"Instruction: {s['instruction']}")
        print(f"Input: {s['input'][:300]}...")
        print(f"Output: {s['output']}")
    
    print("="*60 + "\n")

def main():
    print("="*60)
    print("TRAINING DATA PREPARATION PIPELINE")
    print("="*60)
    
    manual_dir = Path("manual_transcripts")
    if not manual_dir.exists():
        print("❌ manual_transcripts folder not found!")
        print("   Creating it now. Please drop your .txt transcript files inside and run again.")
        manual_dir.mkdir(exist_ok=True)
        return

    # Load extracted data
    print("\n1️⃣  Loading raw transcripts from text files...")
    
    raw_data_dict = {}
    files = list(manual_dir.glob("*.txt"))
    if not files:
        print("❌ No .txt files found in manual_transcripts/ directory.")
        print("   Please copy and paste transcripts from YouTube into individual .txt files.")
        return

    for txt_file in files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            raw_data_dict[txt_file.name] = f.read()

    print(f"✅ Loaded {len(raw_data_dict)} transcript files")
        
    # Create training samples
    print("\n2️⃣  Creating training chunks...")
    samples = create_training_samples(raw_data_dict, min_chunk_length=200, max_chunk_length=1500)
    
    # Save
    print("\n3️⃣  Saving training data...")
    save_training_data(samples, 'training_data.json')
    
    # Analyze
    print("\n4️⃣  Analyzing data quality...")
    analyze_data(samples)
    
    print("\n✅ READY FOR AI EMBEDDING/TRAINING!")
    
if __name__ == "__main__":
    main()

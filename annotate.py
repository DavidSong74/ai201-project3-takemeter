import json
import csv
import os
import sys

RAW_FILE = "data/raw_comments.json"
LABELED_FILE = "data/labeled_comments.csv"

LABELS = {
    "1": "analytical_and_fact_based",
    "2": "subjective_opinion_and_banter",
    "3": "social_and_cultural_meta"
}

def load_raw_comments():
    if not os.path.exists(RAW_FILE):
        print(f"Error: {RAW_FILE} not found. Please run the scraper first.")
        sys.exit(1)
    with open(RAW_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_existing_annotations():
    annotations = {}
    if os.path.exists(LABELED_FILE):
        try:
            with open(LABELED_FILE, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Key by comment text (since that is unique and the required text column)
                    annotations[row['text']] = {
                        'label': row['label'],
                        'difficulty_notes': row.get('difficulty_notes', '')
                    }
        except Exception as e:
            print(f"Warning: Could not load existing annotations: {e}")
    return annotations

def save_annotations(annotations_dict):
    try:
        with open(LABELED_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['text', 'label', 'difficulty_notes'])
            for text, data in annotations_dict.items():
                writer.writerow([text, data['label'], data['difficulty_notes']])
    except Exception as e:
        print(f"Error saving to CSV: {e}")

def print_summary(annotations_dict):
    total = len(annotations_dict)
    print("\n" + "="*40)
    print(f"Annotation Summary ({total} labeled comments):")
    counts = {}
    for data in annotations_dict.values():
        lbl = data['label']
        counts[lbl] = counts.get(lbl, 0) + 1
    
    for key, val in LABELS.items():
        count = counts.get(val, 0)
        pct = (count / total * 100) if total > 0 else 0
        print(f"  [{key}] {val:<30} : {count:<4} ({pct:.1f}%)")
    print("="*40 + "\n")

def run_annotations():
    comments = load_raw_comments()
    annotations = load_existing_annotations()
    
    print(f"Loaded {len(comments)} raw comments.")
    print(f"Loaded {len(annotations)} existing annotations.")
    
    # Filter comments that haven't been labeled yet
    unlabeled = [c for c in comments if c['body'] not in annotations]
    
    if not unlabeled:
        print("All comments have already been annotated!")
        print_summary(annotations)
        return

    print("\nAnnotation Guidelines:")
    for key, val in LABELS.items():
        print(f"  [{key}] -> {val}")
    print("  [s] -> Skip this comment")
    print("  [q] -> Quit and save progress")
    print("-" * 50)
    
    try:
        for idx, comment in enumerate(unlabeled):
            text = comment['body']
            thread = comment['thread_title']
            author = comment['author']
            
            # Print current item progress
            progress_str = f"Item {len(annotations) + 1} / {len(comments)} (Remaining Unlabeled: {len(unlabeled) - idx})"
            
            print(f"\n{progress_str}")
            print(f"Thread: {thread}")
            print(f"Author: {author}")
            print(f"URL: {comment.get('permalink', 'N/A')}")
            print("-" * 50)
            print(text)
            print("-" * 50)
            
            # Get label input
            while True:
                choice = input("Select label [1/2/3/s/q]: ").strip().lower()
                if choice in ['q', 'quit']:
                    print("\nQuitting...")
                    print_summary(annotations)
                    return
                elif choice == 's':
                    print("Skipped.")
                    break
                elif choice in LABELS:
                    label_name = LABELS[choice]
                    
                    # Optional notes
                    notes = input("Optional difficulty notes (press Enter to skip): ").strip()
                    
                    annotations[text] = {
                        'label': label_name,
                        'difficulty_notes': notes
                    }
                    save_annotations(annotations)
                    print(f"Saved: {label_name}")
                    break
                else:
                    print("Invalid input. Please enter 1, 2, 3, s, or q.")
                    
        print("\nAll available comments have been annotated!")
        print_summary(annotations)
        
    except KeyboardInterrupt:
        print("\nInterrupted. Progress saved.")
        print_summary(annotations)

if __name__ == "__main__":
    run_annotations()

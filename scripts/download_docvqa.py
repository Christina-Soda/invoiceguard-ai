from datasets import load_dataset

ds = load_dataset(
    "nielsr/docvqa_1200_examples",
    cache_dir="data/raw/docvqa_cache"
)

ds.save_to_disk("data/raw/docvqa")

print(ds)
print("Saved to data/raw/docvqa")

import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer


class DNAVariantDataset(Dataset):
    """
    Dataset untuk fine-tuning DNABERT-2 pada varian patogenik ClinVar.

    Sumber data: InstaDeepAI/genomics-long-range-benchmark
                 task: variant_effect_pathogenic_clinvar

    Kolom yang tersedia di dataset:
      - 'ref_forward_sequence' : sekuens referensi (tanpa mutasi)
      - 'alt_forward_sequence' : sekuens alternatif (dengan mutasi)
      - 'label'                : 0 = benign, 1 = pathogenic

    Strategi embedding (dari Feng et al., Nature Comms 2025):
      embedding(alt) - embedding(ref) lebih informatif daripada hanya alt,
      karena menangkap EFEK mutasi bukan hanya konteks sekuens.
    """

    LABEL_NAMES = ["Benign", "Pathogenic"]
    NUM_CLASSES = 2

    def __init__(self, data, tokenizer_name: str = "zhihan1996/DNABERT-2-117M", max_length: int = 512):
        self.data = data
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, trust_remote_code=True)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # Nama kolom di InstaDeepAI genomics-long-range-benchmark
        ref_seq = str(
            item.get("ref_forward_sequence") or item.get("ref") or ""
        ).upper()
        alt_seq = str(
            item.get("alt_forward_sequence") or item.get("alt") or item.get("sequence") or ""
        ).upper()

        label = int(item.get("label", 0))

        def _tokenize(seq: str) -> dict:
            return self.tokenizer(
                seq,
                max_length=self.max_length,
                padding="max_length",
                truncation=True,
                return_tensors="pt",
            )

        ref_enc = _tokenize(ref_seq)
        alt_enc = _tokenize(alt_seq)

        return {
            "ref_input_ids":      ref_enc["input_ids"].squeeze(0),
            "ref_attention_mask": ref_enc["attention_mask"].squeeze(0),
            "alt_input_ids":      alt_enc["input_ids"].squeeze(0),
            "alt_attention_mask": alt_enc["attention_mask"].squeeze(0),
            "label":              torch.tensor(label, dtype=torch.long),
        }

import sys
import types
import importlib.util
import torch
import torch.nn as nn

# triton is a Linux-only package. PyTorch inductor and DNABERT-2's custom code
# both attempt to import triton (and its submodules) unconditionally. Install a
# meta-path finder that satisfies every `import triton.*` with an empty stub
# module, preventing ImportError on Windows/CPU where triton is unavailable.
if "triton" not in sys.modules:
    class _TritonAttr:
        """Placeholder for any triton attribute access (e.g. triton.language.dtype)."""
        def __init__(self, name="triton"):
            self._n = name
        def __getattr__(self, n):
            return _TritonAttr(f"{self._n}.{n}")
        def __call__(self, *a, **kw):
            return _TritonAttr(f"{self._n}()")
        def __repr__(self):
            return f"<triton-stub:{self._n}>"

    class _TritonModule(types.ModuleType):
        def __getattr__(self, name):
            if name.startswith("__"):
                raise AttributeError(name)
            val = _TritonAttr(f"{self.__name__}.{name}")
            setattr(self, name, val)
            return val

    class _TritonLoader:
        def create_module(self, spec):
            mod = _TritonModule(spec.name)
            mod.__file__ = "<triton-stub>"
            mod.__package__ = spec.name.rpartition(".")[0] or spec.name
            mod.__path__ = []       # marks it as a package so sub-imports work
            mod.__loader__ = self
            return mod
        def exec_module(self, module):
            pass                    # nothing to execute

    class _TritonFinder:
        _loader = _TritonLoader()
        def find_spec(self, fullname, path, target=None):
            if fullname == "triton" or fullname.startswith("triton."):
                spec = importlib.util.spec_from_loader(fullname, self._loader)
                spec.submodule_search_locations = []
                return spec
            return None

    sys.meta_path.insert(0, _TritonFinder())

from transformers import AutoModel, AutoConfig


class DNAVariantClassifier(nn.Module):
    """
    DNABERT-2 + classification head untuk prediksi patogenisitas varian DNA.

    Arsitektur yang dilatih di Kaggle:
      diff_emb = mean_pool(alt) - mean_pool(ref)   [768]
      classifier: Linear(768 → hidden_dim) → ReLU → Dropout → Linear(hidden_dim → 2)
    """

    def __init__(
        self,
        model_name: str = "zhihan1996/DNABERT-2-117M",
        num_classes: int = 2,
        hidden_dim: int = 512,
        dropout: float = 0.1,
    ):
        super().__init__()
        config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
        # DNABERT-2's custom bert_layers.py accesses config.pad_token_id but newer
        # transformers versions may not set it on BertConfig. Default BERT pad = 0.
        if not hasattr(config, "pad_token_id") or config.pad_token_id is None:
            config.pad_token_id = 0
        # attn_implementation="eager" avoids triton/flash-attention (Linux-only).
        # low_cpu_mem_usage=False disables meta-device init: DNABERT-2's
        # rebuild_alibi_tensor creates CPU tensors and crashes when mixed with
        # meta tensors introduced by newer transformers defaults.
        self.encoder = AutoModel.from_pretrained(
            model_name,
            trust_remote_code=True,
            config=config,
            attn_implementation="eager",
            low_cpu_mem_usage=False,
        )

        # bert_layers.py falls back to PyTorch attention only when
        # flash_attn_qkvpacked_func is None. The triton stub above makes the
        # import succeed (non-None), but the triton kernel asserts CUDA tensors.
        # Null it out so the CPU-safe path is always taken.
        for _mod in sys.modules.values():
            if getattr(_mod, '__name__', None) and 'bert_layers' in _mod.__name__:
                if hasattr(_mod, 'flash_attn_qkvpacked_func'):
                    _mod.flash_attn_qkvpacked_func = None

        encoder_dim = getattr(config, "hidden_size", 768)

        # Matches training: diff_emb (encoder_dim) → hidden_dim → num_classes
        self.classifier = nn.Sequential(
            nn.Linear(encoder_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_classes),
        )
        self.num_classes = num_classes

    def _mean_pool(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        hidden_states = outputs[0]                          # [B, seq_len, H]
        mask = attention_mask.unsqueeze(-1).float()         # [B, seq_len, 1]
        return (hidden_states * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)

    def forward(
        self,
        alt_input_ids: torch.Tensor,
        alt_attention_mask: torch.Tensor,
        ref_input_ids: torch.Tensor,
        ref_attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        alt_emb = self._mean_pool(alt_input_ids, alt_attention_mask)
        ref_emb = self._mean_pool(ref_input_ids, ref_attention_mask)
        diff_emb = alt_emb - ref_emb                        # [B, 768]
        return self.classifier(diff_emb)

    def freeze_encoder(self):
        for param in self.encoder.parameters():
            param.requires_grad = False

    def unfreeze_encoder(self):
        for param in self.encoder.parameters():
            param.requires_grad = True

    def get_embedding(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return self._mean_pool(input_ids, attention_mask)

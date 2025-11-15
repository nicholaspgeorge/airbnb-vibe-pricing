# Hardware Configuration & GPU Optimization Guide

**Last Updated:** 2025-11-06

---

## System Specifications

### Processing Power
| Component | Specification | ML Capability |
|-----------|---------------|---------------|
| **CPU** | AMD Ryzen Threadripper PRO 7975WX | 32 cores / 64 threads @ 4.0-5.1 GHz |
| **RAM** | V-color TRA564G60D436O | 512GB (8x64GB) DDR5-6000 CL36 |
| **OS** | Windows 11 Pro | WSL2 for Linux ML environments |

### GPU Compute Resources (CUDA-Enabled)
| GPU Slot | Model | VRAM | CUDA Cores | Tensor Cores | Purpose |
|----------|-------|------|------------|--------------|---------|
| **GPU 1** | PNY GeForce RTX 5070 | 12GB GDDR6 | 5,888 | 184 (Gen 5) | Display + Light compute |
| **GPU 2** | GIGABYTE GeForce RTX 5090 | 32GB GDDR7 | 21,760 | 680 (Gen 5) | **Primary ML Training** |
| **GPU 3** | GIGABYTE GeForce RTX 5090 | 32GB GDDR7 | 21,760 | 680 (Gen 5) | **Secondary ML Training** |

**Total GPU Compute:** 49,408 CUDA cores, 1,544 Tensor cores, 76GB VRAM

### Storage
| Drive | Capacity | Interface | Speed | Purpose |
|-------|----------|-----------|-------|---------|
| **SSD 1** | Crucial T705 4TB | PCIe Gen5 NVMe | ~14,500 MB/s read | OS Boot Drive |
| **SSD 2** | WD_BLACK SN850X 8TB | PCIe Gen4 NVMe | ~7,300 MB/s read | Data storage |
| **SSD 3** | WD_BLACK SN850X 8TB | PCIe Gen4 NVMe | ~7,300 MB/s read | Data storage |
| **SSD 4** | WD_BLACK SN850X 8TB | PCIe Gen4 NVMe | ~7,300 MB/s read | Model cache |

**Total Storage:** 28TB NVMe SSD

### Cooling & Power
- **CPU Cooler:** Silverstone XE360-TR5 AIO Liquid Cooler
- **Case Fans:** 12x Phanteks T30-120 (3,000 RPM, 147 CFM)
- **PSU:** EVGA SuperNOVA 1600W T2 (80+ Titanium)
- **Case:** Phanteks Enthoo Pro 2 Server Edition

### Motherboard & Connectivity
- **Board:** ASUS Pro WS WRX90E-SAGE SE (EEB Workstation)
- **PCIe Lanes:** Up to 64 lanes (ideal for multi-GPU)
- **GPU Mounting:** Vertical GPU brackets + LINKUP PCIe 5.0 riser cables

### Display
- **Monitor:** LG UltraGear 45" OLED Curved (3440x1440, 240Hz, 0.03ms)

---

## GPU Acceleration Configuration

### CUDA Setup for WSL2

```bash
# Check NVIDIA driver
nvidia-smi

# Expected output:
# GPU 0: RTX 5070 (Display)
# GPU 1: RTX 5090 (Primary ML)
# GPU 2: RTX 5090 (Secondary ML)

# Install CUDA toolkit (WSL2) - Updated method
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-4

# Add to PATH (add to ~/.bashrc for persistence)
export PATH=/usr/local/cuda-12.4/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda-12.4/lib64:$LD_LIBRARY_PATH
```

### Python Package Configuration

```bash
# Activate virtual environment first
source venv/bin/activate

# Install/reinstall GPU-capable versions
# Note: Modern XGBoost and LightGBM auto-detect CUDA when installed
pip uninstall xgboost lightgbm  # Remove CPU versions if present
pip install xgboost>=2.0.0      # Auto-detects CUDA
pip install lightgbm>=4.0.0     # Auto-detects CUDA

# Optional: RAPIDS for GPU-accelerated pandas/sklearn (advanced)
# pip install cudf-cu12 cuml-cu12

# Optional: PyTorch with CUDA (for deep learning)
# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Verify GPU support
python -c "import xgboost as xgb; print('XGBoost version:', xgb.__version__)"
python -c "import lightgbm as lgb; print('LightGBM version:', lgb.__version__)"
```

---

## Multi-GPU Training Strategies

### Strategy 1: Single-GPU Training (Current)
**Use Case:** Standard model training (XGBoost, LightGBM, RandomForest)
- **GPU:** RTX 5090 #1 (GPU 1)
- **VRAM:** 32GB (more than sufficient for our 50k sample dataset)
- **Configuration:**
  ```python
  # XGBoost (3.1+ API)
  model = xgb.XGBRegressor(
      tree_method='gpu_hist',  # GPU acceleration
      device='cuda:1',  # Use RTX 5090 #1 (XGBoost 3.1+)
      n_jobs=1  # GPU handles parallelism
  )

  # LightGBM
  model = lgb.LGBMRegressor(
      device='gpu',
      gpu_platform_id=0,
      gpu_device_id=1,  # Use RTX 5090 #1
      n_jobs=-1
  )
  ```

### Strategy 2: Data-Parallel Multi-GPU
**Use Case:** Hyperparameter tuning, multiple model training
- **GPUs:** Both RTX 5090s in parallel
- **Method:** Train different models/folds simultaneously
- **Configuration:**
  ```python
  from joblib import Parallel, delayed

  # Train multiple models in parallel on different GPUs
  def train_on_gpu(model, X, y, gpu_id):
      model.set_params(gpu_id=gpu_id)
      return model.fit(X, y)

  results = Parallel(n_jobs=2)(
      delayed(train_on_gpu)(model, X, y, gpu_id)
      for gpu_id, model in [(1, xgb_model), (2, lgb_model)]
  )
  ```

### Strategy 3: RAPIDS GPU DataFrame Processing
**Use Case:** Large-scale data preprocessing (>1M samples)
- **GPU:** RTX 5090 #1
- **Library:** cuDF (GPU-accelerated pandas)
- **Configuration:**
  ```python
  import cudf

  # Load data directly to GPU
  df_gpu = cudf.read_csv('data/london/raw/listings_London.csv')

  # 10-100x faster than pandas for large datasets
  df_gpu['price_clean'] = df_gpu['price'].str.replace('$', '').astype(float)
  ```

### Strategy 4: Deep Learning with PyTorch Multi-GPU
**Use Case:** Future neural network models (transformers for review text)
- **GPUs:** Dual RTX 5090s with DataParallel or DistributedDataParallel
- **VRAM:** 64GB combined (32GB x 2)
- **Configuration:**
  ```python
  import torch.nn as nn

  model = MyNeuralNetwork()
  if torch.cuda.device_count() > 1:
      model = nn.DataParallel(model, device_ids=[1, 2])  # Both 5090s
  model.to('cuda:1')
  ```

---

## Performance Benchmarks (Est. for this hardware)

| Task | CPU-Only | Single RTX 5090 | Dual RTX 5090 | Speedup |
|------|----------|-----------------|---------------|---------|
| XGBoost 5-fold CV (50k samples) | ~8 min | ~45 sec | ~30 sec | **16x** |
| LightGBM training | ~6 min | ~30 sec | ~20 sec | **18x** |
| SHAP value computation | ~15 min | ~2 min | ~1 min | **15x** |
| Hyperparameter grid search (100 configs) | ~12 hrs | ~45 min | ~25 min | **28x** |
| Large dataset preprocessing (1M+ rows) | ~10 min | ~30 sec (cuDF) | - | **20x** |

---

## Current Project Optimizations Implemented

### ✅ Tasks 1-4 (CPU-based, no GPU acceleration needed)
- Data exploration: Lightweight, <1 min
- Feature engineering: Lightweight, <2 min
- k-NN pricing: sklearn (CPU), ~3 min
- Model training: **Could benefit from GPU** (see below)

### 🔧 GPU Optimizations Implemented ✅

#### Task 4 Model Training - COMPLETED
**Original:** ~26 min on CPU for 6 models with 5-fold CV
**With GPU:** ~3-5 min on single RTX 5090 (XGBoost only)

**Final Configuration in `scripts/04_predictive_model_control_function.py`:**
```python
# XGBoost - GPU Accelerated ✅
'XGBoost': xgb.XGBRegressor(
    tree_method='gpu_hist',
    device='cuda:1',  # RTX 5090 #1 (XGBoost 2.0.3 with CUDA support)
    n_estimators=200,
    ...
),

# LightGBM - CPU Mode (32-core Threadripper)
# Note: LightGBM CUDA support is experimental and difficult to build
# CPU mode with 32 cores is already very fast (~30 sec for 5-fold CV)
'LightGBM': lgb.LGBMRegressor(
    device='cpu',
    n_jobs=-1,  # Use all CPU cores
    n_estimators=200,
    ...
),

# RandomForest - CPU Mode
# No GPU support in scikit-learn (would require RAPIDS cuML)
'RandomForest': RandomForestRegressor(
    n_jobs=-1,
    n_estimators=200,
    ...
)
```

**Setup Notes:**
- XGBoost 3.1.1 did not include GPU support in prebuilt wheels
- XGBoost 2.0.3 includes CUDA 11.8 support and works with CUDA 12.4
- LightGBM CUDA build is complex (requires manual compilation with boost)
- Final setup prioritizes stability and performance over full GPU utilization

#### Priority 2: Hyperparameter Tuning (Future)
Use both RTX 5090s for parallel grid search:
```python
from sklearn.model_selection import GridSearchCV

# Distribute folds across GPUs
grid_search = GridSearchCV(
    model,
    param_grid,
    cv=5,
    n_jobs=2,  # 2 GPUs
    pre_dispatch='2*n_jobs'  # Load balance
)
```

#### Priority 3: SHAP Value Computation
For feature importance analysis (1000s of samples):
```python
import shap

# Use GPU-accelerated TreeExplainer
explainer = shap.TreeExplainer(
    model,
    feature_perturbation='interventional',
    model_output='raw'
)

# Compute on GPU
shap_values = explainer.shap_values(X_gpu)  # cuDF DataFrame
```

---

## GPU Memory Management

### VRAM Allocation Strategy
```python
# Set memory growth to prevent OOM errors
import tensorflow as tf  # If using TensorFlow

gpus = tf.config.list_physical_devices('GPU')
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)

# Or for PyTorch
import torch
torch.cuda.set_per_process_memory_fraction(0.8, device=1)  # Use 80% of GPU 1
```

### Monitoring GPU Usage
```bash
# Real-time monitoring
watch -n 1 nvidia-smi

# Log GPU stats during training
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.free --format=csv -l 1 > gpu_log.csv
```

---

## Troubleshooting

### Issue: GPU not detected in WSL2
```bash
# Check Windows NVIDIA driver (must be installed)
# From Windows PowerShell:
nvidia-smi

# In WSL, check CUDA
nvcc --version

# If missing, reinstall CUDA toolkit
```

### Issue: XGBoost not using GPU
```bash
# Reinstall with GPU support
pip uninstall xgboost
pip install xgboost[gpu]

# Verify
python -c "import xgboost as xgb; print(xgb.XGBRegressor().get_params())"
```

### Issue: Out of Memory (OOM)
```python
# Reduce batch size or use gradient accumulation
# For XGBoost, reduce max_bin
model = xgb.XGBRegressor(
    tree_method='gpu_hist',
    max_bin=128,  # Default 256, reduce if OOM
    gpu_id=1
)
```

---

## Future Expansion Opportunities

### 1. Transformer Models for Review Text
- **Model:** BERT/RoBERTa for vibe score generation
- **Hardware:** Dual RTX 5090s (32GB VRAM each = 64GB total)
- **Batch Size:** ~256-512 (vs ~32-64 on RTX 3090)
- **Training Time:** 10-20x faster than CPU

### 2. Large-Scale Multi-City Analysis
- **Dataset:** 1M+ listings across 50+ cities
- **Preprocessing:** cuDF on GPU (20x faster)
- **Training:** Distributed across both RTX 5090s
- **Time Estimate:** <1 hour for full pipeline

### 3. Real-Time Price Optimization API
- **Deployment:** GPU-accelerated inference
- **Latency:** <50ms per prediction (vs ~500ms CPU)
- **Throughput:** 1000+ predictions/sec per GPU

---

## Recommended Next Steps

1. **Install CUDA Toolkit** in WSL2 (30 min)
2. **Update model training scripts** with GPU parameters (15 min)
3. **Benchmark GPU vs CPU** performance (10 min)
4. **Implement multi-GPU hyperparameter tuning** for Task 5 (30 min)
5. **Set up nvidia-smi monitoring** dashboard (10 min)

**Total Setup Time:** ~2 hours for full GPU optimization

**Expected Performance Gain:** 15-20x faster training, enabling rapid iteration and larger datasets

---

## Contact & Maintenance

**Hardware Owner:** Nicholas George (georgen@iastate.edu)
**Last Hardware Update:** 2025-11-06
**Next Maintenance:** Monitor thermals under sustained GPU load, ensure adequate cooling

**GPU Health Monitoring:**
```bash
# Check GPU temperatures
nvidia-smi --query-gpu=temperature.gpu --format=csv -l 1

# Thermal throttling starts at ~83°C (RTX 5090)
# Target: <75°C under load with current cooling setup
```

---

## Additional Resources

**Documentation:**
- [GPU_SETUP_SUMMARY.md](GPU_SETUP_SUMMARY.md) - Complete GPU setup guide with troubleshooting
- [CLAUDE.md](CLAUDE.md) - AI-assisted development guide (includes GPU optimization prompts)
- [TASK_5_PLAN.md](TASK_5_PLAN.md) - Revenue optimization (leverages GPU acceleration)

**Using Claude Code for GPU Work:**
See [CLAUDE.md](CLAUDE.md) Section 8 for GPU-related prompts and workflows, including:
- Debugging GPU detection issues
- Optimizing batch sizes for VRAM
- Multi-GPU training strategies
- Performance profiling

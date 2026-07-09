use std::f64::consts::PI;

#[derive(Debug, Clone)]
pub struct EngineOutput {
    pub stabilized_vector: Vec<f64>, // always len 24
    pub drift_score: f64,            // [0, 1]
    pub euler_chi: f64,
    pub genus: f64,
    pub beta0: f64,
    pub beta1: f64,
}

#[derive(Debug, Clone)]
pub struct EngineState {
    nx: usize,
    ny: usize,
    n_fields: usize,
    seed: u64,
    state_vec: [f64; 24],
    tick: u64,
}

impl EngineState {
    pub fn new(nx: usize, ny: usize, n_fields: usize, seed: u64) -> Self {
        let mut state = [0.0_f64; 24];
        for (i, v) in state.iter_mut().enumerate() {
            let t = (seed as f64 * 0.013) + (i as f64 * 0.37);
            *v = (t.sin() * 0.5 + t.cos() * 0.25).clamp(-1.0, 1.0);
        }

        Self {
            nx,
            ny,
            n_fields,
            seed,
            state_vec: state,
            tick: 0,
        }
    }

    pub fn stabilize(&mut self, metric_window: Vec<f64>, embedding: Option<Vec<f64>>) -> EngineOutput {
        let clean_metrics: Vec<f64> = metric_window
            .into_iter()
            .map(|x| if x.is_finite() { x } else { 0.0 })
            .collect();

        let n = clean_metrics.len().max(1) as f64;
        let mean = clean_metrics.iter().sum::<f64>() / n;
        let var = clean_metrics
            .iter()
            .map(|x| {
                let d = *x - mean;
                d * d
            })
            .sum::<f64>()
            / n;
        let std = var.sqrt();

        let mean_abs = clean_metrics.iter().map(|x| x.abs()).sum::<f64>() / n;
        let scale = (std + mean_abs * 0.5 + 1e-6).max(1e-6);

        let (emb_mean, emb_energy) = match embedding {
            Some(v) if !v.is_empty() => {
                let finite_vals: Vec<f64> = v.into_iter().filter(|x| x.is_finite()).collect();
                if finite_vals.is_empty() {
                    (0.0, 0.0)
                } else {
                    let denom = finite_vals.len() as f64;
                    let m = finite_vals.iter().sum::<f64>() / denom;
                    let e = finite_vals.iter().map(|x| x * x).sum::<f64>() / denom;
                    (m, e.sqrt())
                }
            }
            _ => (0.0, 0.0),
        };

        let anchors = self.sample_24(&clean_metrics);
        let mut next = [0.0_f64; 24];

        let topo_gain = ((self.nx * self.ny).max(1) as f64).ln().max(1.0) / 10.0;
        let field_gain = (self.n_fields.max(1) as f64).ln().max(1.0) / 8.0;
        let seed_phase = (self.seed as f64 * 0.0001) % (2.0 * PI);

        for i in 0..24 {
            let prev = self.state_vec[i];
            let target = (anchors[i] - mean) / scale;

            let left = self.state_vec[(i + 23) % 24];
            let right = self.state_vec[(i + 1) % 24];
            let coupling = 0.5 * (left + right) - prev;

            let p = (self.tick as f64) * 0.03 + (i as f64) * 0.17 + seed_phase;
            let resonance = (p.sin() * (0.6 + 0.4 * p.cos())).clamp(-1.0, 1.0);
            let symbolic = (emb_mean.tanh() * 0.2) + (emb_energy.tanh() * 0.1);

            let delta = 0.18 * (target.tanh() - prev)
                + 0.12 * coupling
                + 0.04 * resonance
                + 0.03 * symbolic
                + 0.02 * topo_gain
                + 0.01 * field_gain;

            next[i] = (prev + delta).clamp(-1.0, 1.0);
        }

        self.state_vec = next;
        self.tick = self.tick.wrapping_add(1);

        let innovation = self
            .state_vec
            .iter()
            .zip(anchors.iter())
            .map(|(s, a)| {
                let t = ((a - mean) / scale).tanh();
                (s - t).abs()
            })
            .sum::<f64>()
            / 24.0;

        let spread = self.state_vec.iter().map(|v| v.abs()).sum::<f64>() / 24.0;
        let volatility = (std / (mean_abs + 1e-6)).tanh().abs();
        let drift_score = (0.50 * innovation + 0.30 * volatility + 0.20 * spread).clamp(0.0, 1.0);

        let euler_chi = (2.0 - (drift_score * 2.0)).clamp(-2.0, 2.0);
        let genus = ((2.0 - euler_chi) / 2.0).clamp(0.0, 2.0);
        let beta0 = if drift_score < 0.66 { 1.0 } else { 2.0 };
        let beta1 = ((drift_score * 3.0).round()).clamp(0.0, 3.0);

        EngineOutput {
            stabilized_vector: self.state_vec.to_vec(),
            drift_score,
            euler_chi,
            genus,
            beta0,
            beta1,
        }
    }

    fn sample_24(&self, values: &[f64]) -> [f64; 24] {
        let mut out = [0.0_f64; 24];
        if values.is_empty() {
            return out;
        }

        if values.len() == 1 {
            out.fill(values[0]);
            return out;
        }

        let last = (values.len() - 1) as f64;
        for i in 0..24 {
            let pos = (i as f64) * last / 23.0;
            let lo = pos.floor() as usize;
            let hi = pos.ceil() as usize;
            if lo == hi {
                out[i] = values[lo];
            } else {
                let w = pos - (lo as f64);
                out[i] = values[lo] * (1.0 - w) + values[hi] * w;
            }
        }
        out
    }
}

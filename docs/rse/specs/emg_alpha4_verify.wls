(* Symbolic verification: an exponential PBF forces alpha = 4 (thin screen) *)
(* Conventions follow burstfit.py:gaussian_powerlaw_convolution and turbulence.py *)

alphaOf[b_] := 2 b/(b - 2);

report[name_, val_] := Print[name, ": ", val];

(* 1. Closure values *)
report["closure_beta4_gives_alpha4", alphaOf[4] == 4];
report["closure_kolmogorov_gives_22over5", alphaOf[11/3] == 22/5];

(* 2. Crossover s_c = 2 ln(2/(4-b)) diverges as b -> 4- *)
sc[b_] := 2 Log[2/(4 - b)];
report["sc_diverges_at_beta4", Limit[sc[b], b -> 4, Direction -> "FromBelow"] === Infinity];

(* 3. PBF tail mass: p(s) = e^-s (s<=sc), e^-sc (s/sc)^(-b/2) (s>sc) *)
tailMass[b_] = Integrate[Exp[-sc[b]] (s/sc[b])^(-b/2), {s, sc[b], Infinity},
   Assumptions -> 2 < b < 4];
report["tailmass_closed_form", Simplify[tailMass[b] - Exp[-sc[b]] sc[b]/(b/2 - 1), Assumptions -> 2 < b < 4] === 0];
report["tailmass_positive_beta3", Simplify[tailMass[3] > 0]];
report["tailmass_to_zero_at_beta4", Limit[tailMass[b], b -> 4, Direction -> "FromBelow"] === 0];

(* 3b. Normalizability vs mean delay: integral s^(-b/2) converges for b>2;
       first moment s^(1-b/2) converges only for b>4 *)
norm = Integrate[s^(-b/2), {s, 1, Infinity}, GenerateConditions -> True];
mean = Integrate[s^(1 - b/2), {s, 1, Infinity}, GenerateConditions -> True];
report["norm_condition", norm];
report["mean_condition", mean];

(* 4. Frequency-scaling exponent from D_phi = CC nu^-2 rho^(b-2):
      rho_d from D_phi==1; theta_d ~ 1/(k rho_d), k ~ nu; tau ~ theta_d^2 *)
rhod = (nu^2/CC)^(1/(b - 2));
thetad = 1/(k0 nu rhod);
tauExp = Exponent[PowerExpand[thetad^2 /. {CC -> 1, k0 -> 1}], nu];
report["tau_exponent_equals_minus_alpha", Simplify[tauExp == -alphaOf[b]]];
report["tau_exponent_at_beta4", (tauExp /. b -> 4) == -4];

(* 5. EMG identity: Gaussian(mu,sig) conv one-sided Exp(tau) equals the
      closed forms (erfc and the erfcx form used in burstfit.py) *)
assum = sig > 0 && tau > 0 && Element[{t, mu}, Reals];
conv = Integrate[
   1/(Sqrt[2 Pi] sig) Exp[-(t - u - mu)^2/(2 sig^2)] 1/tau Exp[-u/tau],
   {u, 0, Infinity}, Assumptions -> assum];
emgErfc = 1/(2 tau) Exp[sig^2/(2 tau^2) - (t - mu)/tau] Erfc[(sig/tau - (t - mu)/sig)/Sqrt[2]];
bb = sig/(Sqrt[2] tau) - (t - mu)/(Sqrt[2] sig);
emgErfcx = 1/(2 tau) Exp[-(t - mu)^2/(2 sig^2)] Exp[bb^2] Erfc[bb];
report["emg_conv_equals_erfc_form", FullSimplify[conv - emgErfc, assum] === 0];
report["emg_erfcx_form_equals_erfc_form", FullSimplify[emgErfcx - emgErfc, assum] === 0];

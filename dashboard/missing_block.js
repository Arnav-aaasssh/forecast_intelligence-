  document.getElementById('dash-title').textContent   = meta.title || payload.metadata?.title || '';
  document.getElementById('dash-period').textContent  = 'Evaluation Period: ' + (meta.evaluation_period || '');
  document.getElementById('dash-records').textContent = (meta.records_evaluated||0).toLocaleString();
  document.getElementById('dash-models').textContent  = meta.models_evaluated || '';
  document.getElementById('evidence-banner-text').textContent =
    `${meta.n_realized_weeks||0} of ${meta.n_total_weeks||0} forecast weeks have realized actuals (${meta.realized_window||''}). The remaining ${(meta.n_total_weeks||0)-(meta.n_realized_weeks||0)} weeks are forecast projections, not yet evaluable.`;

  // ── EXECUTIVE DECISION COCKPIT ──────────────────────────
  const confLvl = sa.confidence;
  const winner  = sa.manual_wins > sa.ml_wins ? 'Manual' : (sa.ml_wins > sa.manual_wins ? 'ML' : 'Tied');
  const decision = confLvl === 'Inconclusive'
    ? 'Retain Current Approach — Evidence Inconclusive'
    : `Favour ${winner} Forecast`;
  document.getElementById('exec-decision').textContent = decision;
  document.getElementById('exec-conf-chip').innerHTML  = chip(confLvl);

  const pct = Math.round(((meta.n_realized_weeks||0)/(meta.n_total_weeks||99))*100);
  document.getElementById('exec-ev-window').textContent = `${meta.n_realized_weeks||0} / ${meta.n_total_weeks||99} weeks`;
  document.getElementById('exec-ev-bar').style.width   = pct + '%';
  document.getElementById('exec-ev-sub').textContent   = `${pct}% of forecast horizon realized`;
  if(document.getElementById('exec-total-weeks')) document.getElementById('exec-total-weeks').textContent = meta.n_total_weeks||99;

  document.getElementById('exec-kpi-weeks').textContent     = meta.n_realized_weeks || 0;
  document.getElementById('exec-kpi-sa').textContent        = `${sa.manual_wins}–${sa.ml_wins}`;
  document.getElementById('exec-kpi-sa-chip').innerHTML     = chip(confLvl);
  document.getElementById('exec-kpi-champ').textContent     = champ ? champ.Model : '—';
  document.getElementById('exec-kpi-champ-score').textContent = champ ? `Score: ${champ.CompositeScore}/100` : '';
  document.getElementById('exec-kpi-below').textContent     = bc.overall_share_below + '%';

  // Q1-Q4 Status strip
  document.getElementById('ss-q1-val').textContent = `Manual ${sa.manual_wins}–ML ${sa.ml_wins} · ${confLvl}`;
  const isMlLeading = sa.ml_wins > sa.manual_wins;
  const conclusionText = isMlLeading 
    ? 'The AI-driven models demonstrate a consistent edge over manual adjustments.'
    : (sa.manual_wins > sa.ml_wins ? 'Manual adjustments demonstrate a consistent edge over the AI-driven models.' : 'Manual and AI models are currently tied in performance.');

  document.getElementById('exec-summary-text').innerHTML = `
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 16px;">
      
      <!-- Card 1 -->
      <div class="exec-card" onclick="nav('page-sa')">
        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-2); font-weight: 600; margin-bottom: 6px;">Operational Recommendation</div>
        <div style="font-size: 14px; font-weight: 600; color: var(--navy); margin-bottom: 4px;">${isMlLeading ? 'Deploy ML Forecast' : 'Maintain Manual Forecast'}</div>
        <div style="font-size: 12.5px; color: var(--text-1); line-height: 1.5; padding-right: 12px;">${conclusionText}</div>
      </div>

      <!-- Card 2 -->
      <div class="exec-card" onclick="nav('page-sa')">
        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text-2); font-weight: 600; margin-bottom: 6px;">Head-to-Head Performance</div>
        <div style="font-size: 14px; font-weight: 600; color: var(--navy); margin-bottom: 4px;">${sa.ml_wins} Wins vs ${sa.manual_wins} Wins</div>

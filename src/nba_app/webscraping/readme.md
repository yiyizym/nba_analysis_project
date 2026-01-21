<style>
  body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f4f4f4;
  }
  h1 {
    color: #2c3e50;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
  }
  h2 {
    color: #2980b9;
    margin-top: 30px;
  }
  .step {
    background-color: #fff;
    border-left: 4px solid #3498db;
    margin-bottom: 20px;
    padding: 15px;
    border-radius: 0 5px 5px 0;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  }
  .loop {
    margin-left: 20px;
    border-left: 2px dashed #95a5a6;
    padding-left: 20px;
  }
  .nested-loop {
    margin-left: 20px;
    border-left: 2px dotted #bdc3c7;
    padding-left: 20px;
  }
  .sub-step {
    margin: 10px 0;
  }
  .highlight {
    background-color: #e74c3c;
    color: white;
    padding: 2px 5px;
    border-radius: 3px;
  }
</style>

<h1>Data Scraping and Processing Workflow</h1>

<div class="step">
  <h2>1. Initialization</h2>
  <p>Determine which date to start scraping from</p>
</div>

<div class="step">
  <h2>2. Scrape Boxscores</h2>
  <div class="loop">
    <p><strong>For each</strong> stat_type in stat_types:</p>
    <div class="nested-loop">
      <p><strong>For each</strong> season in seasons:</p>
      <div class="nested-loop">
        <p><strong>For each</strong> sub_season in sub_seasons:</p>
        <div class="sub-step">
          <ul>
            <li>Construct URL with dates, stat_type, sub_season</li>
            <li>Go to URL</li>
            <li>Scrape data table</li>
            <li>Convert to dataframe</li>
            <li>Concat dataframe with previous sub_seasons dataframes</li>
          </ul>
        </div>
      </div>
      <p>Concat dataframe with previous seasons dataframes</p>
    </div>
    <p>Save dataframe to CSV</p>
  </div>
</div>

<div class="step">
  <h2>3. Scrape Schedule</h2>
  <ul>
    <li>Go to URL</li>
    <li>Find games for today</li>
    <li>Scrape game IDs and matchup team IDs</li>
    <li>Save game IDs to CSV</li>
    <li>Save matchups to CSV</li>
  </ul>
</div>

<div class="step">
  <h2>4. Data Validation and Integration</h2>
  <ul>
    <li>Validate the newly scraped data for consistency</li>
    <li>Concat the newly scraped data with previously saved cumulative data and save to CSVs</li>
    <li>Validate the new cumulative data for consistency</li>
  </ul>
</div>

<div class="step">
  <h2>5. <span class="highlight">Process Complete</span></h2>
</div>

<h1>TeamStatsScraper - Team Statistics Scraping</h1>

<div class="step">
  <h2>Overview</h2>
  <p>Generic scraper for all NBA team statistics categories from the official NBA stats website. Supports 50+ stat categories.</p>
  <p><strong>URL pattern:</strong> <code>https://www.nba.com/stats/teams/{category}?SeasonType={season_type}&Season={season}</code></p>
</div>

<div class="step">
  <h2>Supported Categories (8 Groups)</h2>
  <ul>
    <li><strong>Traditional Stats:</strong> traditional, advanced, four-factors, misc, scoring, opponent, defense, estimated-advanced</li>
    <li><strong>Clutch Stats:</strong> clutch-traditional, clutch-advanced, clutch-four-factors, clutch-misc, clutch-scoring, clutch-opponent</li>
    <li><strong>Playtype Stats:</strong> isolation, transition, ball-handler, roll-man, post-up, spot-up, hand-off, cut, off-screen, putbacks</li>
    <li><strong>Tracking Stats:</strong> drives, defensive-impact, catch-shoot, passing, touches, pull-up, rebounding, speed-distance, elbow-touches, post-touches, paint-touches</li>
    <li><strong>Defense Dashboard:</strong> defense-dash-overall, defense-dash-3pt, defense-dash-2pt, defense-dash-lt6, defense-dash-lt10, defense-dash-gt15</li>
    <li><strong>Shot Dashboard:</strong> shots-general, shots-shotclock, shots-dribbles, shots-touch-time, shots-closest-defender, shots-closest-defender-10</li>
    <li><strong>Shooting Stats:</strong> shooting (supports DistanceRange: By+Zone, 5ft+Range, 8ft+Range), opponent-shooting</li>
    <li><strong>Hustle Stats:</strong> hustle, box-outs</li>
  </ul>
</div>

<div class="step">
  <h2>Configuration</h2>
  <pre>
# configs/nba/webscraping_config.yaml
enable_team_stats_scraping: True

# Multi-category mode (recommended)
team_stats_categories:
  traditional_stats:
    enabled: true
  shooting_stats:
    enabled: true
  # ...

# Or single-category mode (backwards compatible)
team_stats_category: shooting
  </pre>
</div>

<div class="step">
  <h2>Usage</h2>
  <pre>
# Run full scraping
python -m src.nba_app.webscraping.main

# Run test script (1 season only)
uv run python scripts/test_team_stats_scraper.py
  </pre>
</div>

<div class="step">
  <h2>Key Features</h2>
  <ul>
    <li><strong>Config-driven:</strong> Define categories in YAML, enable/disable independently</li>
    <li><strong>Extra parameters:</strong> Support for parameters like <code>DistanceRange=By+Zone</code></li>
    <li><strong>Backwards compatible:</strong> <code>TeamStatsShootingScraper</code> alias preserved</li>
    <li><strong>Independent output:</strong> Files like <code>team_stats_traditional.csv</code>, <code>team_stats_shooting_by_zone.csv</code></li>
    <li><strong>Multi-level header handling:</strong> Automatically merges two-row headers into clean column names</li>
    <li><strong>Team ID extraction:</strong> Extracts team IDs from table links</li>
  </ul>
</div>
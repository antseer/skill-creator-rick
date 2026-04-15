#!/usr/bin/env node
/**
 * validate-ai-output.js
 * 
 * 校验 L3 LLM 输出是否符合规范。
 * 用法: node validate-ai-output.js [path-to-output.json]
 * 默认读取 ../sample-templates/ai-output.json
 */

const fs = require('fs');
const path = require('path');

const inputPath = process.argv[2] || path.join(__dirname, '..', 'sample-templates', 'ai-output.json');

let data;
try {
  const raw = fs.readFileSync(inputPath, 'utf-8');
  data = JSON.parse(raw);
} catch (e) {
  console.error(`🔴 FAIL: Cannot parse JSON — ${e.message}`);
  process.exit(1);
}

const issues = [];

// Check 1: headline exists and ≤ 40 chars
if (!data.headline) {
  issues.push('🔴 headline is missing');
} else if (data.headline.length > 40) {
  issues.push(`🔴 headline too long: ${data.headline.length} chars (max 40)`);
}

// Check 2: top1_reason exists and 80-120 chars
if (!data.top1_reason) {
  issues.push('🔴 top1_reason is missing');
} else {
  const len = data.top1_reason.length;
  if (len < 80) issues.push(`🟡 top1_reason too short: ${len} chars (min 80)`);
  if (len > 200) issues.push(`🟡 top1_reason too long: ${len} chars (target 80-120)`);
}

// Check 3: opportunity_cost contains dollar sign
if (!data.opportunity_cost) {
  issues.push('🔴 opportunity_cost is missing');
} else if (!data.opportunity_cost.includes('$')) {
  issues.push('🔴 opportunity_cost does not contain $ (dollar amounts required)');
}

// Check 4: risk_warning ≥ 40 chars
if (!data.risk_warning) {
  issues.push('🔴 risk_warning is missing');
} else if (data.risk_warning.length < 40) {
  issues.push(`🔴 risk_warning too short: ${data.risk_warning.length} chars (min 40)`);
}

// Check 5: anomaly_narratives is array
if (!Array.isArray(data.anomaly_narratives)) {
  issues.push('🔴 anomaly_narratives is not an array');
}

// Check 6: brief_for_card structure
if (!Array.isArray(data.brief_for_card)) {
  issues.push('🔴 brief_for_card is not an array');
} else {
  data.brief_for_card.forEach((item, i) => {
    if (typeof item.rank !== 'number') {
      issues.push(`🔴 brief_for_card[${i}].rank is not a number`);
    }
    if (!item.one_liner || typeof item.one_liner !== 'string') {
      issues.push(`🔴 brief_for_card[${i}].one_liner is missing or not a string`);
    } else if (item.one_liner.length > 80) {
      issues.push(`🟡 brief_for_card[${i}].one_liner too long: ${item.one_liner.length} chars`);
    }
  });
}

// Check 7: No forbidden phrases
const forbidden = ['我认为', '我觉得', '我建议', '请注意', '值得一提'];
const allText = JSON.stringify(data);
forbidden.forEach(phrase => {
  if (allText.includes(phrase)) {
    issues.push(`🔴 Contains forbidden phrase: "${phrase}"`);
  }
});

// Check 8: No markdown
if (allText.includes('```') || allText.includes('**')) {
  issues.push('🟡 Contains markdown formatting (``` or **)');
}

// Report
console.log(`\n=== AI Output Validation ===`);
console.log(`File: ${inputPath}\n`);

if (issues.length === 0) {
  console.log('✅ ALL CHECKS PASSED\n');
  process.exit(0);
} else {
  const critical = issues.filter(i => i.startsWith('🔴'));
  const warnings = issues.filter(i => i.startsWith('🟡'));
  
  issues.forEach(i => console.log(`  ${i}`));
  console.log(`\n  Total: ${critical.length} critical, ${warnings.length} warnings`);
  
  if (critical.length > 0) {
    console.log('\n❌ VALIDATION FAILED\n');
    process.exit(1);
  } else {
    console.log('\n⚠️ PASSED WITH WARNINGS\n');
    process.exit(0);
  }
}

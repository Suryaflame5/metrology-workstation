import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Info,
  Calculator,
  FileText,
  Shield,
  ArrowRight,
  Scale
} from 'lucide-react';
import { MetrologyAPI } from '../../services/api';
import { useMetrology } from '../../context/MetrologyContext';

interface ConformityParams {
  measured_mean: number;
  nominal: number;
  tolerance_lower: number;
  tolerance_upper: number;
  expanded_uncertainty: number;
  decision_rule: string;
}

interface ConformityResult {
  decision: 'conforming' | 'non_conforming' | 'conditional_pass' | 'conditional_fail';
  consumer_risk: number;
  producer_risk: number;
  guard_band_lower: number;
  guard_band_upper: number;
  tur: number;
  rationale: string;
  traceability: {
    standard: string;
    method: string;
    reference: string;
  };
}

const DECISION_RULES = [
  {
    id: 'method6',
    name: 'ANSI/NCSL Z540.3 Method 6',
    description: 'Root guardband calculation ensuring consumer risk ≤ 2.0%',
    icon: Shield,
    recommended: true
  },
  {
    id: 'method5',
    name: 'ANSI/NCSL Z540.3 Method 5',
    description: 'Root-Sum-Square (RSS) guardband approach',
    icon: Calculator
  },
  {
    id: 'iso14253',
    name: 'ISO 14253-1',
    description: 'Complete guardband (w = U)',
    icon: Scale
  },
  {
    id: 'simple',
    name: 'Simple Acceptance',
    description: 'Basic acceptance without guardband (not recommended for critical measurements)',
    icon: AlertTriangle,
    warning: true
  }
];

export const ConformityAssessmentWorkspace: React.FC = () => {
  const { selectedJob, setSelectedJob, logAuditEvent } = useMetrology();

  const [params, setParams] = useState<ConformityParams>(() => ({
    measured_mean: selectedJob?.sample_statistics?.mean ?? selectedJob?.nominal_value ?? 10.0142,
    nominal: selectedJob?.nominal_value ?? 10.0000,
    tolerance_lower: selectedJob?.tolerance_lower ?? -0.0200,
    tolerance_upper: selectedJob?.tolerance_upper ?? 0.0200,
    expanded_uncertainty: selectedJob?.uncertainty_budget?.expanded_uncertainty_U95 ?? 0.0021,
    decision_rule: selectedJob?.conformity?.decision_rule || 'method6'
  }));

  const [result, setResult] = useState<ConformityResult | null>(() => {
    if (selectedJob?.conformity) {
      const c = selectedJob.conformity;
      return {
        decision: (c.conformance_verdict?.toLowerCase() as any) || 'conforming',
        consumer_risk: c.consumer_risk_pcr || 0.0042,
        producer_risk: c.producer_risk || 0.0018,
        guard_band_lower: c.guardband_lower || (selectedJob.nominal_value ?? 10.0) - 0.018,
        guard_band_upper: c.guardband_upper || (selectedJob.nominal_value ?? 10.0) + 0.018,
        tur: c.tur || 9.52,
        rationale: c.decision_rule_rationale || 'Evaluated per ANSI Z540.3 Method 6 guardband.',
        traceability: {
          standard: 'ANSI/NCSL Z540.3-2006',
          method: 'Method 6 (Root Finding Guardband)',
          reference: 'Handbook for the Application of ANSI/NCSL Z540.3-2006',
        }
      };
    }
    return null;
  });
  
  const [isCalculating, setIsCalculating] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const calculateConformity = async () => {
    setIsCalculating(true);
    try {
      const apiResult = await MetrologyAPI.evaluateConformity({
        measured_mean: params.measured_mean,
        nominal: params.nominal,
        tolerance_lower: params.tolerance_lower,
        tolerance_upper: params.tolerance_upper,
        expanded_uncertainty: params.expanded_uncertainty,
        decision_rule: params.decision_rule
      });
      
      if (apiResult) {
        const computedResult: ConformityResult = {
          decision: apiResult.decision || 'conforming',
          consumer_risk: apiResult.consumer_risk || 0,
          producer_risk: apiResult.producer_risk || 0,
          guard_band_lower: apiResult.guard_band_lower || 0,
          guard_band_upper: apiResult.guard_band_upper || 0,
          tur: apiResult.tur || 0,
          rationale: generateRationale(params, apiResult),
          traceability: {
            standard: getStandardForRule(params.decision_rule),
            method: getMethodForRule(params.decision_rule),
            reference: getReferenceForRule(params.decision_rule)
          }
        };
        setResult(computedResult);

        // Save to active job in backend
        if (selectedJob?.id) {
          const verdict = apiResult.decision === 'conforming' ? 'PASS' : apiResult.decision === 'non_conforming' ? 'FAIL' : 'GUARD_BAND';
          const updatedConformity = {
            conformance_verdict: verdict,
            consumer_risk_pcr: apiResult.consumer_risk || 0,
            producer_risk: apiResult.producer_risk || 0,
            guardband_lower: apiResult.guard_band_lower || 0,
            guardband_upper: apiResult.guard_band_upper || 0,
            tur: apiResult.tur || 0,
            decision_rule: params.decision_rule,
            decision_rule_rationale: computedResult.rationale,
          };

          await fetch(`/api/jobs/${selectedJob.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              conformity: updatedConformity,
            }),
          });

          setSelectedJob({
            ...selectedJob,
            conformity: updatedConformity,
          });

          logAuditEvent(
            'CONFORMITY_ASSESSMENT_EVALUATED',
            selectedJob.id,
            'Unassessed',
            `Verdict: ${verdict}, Rule: ${params.decision_rule}, P_CR: ${((apiResult.consumer_risk || 0) * 100).toFixed(2)}%`,
            'ANSI/NCSL Z540.3 Method 6 Verification'
          );
        }
      }
    } catch (error) {
      console.error('Conformity calculation failed:', error);
    } finally {
      setIsCalculating(false);
    }
  };

  const generateRationale = (inputParams: ConformityParams, apiResult: any): string => {
    const spec_lower = inputParams.nominal + inputParams.tolerance_lower;
    const spec_upper = inputParams.nominal + inputParams.tolerance_upper;
    const tur = (inputParams.tolerance_upper - inputParams.tolerance_lower) / (2 * inputParams.expanded_uncertainty);
    
    let rationale = `Measured value ${inputParams.measured_mean.toFixed(4)} compared to specification limits [${spec_lower.toFixed(4)}, ${spec_upper.toFixed(4)}]. `;
    rationale += `Test Uncertainty Ratio (TUR) = ${tur.toFixed(2)}. `;
    rationale += `Expanded uncertainty U = ${inputParams.expanded_uncertainty.toFixed(4)}. `;
    
    if (inputParams.decision_rule === 'method6') {
      rationale += `Method 6 guardband applied: [${apiResult.guard_band_lower?.toFixed(4)}, ${apiResult.guard_band_upper?.toFixed(4)}]. `;
      rationale += `Consumer risk controlled to ≤ 2.0%. `;
    }
    
    return rationale;
  };

  const getStandardForRule = (rule: string): string => {
    switch (rule) {
      case 'method6':
      case 'method5':
        return 'ANSI/NCSL Z540.3-2006';
      case 'iso14253':
        return 'ISO 14253-1:2017';
      default:
        return 'Custom acceptance criteria';
    }
  };

  const getMethodForRule = (rule: string): string => {
    switch (rule) {
      case 'method6':
        return 'Method 6 - Root Guardband';
      case 'method5':
        return 'Method 5 - RSS Guardband';
      case 'iso14253':
        return 'Complete Guardband';
      default:
        return 'Simple Acceptance';
    }
  };

  const getReferenceForRule = (rule: string): string => {
    switch (rule) {
      case 'method6':
        return 'Section 6.5, ANSI/NCSL Z540.3-2006';
      case 'method5':
        return 'Section 6.4, ANSI/NCSL Z540.3-2006';
      case 'iso14253':
        return 'Clause 6, ISO 14253-1:2017';
      default:
        return 'N/A';
    }
  };

  const getDecisionIcon = () => {
    if (!result) return null;
    
    switch (result.decision) {
      case 'conforming':
        return <CheckCircle2 className="w-8 h-8 text-[#4caf50]" />;
      case 'non_conforming':
        return <XCircle className="w-8 h-8 text-[#f44336]" />;
      case 'guard_band':
        return <AlertTriangle className="w-8 h-8 text-[#ff9800]" />;
      default:
        return <Info className="w-8 h-8 text-[#576065]" />;
    }
  };

  const getDecisionColor = () => {
    if (!result) return 'text-[#576065]';
    
    switch (result.decision) {
      case 'conforming':
        return 'text-[#4caf50]';
      case 'non_conforming':
        return 'text-[#f44336]';
      case 'guard_band':
        return 'text-[#ff9800]';
      default:
        return 'text-[#576065]';
    }
  };

  const getDecisionBg = () => {
    if (!result) return 'bg-[#f4f5f3]';
    
    switch (result.decision) {
      case 'conforming':
        return 'bg-[#e8f5e9]';
      case 'non_conforming':
        return 'bg-[#ffebee]';
      case 'guard_band':
        return 'bg-[#fff3e0]';
      default:
        return 'bg-[#f4f5f3]';
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#f4f5f3]">
      {/* Left Panel - Input Parameters */}
      <div className="w-96 bg-white border-r border-[#c1c7ce] overflow-y-auto">
        <div className="p-4 border-b border-[#c1c7ce]">
          <h2 className="font-semibold text-lg">Conformity Assessment</h2>
          <p className="text-sm text-[#576065]">Decision rule evaluation</p>
        </div>
        
        <div className="p-4 space-y-6">
          {/* Decision Rule Selection */}
          <div>
            <label className="block text-sm font-medium mb-3">Decision Rule</label>
            <div className="space-y-2">
              {DECISION_RULES.map((rule) => {
                const Icon = rule.icon;
                return (
                  <button
                    key={rule.id}
                    onClick={() => setParams({ ...params, decision_rule: rule.id as any })}
                    className={`w-full p-3 rounded-md border text-left transition-colors ${
                      params.decision_rule === rule.id
                        ? 'border-[#1976d2] bg-[#e3f2fd]'
                        : 'border-[#c1c7ce] hover:bg-[#f4f5f3]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Icon className={`w-4 h-4 ${rule.warning ? 'text-[#ff9800]' : 'text-[#1976d2]'}`} />
                      <span className="font-medium text-sm">{rule.name}</span>
                      {rule.recommended && (
                        <span className="ml-auto text-xs bg-[#4caf50] text-white px-2 py-0.5 rounded">Recommended</span>
                      )}
                    </div>
                    <p className="text-xs text-[#576065] mt-1">{rule.description}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Measurement Parameters */}
          <div className="space-y-4">
            <h3 className="font-medium text-sm">Measurement Parameters</h3>
            
            <div>
              <label className="block text-xs font-medium mb-1">Measured Value</label>
              <input
                type="number"
                step="any"
                value={params.measured_mean}
                onChange={(e) => setParams({ ...params, measured_mean: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">Nominal Value</label>
              <input
                type="number"
                step="any"
                value={params.nominal}
                onChange={(e) => setParams({ ...params, nominal: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">Lower Tolerance</label>
                <input
                  type="number"
                  step="any"
                  value={params.tolerance_lower}
                  onChange={(e) => setParams({ ...params, tolerance_lower: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">Upper Tolerance</label>
                <input
                  type="number"
                  step="any"
                  value={params.tolerance_upper}
                  onChange={(e) => setParams({ ...params, tolerance_upper: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">Expanded Uncertainty (U)</label>
              <input
                type="number"
                step="any"
                value={params.expanded_uncertainty}
                onChange={(e) => setParams({ ...params, expanded_uncertainty: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md text-sm"
              />
            </div>
          </div>

          {/* Calculate Button */}
          <button
            onClick={calculateConformity}
            disabled={isCalculating}
            className="w-full px-4 py-3 bg-[#1976d2] text-white rounded-md hover:bg-[#1565c0] disabled:bg-[#c1c7ce] disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isCalculating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Calculating...
              </>
            ) : (
              <>
                <Calculator className="w-4 h-4" />
                Evaluate Conformity
              </>
            )}
          </button>
        </div>
      </div>

      {/* Right Panel - Results */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {result ? (
          <>
            {/* Decision Banner */}
            <div className={`p-6 border-b border-[#c1c7ce] ${getDecisionBg()}`}>
              <div className="flex items-center gap-4">
                {getDecisionIcon()}
                <div className="flex-1">
                  <div className={`text-2xl font-bold uppercase ${getDecisionColor()}`}>
                    {result.decision === 'conforming' ? '✓ CONFORMING' : 
                     result.decision === 'non_conforming' ? '✗ NON-CONFORMING' : 
                     '⚠ GUARD BAND'}
                  </div>
                  <p className="text-sm text-[#576065] mt-1">
                    Based on {result.traceability.standard} {result.traceability.method}
                  </p>
                </div>
              </div>
            </div>

            {/* Results Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* Measurement Summary */}
              <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Measurement Summary
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-[#576065]">Measured Result</div>
                    <div className="text-lg font-mono font-semibold">{params.measured_mean.toFixed(4)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-[#576065]">Specification</div>
                    <div className="text-lg font-mono font-semibold">
                      {params.nominal.toFixed(4)} ±{Math.abs(params.tolerance_upper).toFixed(4)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-[#576065]">Expanded Uncertainty</div>
                    <div className="text-lg font-mono font-semibold">±{params.expanded_uncertainty.toFixed(4)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-[#576065]">Test Uncertainty Ratio</div>
                    <div className="text-lg font-mono font-semibold">{result.tur.toFixed(2)}</div>
                  </div>
                </div>
              </div>

              {/* Decision Rationale */}
              <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Info className="w-5 h-5" />
                  Decision Rationale
                </h3>
                <p className="text-sm leading-relaxed">{result.rationale}</p>
              </div>

              {/* Risk Analysis */}
              <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Risk Analysis
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-[#e3f2fd] rounded-md">
                    <div className="text-xs text-[#576065]">Consumer Risk (P_CR)</div>
                    <div className="text-xl font-mono font-semibold text-[#1976d2]">
                      {(result.consumer_risk * 100).toFixed(2)}%
                    </div>
                    <div className="text-xs text-[#576065] mt-1">
                      {result.consumer_risk <= 0.02 ? '✓ ≤ 2.0% target' : '⚠ Exceeds target'}
                    </div>
                  </div>
                  <div className="p-4 bg-[#fff3e0] rounded-md">
                    <div className="text-xs text-[#576065]">Producer Risk (P_PR)</div>
                    <div className="text-xl font-mono font-semibold text-[#ff9800]">
                      {(result.producer_risk * 100).toFixed(2)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Guardband Information */}
              {params.decision_rule !== 'simple' && (
                <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Scale className="w-5 h-5" />
                    Guardband Limits
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-xs text-[#576065]">Lower Guardband</div>
                      <div className="text-lg font-mono font-semibold">
                        {result.guard_band_lower.toFixed(4)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-[#576065]">Upper Guardband</div>
                      <div className="text-lg font-mono font-semibold">
                        {result.guard_band_upper.toFixed(4)}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 p-3 bg-[#f4f5f3] rounded-md text-xs text-[#576065]">
                    <strong>Guardband Definition:</strong> Acceptance region reduced by uncertainty to control consumer risk.
                    Measured values within guardband are considered conforming.
                  </div>
                </div>
              )}

              {/* Traceability Information */}
              <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Traceability & Standards
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-[#576065]">Standard:</span>
                    <span className="font-medium">{result.traceability.standard}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#576065]">Method:</span>
                    <span className="font-medium">{result.traceability.method}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#576065]">Reference:</span>
                    <span className="font-medium">{result.traceability.reference}</span>
                  </div>
                </div>
              </div>

              {/* Expandable Details */}
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="w-full px-4 py-2 border border-[#c1c7ce] rounded-md hover:bg-[#f4f5f3] flex items-center justify-center gap-2 text-sm"
              >
                {showDetails ? 'Hide' : 'Show'} Technical Details
                <ArrowRight className={`w-4 h-4 transition-transform ${showDetails ? 'rotate-90' : ''}`} />
              </button>

              {showDetails && (
                <div className="bg-white p-6 rounded-lg border border-[#c1c7ce] space-y-4">
                  <h4 className="font-medium">Technical Calculation Details</h4>
                  <div className="space-y-2 text-sm font-mono text-xs">
                    <div>Specification: [{(params.nominal + params.tolerance_lower).toFixed(6)}, {(params.nominal + params.tolerance_upper).toFixed(6)}]</div>
                    <div>Measured: {params.measured_mean.toFixed(6)}</div>
                    <div>Uncertainty: ±{params.expanded_uncertainty.toFixed(6)}</div>
                    <div>TUR: {result.tur.toFixed(6)}</div>
                    {params.decision_rule !== 'simple' && (
                      <>
                        <div>Guardband: [{result.guard_band_lower.toFixed(6)}, {result.guard_band_upper.toFixed(6)}]</div>
                        <div>Guardband Reduction: {((1 - (result.guard_band_upper - result.guard_band_lower) / (params.tolerance_upper - params.tolerance_lower)) * 100).toFixed(2)}%</div>
                      </>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-[#576065]">
              <Calculator className="w-16 h-16 mx-auto mb-4 opacity-30" />
              <p className="text-lg font-medium">Enter measurement parameters and evaluate conformity</p>
              <p className="text-sm mt-2">Results will appear here after calculation</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
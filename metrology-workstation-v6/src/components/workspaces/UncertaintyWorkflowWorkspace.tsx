import React, { useState } from 'react';
import { 
  Plus, 
  ChevronRight, 
  Calculator, 
  CheckCircle2, 
  AlertCircle,
  Info,
  ArrowRight,
  ChevronDown
} from 'lucide-react';
import { MetrologyAPI } from '../../services/api';
import { useMetrology } from '../../context/MetrologyContext';

interface UncertaintyComponent {
  id: string;
  name: string;
  value: number;
  uncertainty: number;
  distribution: 'normal' | 'rectangular' | 'triangular' | 'u-shaped';
  degrees_of_freedom?: number;
  sensitivity_coefficient?: number;
  contribution?: number;
}

interface WorkflowStep {
  id: number;
  title: string;
  description: string;
  status: 'pending' | 'active' | 'completed';
}

const WORFLOW_STEPS: WorkflowStep[] = [
  {
    id: 1,
    title: 'Create Measurement Model',
    description: 'Define the mathematical relationship between input quantities and the measurand',
    status: 'pending'
  },
  {
    id: 2,
    title: 'Add Input Quantities',
    description: 'Identify and add all uncertainty sources affecting the measurement',
    status: 'pending'
  },
  {
    id: 3,
    title: 'Select Distributions',
    description: 'Choose appropriate probability distributions for each uncertainty source',
    status: 'pending'
  },
  {
    id: 4,
    title: 'Enter Uncertainty Values',
    description: 'Input standard uncertainty values for each component',
    status: 'pending'
  },
  {
    id: 5,
    title: 'Calculate Sensitivity Coefficients',
    description: 'Determine how each input quantity affects the final result',
    status: 'pending'
  },
  {
    id: 6,
    title: 'Compute Combined Uncertainty',
    description: 'Combine all uncertainty components using the law of propagation of uncertainty',
    status: 'pending'
  },
  {
    id: 7,
    title: 'Determine Expanded Uncertainty',
    description: 'Apply coverage factor (k) based on effective degrees of freedom',
    status: 'pending'
  },
  {
    id: 8,
    title: 'Review Contributions',
    description: 'Analyze which uncertainty sources contribute most to the final result',
    status: 'pending'
  }
];

export const UncertaintyWorkflowWorkspace: React.FC = () => {
  const { selectedJob, setSelectedJob, logAuditEvent } = useMetrology();

  const [currentStep, setCurrentStep] = useState(1);
  const [components, setComponents] = useState<UncertaintyComponent[]>(() => {
    if (selectedJob?.uncertainty_budget?.components?.length) {
      return selectedJob.uncertainty_budget.components.map((c: any, i: number) => ({
        id: `comp-${i + 1}`,
        name: c.name || c.source || `Component ${i + 1}`,
        value: c.value ?? c.estimate ?? selectedJob.nominal_value ?? 0,
        uncertainty: c.std_uncertainty ?? c.standard_uncertainty ?? 0.0001,
        distribution: (c.distribution?.toLowerCase() as any) || 'normal',
        degrees_of_freedom: c.degrees_of_freedom ?? Infinity,
        sensitivity_coefficient: c.sensitivity_coefficient ?? 1.0,
        contribution: c.percentage_contribution ?? 0,
      }));
    }
    return [
      { id: 'comp-1', name: 'Repeatability (Type A)', value: selectedJob?.nominal_value || 10.0, uncertainty: 0.00015, distribution: 'normal', degrees_of_freedom: 9, sensitivity_coefficient: 1, contribution: 0 },
      { id: 'comp-2', name: 'Reference Standard Calibration', value: 0, uncertainty: 0.00008, distribution: 'normal', degrees_of_freedom: Infinity, sensitivity_coefficient: 1, contribution: 0 },
      { id: 'comp-3', name: 'Digital Resolution', value: 0, uncertainty: 0.00005, distribution: 'rectangular', degrees_of_freedom: Infinity, sensitivity_coefficient: 1, contribution: 0 },
      { id: 'comp-4', name: 'Thermal CTE Drift', value: 0, uncertainty: 0.00004, distribution: 'triangular', degrees_of_freedom: Infinity, sensitivity_coefficient: 1, contribution: 0 },
    ];
  });

  const [modelName, setModelName] = useState(selectedJob?.title || 'Precision Calibration GUM Model');
  const [measurandFormula, setMeasurandFormula] = useState(
    `${selectedJob?.unit || 'V'}_meas = ${selectedJob?.unit || 'V'}_ref + δ${selectedJob?.unit || 'V'}_res + α·(T - T_0) + δ${selectedJob?.unit || 'V'}_drift + s_p`
  );
  const [confidenceLevel, setConfidenceLevel] = useState(0.9545);
  const [calculationResult, setCalculationResult] = useState<any>(selectedJob?.uncertainty_budget || null);
  const [isCalculating, setIsCalculating] = useState(false);

  const addComponent = () => {
    const newComponent: UncertaintyComponent = {
      id: `comp-${Date.now()}`,
      name: `Component ${components.length + 1}`,
      value: 0,
      uncertainty: 0.0001,
      distribution: 'normal',
      degrees_of_freedom: Infinity,
      sensitivity_coefficient: 1,
      contribution: 0
    };
    setComponents([...components, newComponent]);
  };

  const updateComponent = (id: string, field: keyof UncertaintyComponent, value: any) => {
    setComponents(components.map(comp => 
      comp.id === id ? { ...comp, [field]: value } : comp
    ));
  };

  const removeComponent = (id: string) => {
    setComponents(components.filter(comp => comp.id !== id));
  };

  const calculateUncertainty = async () => {
    setIsCalculating(true);
    try {
      const result = await MetrologyAPI.evaluateUncertainty(
        components.map(comp => ({
          name: comp.name,
          value: comp.value,
          uncertainty: comp.uncertainty,
          distribution: comp.distribution,
          degrees_of_freedom: comp.degrees_of_freedom,
          sensitivity_coefficient: comp.sensitivity_coefficient
        })),
        confidenceLevel
      );
      
      if (result) {
        setCalculationResult(result);
        // Update components with calculated contributions
        if (result.component_contributions) {
          setComponents(components.map((comp, index) => ({
            ...comp,
            contribution: result.component_contributions[index] || 0
          })));
        }

        // Save to active job in backend if present
        if (selectedJob?.id) {
          const updatedBudget = {
            combined_uncertainty_uc: result.combined_uncertainty_uc || result.combined_standard_uncertainty,
            expanded_uncertainty_U95: result.expanded_uncertainty_U95 || result.expanded_uncertainty,
            coverage_factor_k: result.coverage_factor_k || result.coverage_factor || 2.0,
            effective_degrees_of_freedom: result.effective_degrees_of_freedom || result.effective_dof || 50,
            components: components.map((comp, idx) => ({
              source: comp.name,
              name: comp.name,
              value: comp.value,
              std_uncertainty: comp.uncertainty,
              distribution: comp.distribution,
              degrees_of_freedom: comp.degrees_of_freedom,
              sensitivity_coefficient: comp.sensitivity_coefficient,
              percentage_contribution: result.component_contributions ? result.component_contributions[idx] : 0,
            })),
          };

          await fetch(`/api/jobs/${selectedJob.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              uncertainty_budget: updatedBudget,
            }),
          });

          setSelectedJob({
            ...selectedJob,
            uncertainty_budget: updatedBudget,
          });

          logAuditEvent(
            'UNCERTAINTY_BUDGET_UPDATED',
            selectedJob.id,
            'Previous Budget',
            `Uc=${updatedBudget.combined_uncertainty_uc}, U95=${updatedBudget.expanded_uncertainty_U95}`,
            'Calculated via 50-digit high-precision GUM engine'
          );
        }
      }
    } catch (error) {
      console.error('Calculation failed:', error);
    } finally {
      setIsCalculating(false);
    }
  };

  const nextStep = () => {
    if (currentStep < WORFLOW_STEPS.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const getStepStatus = (stepId: number): 'pending' | 'active' | 'completed' => {
    if (stepId < currentStep) return 'completed';
    if (stepId === currentStep) return 'active';
    return 'pending';
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Calculator className="w-5 h-5" />
                Measurement Model Definition
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Model Name</label>
                  <input
                    type="text"
                    value={modelName}
                    onChange={(e) => setModelName(e.target.value)}
                    className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1976d2]"
                    placeholder="e.g., Micrometer Calibration Model"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Measurand Formula</label>
                  <textarea
                    value={measurandFormula}
                    onChange={(e) => setMeasurandFormula(e.target.value)}
                    className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md focus:outline-none focus:ring-2 focus:ring-[#1976d2] h-24"
                    placeholder="e.g., y = x₁ + x₂ - x₃"
                  />
                  <p className="text-xs text-[#576065] mt-1">
                    Define the mathematical relationship between input quantities and the measurand
                  </p>
                </div>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  Input Quantities
                </h3>
                <button
                  onClick={addComponent}
                  className="px-4 py-2 bg-[#1976d2] text-white rounded-md hover:bg-[#1565c0] flex items-center gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Add Component
                </button>
              </div>
              
              {components.length === 0 ? (
                <div className="text-center py-8 text-[#576065]">
                  <Info className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>No uncertainty components added yet. Click "Add Component" to begin.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {components.map((component, index) => (
                    <div key={component.id} className="p-4 bg-[#f4f5f3] rounded-md border border-[#c1c7ce]">
                      <div className="flex justify-between items-start mb-3">
                        <input
                          type="text"
                          value={component.name}
                          onChange={(e) => updateComponent(component.id, 'name', e.target.value)}
                          className="font-medium bg-transparent border-none focus:outline-none flex-1"
                          placeholder="Component name"
                        />
                        <button
                          onClick={() => removeComponent(component.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          ×
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium mb-1">Value</label>
                          <input
                            type="number"
                            value={component.value}
                            onChange={(e) => updateComponent(component.id, 'value', parseFloat(e.target.value))}
                            className="w-full px-2 py-1 border border-[#c1c7ce] rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium mb-1">Standard Uncertainty</label>
                          <input
                            type="number"
                            value={component.uncertainty}
                            onChange={(e) => updateComponent(component.id, 'uncertainty', parseFloat(e.target.value))}
                            className="w-full px-2 py-1 border border-[#c1c7ce] rounded text-sm"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
              <h3 className="text-lg font-semibold mb-4">Distribution Selection</h3>
              <div className="space-y-3">
                {components.map((component) => (
                  <div key={component.id} className="p-4 bg-[#f4f5f3] rounded-md border border-[#c1c7ce]">
                    <div className="font-medium mb-2">{component.name}</div>
                    <select
                      value={component.distribution}
                      onChange={(e) => updateComponent(component.id, 'distribution', e.target.value as any)}
                      className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md"
                    >
                      <option value="normal">Normal (Gaussian)</option>
                      <option value="rectangular">Rectangular (Uniform)</option>
                      <option value="triangular">Triangular</option>
                      <option value="u-shaped">U-shaped (Arcsine)</option>
                    </select>
                    <p className="text-xs text-[#576065] mt-2">
                      {component.distribution === 'normal' && 'For repeated measurements with Type A evaluation'}
                      {component.distribution === 'rectangular' && 'For specifications, digital resolution, or uniform tolerances'}
                      {component.distribution === 'triangular' && 'When values are more likely to be near the center'}
                      {component.distribution === 'u-shaped' && 'For phase-related measurements or interpolation errors'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
              <h3 className="text-lg font-semibold mb-4">Uncertainty Values</h3>
              <div className="space-y-3">
                {components.map((component) => (
                  <div key={component.id} className="p-4 bg-[#f4f5f3] rounded-md border border-[#c1c7ce]">
                    <div className="font-medium mb-2">{component.name}</div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium mb-1">Value</label>
                        <input
                          type="number"
                          step="any"
                          value={component.value}
                          onChange={(e) => updateComponent(component.id, 'value', parseFloat(e.target.value))}
                          className="w-full px-2 py-1 border border-[#c1c7ce] rounded text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium mb-1">Standard Uncertainty (u)</label>
                        <input
                          type="number"
                          step="any"
                          value={component.uncertainty}
                          onChange={(e) => updateComponent(component.id, 'uncertainty', parseFloat(e.target.value))}
                          className="w-full px-2 py-1 border border-[#c1c7ce] rounded text-sm"
                        />
                      </div>
                    </div>
                    <div className="mt-2">
                      <label className="block text-xs font-medium mb-1">Degrees of Freedom (ν)</label>
                      <input
                        type="number"
                        value={component.degrees_of_freedom === Infinity ? '' : component.degrees_of_freedom}
                        onChange={(e) => updateComponent(component.id, 'degrees_of_freedom', e.target.value === '' ? Infinity : parseFloat(e.target.value))}
                        className="w-full px-2 py-1 border border-[#c1c7ce] rounded text-sm"
                        placeholder="∞ for Type B"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
              <h3 className="text-lg font-semibold mb-4">Sensitivity Coefficients</h3>
              <p className="text-sm text-[#576065] mb-4">
                Sensitivity coefficients (cᵢ) describe how each input quantity affects the measurand. 
                For simple additive models, cᵢ = 1. For complex relationships, cᵢ = ∂f/∂xᵢ.
              </p>
              <div className="space-y-3">
                {components.map((component) => (
                  <div key={component.id} className="p-4 bg-[#f4f5f3] rounded-md border border-[#c1c7ce]">
                    <div className="font-medium mb-2">{component.name}</div>
                    <div>
                      <label className="block text-xs font-medium mb-1">Sensitivity Coefficient (cᵢ)</label>
                      <input
                        type="number"
                        step="any"
                        value={component.sensitivity_coefficient}
                        onChange={(e) => updateComponent(component.id, 'sensitivity_coefficient', parseFloat(e.target.value))}
                        className="w-full px-2 py-1 border border-[#c1c7ce] rounded text-sm"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );

      case 6:
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
              <h3 className="text-lg font-semibold mb-4">Combined Uncertainty Calculation</h3>
              <button
                onClick={calculateUncertainty}
                disabled={isCalculating || components.length === 0}
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
                    Calculate Combined Uncertainty
                  </>
                )}
              </button>
              
              {calculationResult && (
                <div className="mt-6 p-4 bg-[#e8f5e9] rounded-md border border-[#4caf50]">
                  <div className="flex items-center gap-2 text-[#2e7d32] font-semibold mb-3">
                    <CheckCircle2 className="w-5 h-5" />
                    Calculation Complete
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Combined Standard Uncertainty (u꜀):</span>
                      <span className="font-mono font-semibold">{calculationResult.combined_uncertainty?.toFixed(6)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Effective Degrees of Freedom (ν꜀ff):</span>
                      <span className="font-mono font-semibold">{calculationResult.effective_dof?.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 7:
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
              <h3 className="text-lg font-semibold mb-4">Expanded Uncertainty</h3>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Confidence Level</label>
                  <select
                    value={confidenceLevel}
                    onChange={(e) => setConfidenceLevel(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md"
                  >
                    <option value={0.6827}>68.27% (k ≈ 1)</option>
                    <option value={0.9545}>95.45% (k ≈ 2)</option>
                    <option value={0.99}>99% (k ≈ 2.58)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Coverage Factor (k)</label>
                  <input
                    type="text"
                    value={calculationResult?.coverage_factor?.toFixed(3) || '-'}
                    readOnly
                    className="w-full px-3 py-2 border border-[#c1c7ce] rounded-md bg-[#f4f5f3]"
                  />
                </div>
              </div>
              
              {calculationResult && (
                <div className="p-4 bg-[#e3f2fd] rounded-md border border-[#1976d2]">
                  <div className="text-center">
                    <div className="text-sm text-[#576065] mb-1">Expanded Uncertainty (U)</div>
                    <div className="text-3xl font-mono font-bold text-[#1976d2]">
                      ±{calculationResult.expanded_uncertainty?.toFixed(6)}
                    </div>
                    <div className="text-xs text-[#576065] mt-1">
                      at {Math.round(confidenceLevel * 100)}% confidence level
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 8:
        return (
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-[#c1c7ce]">
              <h3 className="text-lg font-semibold mb-4">Contribution Analysis</h3>
              {calculationResult && components.length > 0 ? (
                <div className="space-y-3">
                  {components
                    .sort((a, b) => (b.contribution || 0) - (a.contribution || 0))
                    .map((component, index) => {
                      const contribution = component.contribution || 0;
                      const percentage = calculationResult.combined_uncertainty > 0 
                        ? (contribution / calculationResult.combined_uncertainty) * 100 
                        : 0;
                      
                      return (
                        <div key={component.id} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="font-medium">{component.name}</span>
                            <span className="text-sm font-mono">{percentage.toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-[#e0e0e0] rounded-full h-2">
                            <div
                              className="bg-[#1976d2] h-2 rounded-full transition-all"
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <div className="text-xs text-[#576065]">
                            Contribution: {contribution.toFixed(6)} | cᵢ·uᵢ = {component.sensitivity_coefficient} × {component.uncertainty}
                          </div>
                        </div>
                      );
                    })}
                </div>
              ) : (
                <div className="text-center py-8 text-[#576065]">
                  <AlertCircle className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Complete the calculation first to see contribution analysis.</p>
                </div>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-[#f4f5f3]">
      {/* Left Sidebar - Workflow Steps */}
      <div className="w-72 bg-white border-r border-[#c1c7ce] overflow-y-auto">
        <div className="p-4 border-b border-[#c1c7ce]">
          <h2 className="font-semibold text-lg">Uncertainty Workflow</h2>
          <p className="text-sm text-[#576065]">Step-by-step GUM analysis</p>
        </div>
        
        <div className="p-4 space-y-2">
          {WORFLOW_STEPS.map((step) => {
            const status = getStepStatus(step.id);
            return (
              <div
                key={step.id}
                className={`p-3 rounded-md cursor-pointer transition-colors ${
                  status === 'active' 
                    ? 'bg-[#e3f2fd] border border-[#1976d2]' 
                    : status === 'completed'
                    ? 'bg-[#e8f5e9] border border-[#4caf50]'
                    : 'bg-[#f4f5f3] border border-[#c1c7ce]'
                }`}
                onClick={() => setCurrentStep(step.id)}
              >
                <div className="flex items-center gap-2">
                  {status === 'completed' ? (
                    <CheckCircle2 className="w-4 h-4 text-[#4caf50]" />
                  ) : status === 'active' ? (
                    <ChevronRight className="w-4 h-4 text-[#1976d2]" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border-2 border-[#c1c7ce]" />
                  )}
                  <span className="font-medium text-sm">{step.title}</span>
                </div>
                <p className="text-xs text-[#576065] mt-1 ml-6">{step.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-4 bg-white border-b border-[#c1c7ce]">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="font-semibold text-lg">
                {WORFLOW_STEPS[currentStep - 1]?.title}
              </h2>
              <p className="text-sm text-[#576065]">
                Step {currentStep} of {WORFLOW_STEPS.length}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={prevStep}
                disabled={currentStep === 1}
                className="px-4 py-2 border border-[#c1c7ce] rounded-md hover:bg-[#f4f5f3] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                Previous
              </button>
              <button
                onClick={nextStep}
                disabled={currentStep === WORFLOW_STEPS.length}
                className="px-4 py-2 bg-[#1976d2] text-white rounded-md hover:bg-[#1565c0] disabled:bg-[#c1c7ce] disabled:cursor-not-allowed flex items-center gap-2"
              >
                {currentStep === WORFLOW_STEPS.length ? 'Complete' : 'Next'}
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Step Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {renderStepContent()}
        </div>
      </div>
    </div>
  );
};